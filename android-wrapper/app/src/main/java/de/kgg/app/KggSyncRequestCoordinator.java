package de.kgg.app;

import org.json.JSONObject;
import org.json.JSONTokener;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Callable;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.BiFunction;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** One active and one waiting immutable request. No Android or provider dependency. */
final class KggSyncRequestCoordinator implements AutoCloseable {
    private final Object admission = new Object();
    private final BiFunction<String,String,Callable<String>> prepare;
    private final Supplier<String> statusSource, peerSource;
    private final Consumer<String> completion;
    private final SerialOwner executor;
    private final boolean ownsExecutor;
    private final Set<String> pendingIds = new HashSet<>();
    private volatile Thread owner;
    private volatile long generation;
    private volatile Snapshot snapshot = new Snapshot(initialStatus(0),initialPeers(0));
    private int admitted;
    private boolean closed;
    private static final class Snapshot {
        final String status,peers;
        Snapshot(String status,String peers){this.status=status;this.peers=peers;}
    }
    KggSyncRequestCoordinator(BiFunction<String,String,Callable<String>> prepare,
            Supplier<String> statusSource,Supplier<String> peerSource,Consumer<String> completion) {
        this(prepare,statusSource,peerSource,completion,newExecutor(),true);
    }
    KggSyncRequestCoordinator(BiFunction<String,String,Callable<String>> prepare,
            Supplier<String> statusSource,Supplier<String> peerSource,Consumer<String> completion,SerialOwner executor){
        this(prepare,statusSource,peerSource,completion,executor,false);
    }
    private KggSyncRequestCoordinator(BiFunction<String,String,Callable<String>> prepare,
            Supplier<String> statusSource,Supplier<String> peerSource,Consumer<String> completion,SerialOwner executor,boolean ownsExecutor){
        this.prepare=prepare;this.statusSource=statusSource;this.peerSource=peerSource;this.completion=completion;
        this.executor=executor;this.ownsExecutor=ownsExecutor;
    }
    static final class SerialOwner extends ThreadPoolExecutor {
        private int reserved;
        private final ReentrantLock execution=new ReentrantLock();
        SerialOwner(){super(1,1,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(1),task->{
            Thread thread=new Thread(task,"kgg-sync-io");thread.setDaemon(true);return thread;
        },new ThreadPoolExecutor.AbortPolicy());}
        synchronized boolean reserve(boolean immediate){
            if(reserved>=(immediate?1:2))return false;
            reserved++;return true;
        }
        synchronized void release(){reserved--;}
        void enter(){execution.lock();}
        void leave(){execution.unlock();release();}
    }
    static SerialOwner newExecutor(){return new SerialOwner();}
    boolean isOwnerThread(){return Thread.currentThread()==owner;}
    long getConfigurationGeneration(){return generation;}
    String getStatusSnapshot(){return snapshot.status;}
    String getPeerSnapshot(){return snapshot.peers;}
    <T> T readConfiguration(Supplier<T> read){synchronized(admission){return read.get();}}
    boolean updateConfiguration(Supplier<Boolean> write){synchronized(admission){return !closed&&write.get();}}
    boolean publishIfCurrent(long expected,Runnable publish){
        synchronized(admission){if(expected!=generation)return false;publish.run();return true;}
    }
    /** Old Boolean configuration calls either complete now or reject BUSY. */
    boolean runBooleanWhenIdle(Supplier<Boolean> action){
        synchronized(admission){if(closed||!executor.reserve(true))return false;}
        executor.enter();Thread previous=owner;owner=Thread.currentThread();
        try{return action.get();}finally{owner=previous;executor.leave();}
    }
    boolean requestSyncJson(String header,String payload) {
        if(header==null||header.length()>2048||payload==null||payload.length()>8_000_000)return false;
        try {
            JSONObject request=new JSONObject(header);
            String token=request.getString("documentToken"),id=request.getString("requestId"),op=request.getString("operation");
            Object supplied=request.get("configurationGeneration");
            if(!(supplied instanceof Number)||((Number)supplied).doubleValue()!=((Number)supplied).longValue()
                    ||!token.matches("[A-Za-z0-9._:-]{1,160}")||!id.matches("[A-Za-z0-9._:-]{1,96}")
                    ||!op.matches("read|write|configureOwnDriveFile|selectDrivePeerFiles|disconnectDrive")||request.has("payload"))return false;
            long expected=((Number)supplied).longValue();String key=token+"/"+id;
            synchronized(admission){
                if(closed||admitted>=2||expected!=generation||pendingIds.contains(key))return false;
                // Only the small header is parsed here. Payload and generation
                // are immutable; all bindings are mutated on this same owner.
                if(!executor.reserve(false))return false;
                final Callable<String> action;
                try{action=prepare.apply(header,payload);}catch(Exception invalid){executor.release();return false;}
                admitted++;pendingIds.add(key);markPending();
                try{executor.execute(()->runRequest(request,key,expected,op,action));return true;}
                catch(RejectedExecutionException full){admitted--;pendingIds.remove(key);executor.release();return false;}
            }
        }catch(Exception invalid){return false;}
    }
    private void runRequest(JSONObject request,String key,long expected,String op,Callable<String> action){
        executor.enter();try{
        owner=Thread.currentThread();
        Object result=null;String error="";
        try{
            if(expected!=generation)throw new IllegalStateException("stale_generation");
            String value=action.call();JSONTokener parser=new JSONTokener(value);result=parser.nextValue();
            if(parser.nextClean()!=0)throw new IllegalStateException("invalid_result");
        }catch(Exception failure){error=boundedError(failure);}
        boolean configOperation=op.equals("disconnectDrive")||op.equals("configureOwnDriveFile")||op.equals("selectDrivePeerFiles");
        if(expected!=generation&&!configOperation)error="stale_generation";
        synchronized(admission){admitted--;pendingIds.remove(key);}
        if(expected==generation||configOperation)refreshSnapshots();
        try{
            JSONObject reply=new JSONObject().put("kind","kgg_sync_async_result").put("version",1)
                    .put("documentToken",request.getString("documentToken")).put("requestId",request.getString("requestId"))
                    .put("operation",op).put("configurationGeneration",expected)
                    .put("currentConfigurationGeneration",generation).put("ok",error.isEmpty());
            if(error.isEmpty())reply.put("result",result==null?JSONObject.NULL:result);else reply.put("error",error);
            completion.accept(reply.toString());
        }catch(Exception ignored){/* Native persistence is independent of a detached JS listener. */}
        }finally{executor.leave();}
    }
    /** Picker/configuration callbacks share the same bounded owner as accepted I/O. */
    boolean enqueueControl(Runnable action){
        return enqueueControl(action,null);
    }
    boolean enqueueControl(Runnable action,Runnable after){
        synchronized(admission){
            if(closed||admitted>=2||!executor.reserve(false))return false;
            admitted++;markPending();
            try{executor.execute(()->{executor.enter();try{owner=Thread.currentThread();try{action.run();}catch(Exception failure){reportError(boundedError(failure));}
                finally{synchronized(admission){admitted--;}refreshSnapshots();if(after!=null)after.run();}}finally{executor.leave();}});return true;}
            catch(RejectedExecutionException full){admitted--;executor.release();return false;}
        }
    }
    long invalidateConfiguration(){
        synchronized(admission){generation++;snapshot=new Snapshot(initialStatus(generation),initialPeers(generation));return generation;}
    }
    void reportError(String code){
        synchronized(admission){try{JSONObject status=new JSONObject(snapshot.status).put("pending",true)
                .put("providerAccepted",false).put("lastError",code);snapshot=new Snapshot(status.toString(),snapshot.peers);}catch(Exception ignored){}}
    }
    private void markPending(){
        try{JSONObject status=new JSONObject(snapshot.status).put("pending",true).put("providerAccepted",false);
            snapshot=new Snapshot(status.toString(),snapshot.peers);}catch(Exception ignored){}
    }
    private void refreshSnapshots(){
        long current=generation;
        try{
            // Suppliers may access files; they run only on the serial worker,
            // never under admission and never inside either snapshot getter.
            JSONObject status=new JSONObject(statusSource.get()),peers=new JSONObject(peerSource.get());
            String now=Instant.now().toString();
            synchronized(admission){
                if(current!=generation)return;
                boolean pending=status.optBoolean("pending")||admitted>0;
                status.put("initialized",true).put("configurationGeneration",current).put("updatedAt",now)
                        .put("pending",pending).put("providerAccepted",status.optBoolean("providerAccepted")&&!pending);
                // Peer freshness belongs to the last real read, independently
                // of status refreshes or a newly completed write.
                peers.put("configurationGeneration",current);
                if(!peers.has("stale"))peers.put("stale",true);
                if(!peers.has("updatedAt"))peers.put("updatedAt","");
                snapshot=new Snapshot(status.toString(),peers.toString());
            }
        }catch(Exception failure){reportError("snapshot_failed");}
    }
    private static String boundedError(Exception failure){
        String code=failure.getMessage();return code!=null&&code.matches("[a-z_]{1,64}")?code:"operation_failed";
    }
    private static String initialStatus(long generation){
        return "{\"available\":true,\"platform\":\"android\",\"transport\":\"initializing\",\"initialized\":false,\"driveConfigured\":true,\"pending\":true,\"providerAccepted\":false,\"stale\":true,\"configurationGeneration\":"+generation+",\"updatedAt\":\"\"}";
    }
    private static String initialPeers(long generation){
        return "{\"kind\":\"kgg_cross_data_safe_sync_mesh\",\"version\":1,\"roomId\":\"\",\"peers\":[],\"stale\":true,\"configurationGeneration\":"+generation+",\"updatedAt\":\"\"}";
    }
    @Override public void close(){
        // Accepted writes are not cancelled by a page reload or UI teardown.
        // The bounded queue drains; provider/outbox outcomes remain authoritative.
        synchronized(admission){closed=true;}if(ownsExecutor)executor.shutdown();
    }
}
