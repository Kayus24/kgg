package de.kgg.app;

import org.json.JSONObject;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;
import java.util.function.BiFunction;
import java.util.function.Supplier;

/** Android-free behavioral contract; no provider, emulator, Gradle or new library. */
public final class KggSyncRequestCoordinatorTest {
    private static final AtomicInteger checks = new AtomicInteger();
    private static Class<?> coordinatorClass;
    private static void check(boolean value, String message) {
        checks.incrementAndGet();
        if (!value) throw new AssertionError(message);
    }
    private static Object call(Object owner, String method, Class<?>[] parameters, Object... values) throws Exception {
        Method target = coordinatorClass.getDeclaredMethod(method, parameters);
        target.setAccessible(true);
        try { return target.invoke(owner, values); }
        catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof Exception) throw (Exception) failure.getCause();
            throw failure;
        }
    }
    private static final class Fixture implements AutoCloseable {
        final AtomicReference<String> target = new AtomicReference<>("content://synthetic/old-own");
        final AtomicReference<String> peerMetadata = new AtomicReference<>("{\"peers\":[],\"stale\":true,\"updatedAt\":\"\"}");
        final ConcurrentLinkedQueue<JSONObject> replies = new ConcurrentLinkedQueue<>();
        final ConcurrentLinkedQueue<String> writes = new ConcurrentLinkedQueue<>();
        final ConcurrentLinkedQueue<String> durable = new ConcurrentLinkedQueue<>();
        final ConcurrentLinkedQueue<String> prepared = new ConcurrentLinkedQueue<>();
        final AtomicInteger active = new AtomicInteger(), maxActive = new AtomicInteger(), statusReads = new AtomicInteger(), peerReads = new AtomicInteger();
        final Object signal = new Object();
        final Thread testThread = Thread.currentThread();
        volatile CountDownLatch writeEntered = new CountDownLatch(1), writeRelease = new CountDownLatch(0);
        volatile CountDownLatch readEntered = new CountDownLatch(1), readRelease = new CountDownLatch(0);
        volatile boolean failWrite;
        volatile boolean accepted = true;
        final Object coordinator;
        Fixture() throws Exception {
            // Capture the binding and immutable payload on admission, not when a
            // delayed queued action finally starts. The real bridge supplies this
            // boundary; the coordinator must not defer or repeat preparation.
            BiFunction<String, String, Callable<String>> prepare = (requestJson, separatePayload) -> {
                JSONObject request = new JSONObject(requestJson);
                check(!request.has("payload")&&requestJson.length()<=2048,"large payload was parsed as part of the admission header");
                String id = request.getString("requestId"), operation = request.getString("operation");
                String payload = separatePayload, bound = target.get();
                prepared.add(id + ":" + bound);
                return () -> {
                    int count = active.incrementAndGet();maxActive.accumulateAndGet(count, Math::max);
                    try {
                        if ("write".equals(operation)) {
                            durable.add(payload);writeEntered.countDown();
                            if (!writeRelease.await(5,TimeUnit.SECONDS)) throw new IllegalStateException("test_write_gate_timeout");
                            if (failWrite) throw new IllegalStateException("write_failed");
                            writes.add(bound + ":" + payload);accepted = true;
                            return "true";
                        }
                        readEntered.countDown();
                        if (!readRelease.await(5,TimeUnit.SECONDS)) throw new IllegalStateException("test_read_gate_timeout");
                        peerMetadata.set("{\"kind\":\"kgg_cross_data_safe_sync_mesh\",\"version\":1,\"roomId\":\"synthetic-room\",\"stale\":false,\"updatedAt\":\"2026-10-23T12:00:00Z\",\"peers\":[{\"origin\":{\"deviceId\":\"synthetic-peer\",\"roomId\":\"synthetic-room\"},\"exportedAt\":\"2026-10-23T12:00:00Z\"}]}");
                        return "{\"kind\":\"kgg_cross_data_safe_sync_mesh\",\"version\":1,\"roomId\":\"synthetic-room\",\"peers\":[]}";
                    } finally { active.decrementAndGet(); }
                };
            };
            Supplier<String> status = () -> {
                check(Thread.currentThread()!=testThread,"status supplier performed I/O on the bridge caller");
                statusReads.incrementAndGet();
                return "{\"transport\":\"saf-document\",\"driveConfigured\":true,\"pending\":false,\"providerAccepted\":"+accepted+"}";
            };
            Supplier<String> peers = () -> {
                check(Thread.currentThread()!=testThread,"peer supplier performed I/O on the bridge caller");
                peerReads.incrementAndGet();
                return peerMetadata.get();
            };
            Consumer<String> completion = value -> { replies.add(new JSONObject(value));synchronized(signal){signal.notifyAll();} };
            Constructor<?> constructor = coordinatorClass.getDeclaredConstructor(BiFunction.class,Supplier.class,Supplier.class,Consumer.class);
            constructor.setAccessible(true);coordinator=constructor.newInstance(prepare,status,peers,completion);
        }
        long generation() throws Exception { return ((Number)call(coordinator,"getConfigurationGeneration",new Class<?>[0])).longValue(); }
        boolean submit(String id,String operation,String payload) throws Exception { return submit(id,operation,payload,generation()); }
        boolean submit(String id,String operation,String payload,long generation) throws Exception {
            String request = new JSONObject().put("documentToken","synthetic-document-a").put("requestId",id)
                    .put("operation",operation).put("configurationGeneration",generation).toString();
            return (Boolean)call(coordinator,"requestSyncJson",new Class<?>[]{String.class,String.class},request,payload);
        }
        JSONObject status() throws Exception { return new JSONObject((String)call(coordinator,"getStatusSnapshot",new Class<?>[0])); }
        JSONObject peers() throws Exception { return new JSONObject((String)call(coordinator,"getPeerSnapshot",new Class<?>[0])); }
        JSONObject await(String id) throws Exception {
            long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);
            synchronized(signal){
                for(;;){
                    for(JSONObject result:replies)if(id.equals(result.optString("requestId")))return result;
                    long remaining=end-System.nanoTime();if(remaining<=0)throw new AssertionError("missing completion: "+id);
                    TimeUnit.NANOSECONDS.timedWait(signal,remaining);
                }
            }
        }
        void warm() throws Exception { check(submit("warm","read",""),"warm read rejected");check(await("warm").getBoolean("ok"),"warm read failed"); }
        @Override public void close() throws Exception {
            writeRelease.countDown();readRelease.countDown();call(coordinator,"close",new Class<?>[0]);
        }
    }
    private static void boundedGetterWhileProviderBlocked(Fixture f) throws Exception {
        int beforeStatus=f.statusReads.get(),beforePeers=f.peerReads.get();
        ExecutorService reader=Executors.newSingleThreadExecutor();
        try {
            Future<List<JSONObject>> result=reader.submit(()->List.of(f.status(),f.peers()));
            List<JSONObject> snapshots=result.get(750,TimeUnit.MILLISECONDS);
            check(snapshots.get(0).optBoolean("pending"),"accepted pending job was hidden by a previous ACK");
            check(!snapshots.get(0).optBoolean("providerAccepted"),"old provider ACK was presented while another write is pending");
            check(snapshots.get(0).has("configurationGeneration"),"status has no configuration identity");
            check(snapshots.get(0).has("updatedAt"),"status has no snapshot freshness");
            check(snapshots.get(1).getJSONArray("peers").length()==1,"cached peer metadata missing");
            check(!snapshots.get(1).toString().contains("mediaBlobs"),"display snapshot carried full media payload");
            check(beforeStatus==f.statusReads.get()&&beforePeers==f.peerReads.get(),"snapshot getter recomputed blocking backend state");
        } finally { reader.shutdownNow(); }
    }
    private static void queueAndFinalAck() throws Exception {
        try(Fixture f=new Fixture()){
            f.warm();f.writeRelease=new CountDownLatch(1);
            check(f.submit("write-a","write","immutable-revision-one"),"first write not admitted");
            check(f.writeEntered.await(2,TimeUnit.SECONDS),"worker did not reach provider write");
            check(f.durable.contains("immutable-revision-one"),"private outbox boundary was not reached before provider ACK");
            check(f.replies.stream().noneMatch(value->"write-a".equals(value.optString("requestId"))),"enqueue resolved as final provider ACK");
            boundedGetterWhileProviderBlocked(f);
            check(f.submit("read-b","read",""),"one waiting job should be admitted");
            check(!f.submit("write-c","write","revision-three"),"third job exceeded one-active/one-waiting budget");
            check(!f.submit("write-a","write","duplicate"),"duplicate active request ID was admitted");
            check(f.prepared.stream().noneMatch(value->value.startsWith("write-c:")),"queue rejection prepared or mutated a job");
            f.writeRelease.countDown();JSONObject ack=f.await("write-a");f.await("read-b");
            check(ack.getBoolean("ok")&&Boolean.TRUE.equals(ack.get("result")),"final provider result was not delivered");
            check(ack.getString("documentToken").equals("synthetic-document-a")&&ack.getString("operation").equals("write"),"completion identity changed");
            check(ack.getLong("configurationGeneration")==0,"completion generation changed");
            check(f.maxActive.get()==1,"native actions overlapped");
            check(f.writes.contains("content://synthetic/old-own:immutable-revision-one"),"accepted payload or target changed");
        }
    }
    private static void immutableQueuedBindingAndGeneration() throws Exception {
        try(Fixture f=new Fixture()){
            f.warm();f.readEntered=new CountDownLatch(1);f.readRelease=new CountDownLatch(1);
            check(f.submit("read-held","read",""),"held read not admitted");check(f.readEntered.await(2,TimeUnit.SECONDS),"read gate missing");
            check(f.submit("write-old","write","original-payload"),"queued old binding not admitted");
            check(f.prepared.contains("write-old:content://synthetic/old-own"),"binding was not captured on admission");
            check(!f.submit("disconnect-full","disconnectDrive",""),"full queue accepted disconnect and lost its completion");
            check(f.generation()==0,"rejected operation changed configuration");
            f.target.set("content://synthetic/new-own");f.accepted=false;
            long next=((Number)call(f.coordinator,"invalidateConfiguration",new Class<?>[0])).longValue();check(next==1,"configuration generation did not advance");
            check(!f.submit("stale-request","write","stale",0),"native admission trusted stale JS generation");
            f.readRelease.countDown();f.await("read-held");f.await("write-old");
            check(f.writes.stream().noneMatch(value->value.startsWith("content://synthetic/new-own:")),"accepted old write was redirected into a new binding");
            check(f.status().getLong("configurationGeneration")==1&&!f.status().optBoolean("providerAccepted"),"old completion republished provider ACK for new configuration");
        }
    }
    private static void detachedUiDoesNotCancelDurableWrite() throws Exception {
        try(Fixture f=new Fixture()){
            f.warm();f.writeRelease=new CountDownLatch(1);
            check(f.submit("orphaned-ui","write","durable-before-reload"),"write not admitted");check(f.writeEntered.await(2,TimeUnit.SECONDS),"provider gate missing");
            // The JS timeout/reload discards only its waiter. Native has accepted
            // immutable work and must still finish its own persistence/ACK path.
            check(f.durable.contains("durable-before-reload"),"accepted native write was not retained");
            f.writeRelease.countDown();JSONObject result=f.await("orphaned-ui");
            check(result.getBoolean("ok"),"detached UI prevented accepted provider completion");
            check(f.writes.contains("content://synthetic/old-own:durable-before-reload"),"accepted write vanished after UI detachment");
        }
        try(Fixture f=new Fixture()){
            f.warm();f.failWrite=true;check(f.submit("failure","write","pending-after-error"),"failure job not admitted");
            JSONObject result=f.await("failure");check(!result.getBoolean("ok"),"provider failure reported success");
            check(result.optString("error").contains("write_failed"),"bounded provider error missing");
            check(f.durable.contains("pending-after-error")&&f.writes.isEmpty(),"failed provider job lost pending data or claimed publication");
        }
    }
    private static void peerFreshnessRequiresActualRead() throws Exception {
        try(Fixture f=new Fixture()){
            CountDownLatch initialized=new CountDownLatch(1);
            check((Boolean)call(f.coordinator,"enqueueControl",new Class<?>[]{Runnable.class,Runnable.class},(Runnable)()->{},(Runnable)initialized::countDown),"initial status refresh rejected");
            check(initialized.await(2,TimeUnit.SECONDS),"initial status refresh missing");
            check(f.status().optBoolean("initialized"),"status initialization did not complete");
            check(f.peers().optBoolean("stale")&&f.peers().optString("updatedAt").isEmpty(),"status-only initialization declared unseen empty peers current");
            f.warm();
            check(!f.peers().optBoolean("stale")&&f.peers().getString("updatedAt").equals("2026-10-23T12:00:00Z"),"actual read freshness was replaced with status refresh time");
            check(f.submit("write-no-peer-read","write","revision"),"write after read rejected");f.await("write-no-peer-read");
            check(f.peers().getString("updatedAt").equals("2026-10-23T12:00:00Z"),"write/status refresh falsely renewed peer read freshness");
            call(f.coordinator,"invalidateConfiguration",new Class<?>[0]);
            check(f.peers().optBoolean("stale")&&f.peers().optString("updatedAt").isEmpty(),"reconfiguration retained a fresh claim about old peers");
        }
    }
    private static void oldBooleanCallsRejectBusyAndCompleteWhenIdle() throws Exception {
        try(Fixture f=new Fixture()){
            CountDownLatch legacyEntered=new CountDownLatch(1),legacyRelease=new CountDownLatch(1);
            AtomicInteger calls=new AtomicInteger();ExecutorService caller=Executors.newSingleThreadExecutor();
            try{
                Future<Boolean> legacy=caller.submit(()->(Boolean)call(f.coordinator,"runBooleanWhenIdle",new Class<?>[]{Supplier.class},(Supplier<Boolean>)()->{
                    calls.incrementAndGet();legacyEntered.countDown();try{legacyRelease.await(5,TimeUnit.SECONDS);}catch(InterruptedException e){throw new IllegalStateException(e);}return false;
                }));
                check(legacyEntered.await(2,TimeUnit.SECONDS),"idle old Boolean operation was not executed");
                check(f.submit("waiting-after-legacy","read",""),"one async job could not wait behind old synchronous completion");
                check(!f.submit("third-after-legacy","write","must-not-enqueue"),"legacy active plus two async jobs exceeded shared capacity");
                check(f.prepared.stream().noneMatch(value->value.startsWith("third-after-legacy:")),"global queue rejection still prepared a job");
                check(f.readEntered.getCount()==1,"provider job overlapped the direct old Boolean operation");
                long start=System.nanoTime();
                check(!(Boolean)call(f.coordinator,"runBooleanWhenIdle",new Class<?>[]{Supplier.class},(Supplier<Boolean>)()->{calls.incrementAndGet();return true;}),"busy Boolean call returned acceptance for queued work");
                check(TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-start)<750&&calls.get()==1,"BUSY rejection waited on provider or executed the rejected action");
                check(f.status().has("configurationGeneration"),"snapshot getter blocked behind old synchronous execution");
                legacyRelease.countDown();check(!legacy.get(2,TimeUnit.SECONDS),"old Boolean false completion became queue-accept true");
                check(f.await("waiting-after-legacy").getBoolean("ok"),"async job failed after old Boolean completion");
            }finally{legacyRelease.countDown();caller.shutdownNow();}
        }
    }
    private static void lateStatusRefreshCannotRepublishOldConfiguration()throws Exception{
        CountDownLatch captured=new CountDownLatch(1),release=new CountDownLatch(1),finished=new CountDownLatch(1);
        AtomicReference<String> follow=new AtomicReference<>("old-room");
        try(KggSyncRequestCoordinator owner=new KggSyncRequestCoordinator((header,payload)->()->"true",()->{
            String before=follow.get();captured.countDown();try{release.await(5,TimeUnit.SECONDS);}catch(InterruptedException e){throw new IllegalStateException(e);}
            return "{\"syncRoomId\":\""+before+"\",\"providerAccepted\":true}";
        },()->"{\"peers\":[{\"origin\":{\"deviceId\":\"old-peer\"}}],\"stale\":false}",value->{})){
            check(owner.enqueueControl(()->{},finished::countDown),"controlled status refresh rejected");
            check(captured.await(2,TimeUnit.SECONDS),"old status did not reach controlled capture");
            check(owner.updateConfiguration(()->{follow.set("new-room");owner.invalidateConfiguration();return true;}),"small synchronous config update rejected during status IO");
            release.countDown();check(finished.await(2,TimeUnit.SECONDS),"late status refresh did not finish");
            check(follow.get().equals("new-room"),"late status work restored an old Followconfig cache");
            JSONObject status=new JSONObject(owner.getStatusSnapshot()),peers=new JSONObject(owner.getPeerSnapshot());
            check(status.getLong("configurationGeneration")==1&&!status.optBoolean("providerAccepted"),"late old status overwrote new configuration or ACK");
            check(peers.optBoolean("stale")&&!peers.toString().contains("old-peer"),"late old peer supplier was published with the new generation");
        }finally{release.countDown();}
    }
    public static void main(String[] args) throws Exception {
        try { coordinatorClass=Class.forName("de.kgg.app.KggSyncRequestCoordinator"); }
        catch(ClassNotFoundException missing){throw new AssertionError("Correlated bounded native Sync execution is absent; legacy transport cannot expose non-blocking snapshots or final async ACK",missing);}
        queueAndFinalAck();immutableQueuedBindingAndGeneration();detachedUiDoesNotCancelDurableWrite();peerFreshnessRequiresActualRead();oldBooleanCallsRejectBusyAndCompleteWhenIdle();lateStatusRefreshCannotRepublishOldConfiguration();
        System.out.println("Native correlated async Sync PASS: "+checks+" checks; no Android provider/device claim");
    }
}
