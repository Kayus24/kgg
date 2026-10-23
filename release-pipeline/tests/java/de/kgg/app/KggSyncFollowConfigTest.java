package de.kgg.app;

import android.content.Context;
import org.json.JSONObject;
import java.io.File;
import java.nio.file.Files;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.function.BiFunction;
import java.util.concurrent.Callable;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** Real local bridge, temporary filesystem and in-memory Android preference boundary. */
public final class KggSyncFollowConfigTest {
    private static int checks;
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    private static final class ScanContext extends Context {
        final CountDownLatch scanEntered=new CountDownLatch(1),scanRelease=new CountDownLatch(1);
        volatile Thread scanThread;
        ScanContext(File root){super(root);}
        @Override public File getFilesDir(){
            if(Thread.currentThread()==scanThread){
                scanThread=null;scanEntered.countDown();
                try{if(!scanRelease.await(5,TimeUnit.SECONDS))throw new IllegalStateException("controlled_scan_timeout");}
                catch(InterruptedException failure){throw new IllegalStateException(failure);}
            }
            return super.getFilesDir();
        }
    }
    private static void statusInitializationPreservesConcurrentPairing()throws Exception{
        for(boolean pairedRoom:new boolean[]{true,false}){
            File root=Files.createTempDirectory("kgg-status-room-contract-").toFile();
            System.setProperty("kgg.test.storage",root.getAbsolutePath());
            ScanContext context=new ScanContext(root);KggSyncBridge local=new KggSyncBridge(context);
            ExecutorService scan=Executors.newSingleThreadExecutor();
            try(KggSyncRequestCoordinator owner=new KggSyncRequestCoordinator((header,payload)->()->"true",()->"{}",()->"{\"peers\":[]}",value->{})){
                local.attachSyncOwner(owner,owner::invalidateConfiguration);
                Future<String> status=scan.submit(()->{context.scanThread=Thread.currentThread();return local.getStatus();});
                check(context.scanEntered.await(2,TimeUnit.SECONDS),"real status did not reach filesystem scan after reading its roomless configuration");
                String room=pairedRoom?"paired-room":"";
                check(local.writeFollowConfig(new JSONObject().put("therapistId","paired-self").put("syncRoomId",room).put("followedTherapists",new org.json.JSONArray()).toString()),"concurrent room write failed");
                JSONObject paired=new JSONObject(local.readFollowConfig());
                paired.getJSONArray("followedTherapists").put(new JSONObject().put("deviceId","paired-peer").put("roomId","paired-room"));
                check(local.writeFollowConfig(paired.toString()),"concurrent peer upsert failed");
                check(new JSONObject(local.readFollowConfig()).getJSONArray("followedTherapists").length()==1,"pairing did not finish before old status scan resumed");
                context.scanRelease.countDown();JSONObject oldStatus=new JSONObject(status.get(3,TimeUnit.SECONDS));
                check(oldStatus.getString("syncRoomId").equals("default"),"control did not retain the genuine old roomless getStatus snapshot");
                JSONObject current=new JSONObject(local.readFollowConfig());
                check(current.getString("syncRoomId").equals(pairedRoom?"paired-room":"default")
                        &&current.getJSONArray("followedTherapists").length()==1
                        &&current.getJSONArray("followedTherapists").getJSONObject(0).getString("deviceId").equals("paired-peer")
                        &&current.getString("therapistId").equals("paired-self"),
                        "old getStatus room initialization overwrote the successfully paired room/peer/current identity");
                check(owner.getConfigurationGeneration()==(pairedRoom?2:3),"status initialization unnecessarily changed an existing room or failed to initialize a still-empty one");
            }finally{context.scanRelease.countDown();scan.shutdownNow();try(var paths=Files.walk(root.toPath())){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(Exception ignored){}});}}
        }
    }
    public static void main(String[] args)throws Exception{
        File root=Files.createTempDirectory("kgg-follow-contract-").toFile();
        System.setProperty("kgg.test.storage",root.getAbsolutePath());
        Context context=(Context)Context.class.getConstructor(File.class).newInstance(root);
        KggSyncBridge local=new KggSyncBridge(context);
        CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1),done=new CountDownLatch(1);
        AtomicReference<String> boundResult=new AtomicReference<>();
        AtomicReference<KggSyncRequestCoordinator> currentOwner=new AtomicReference<>();
        AtomicReference<String> peerCache=new AtomicReference<>("{\"peers\":[],\"stale\":true,\"updatedAt\":\"\"}");
        BiFunction<String,String,Callable<String>> prepare=(header,payload)->{
            String boundFollowConfiguration=local.readFollowConfig();
            long expected=new JSONObject(header).getLong("configurationGeneration");
            return ()->{entered.countDown();release.await(5,TimeUnit.SECONDS);String raw=local.readSyncJson(boundFollowConfiguration);boundResult.set(raw);
                currentOwner.get().publishIfCurrent(expected,()->peerCache.set("{\"peers\":[{\"origin\":{\"deviceId\":\"late-old-room-peer\"}}],\"stale\":false}"));return raw;};
        };
        try(KggSyncRequestCoordinator owner=new KggSyncRequestCoordinator(prepare,()->"{}",peerCache::get,value->done.countDown())){
            currentOwner.set(owner);
            local.attachSyncOwner(owner,owner::invalidateConfiguration);
            String header="{\"documentToken\":\"pairing-test\",\"requestId\":\"blocked-read\",\"operation\":\"read\",\"configurationGeneration\":0}";
            check(owner.requestSyncJson(header,""),"blocking native job rejected");check(entered.await(2,TimeUnit.SECONDS),"native I/O did not block");
            long start=System.nanoTime();
            check(local.writeFollowConfig("{\"therapistId\":\"self\",\"syncRoomId\":\"paired-room\",\"followedTherapists\":[]}"),"first synchronous room write rejected");
            JSONObject second=new JSONObject(local.readFollowConfig());
            check(second.optString("syncRoomId").equals("paired-room"),"accepted Followconfig write was invisible to the immediately following real pairing read");
            second.getJSONArray("followedTherapists").put(new JSONObject().put("deviceId","paired-peer").put("roomId","paired-room"));
            check(local.writeFollowConfig(second.toString()),"second pairing write was silently rejected behind provider I/O");
            JSONObject result=new JSONObject(local.readFollowConfig());
            check(result.getJSONArray("followedTherapists").length()==1&&result.getString("syncRoomId").equals("paired-room"),"real consecutive pairing writes lost room or peer");
            check(owner.getConfigurationGeneration()==2,"accepted synchronous writes were not atomically invalidated");
            check(!owner.publishIfCurrent(0,()->{throw new AssertionError("old peer results published after synchronous config invalidation");}),"old generation peer publication was accepted");
            check(new JSONObject(owner.getPeerSnapshot()).optBoolean("stale"),"reconfigured peer list claimed fresh old results");
            check(TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-start)<750,"cheap Followconfig writes waited on blocked I/O");
            release.countDown();check(done.await(3,TimeUnit.SECONDS),"accepted native job failed to drain");
            check(!new JSONObject(boundResult.get()).getString("roomId").equals("paired-room"),"accepted old local read was redirected to the newly paired room");
            check(!peerCache.get().contains("late-old-room-peer"),"read finishing after synchronous pairing published an old peer cache");
            check(new JSONObject(local.readFollowConfig()).getJSONArray("followedTherapists").length()==1,"old native completion overwrote paired state");
        }finally{release.countDown();try(var paths=Files.walk(root.toPath())){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(Exception ignored){}});}}
        statusInitializationPreservesConcurrentPairing();
        System.out.println("Real local Followconfig PASS: "+checks+" checks; synthetic preferences/files, no Android device claim");
    }
}
