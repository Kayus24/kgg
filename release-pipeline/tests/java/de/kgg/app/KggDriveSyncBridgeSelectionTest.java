package de.kgg.app;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.content.UriPermission;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicInteger;

/** Real picker-result bridge, serial owner and transport; only Android/provider boundaries are doubles. */
public final class KggDriveSyncBridgeSelectionTest {
    private static final int READ=1, WRITE=2, PERSISTABLE=64;
    private static final Uri OWN=Uri.parse("content://synthetic/own"), PEER=Uri.parse("content://synthetic/peer");
    private static int checks;
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}

    private static final class Provider extends ContentResolver {
        final Map<Uri,Integer> grants=new LinkedHashMap<>();
        final Map<Uri,String> documents=new LinkedHashMap<>();
        int takes,releases,writes,lastTakenFlags;
        boolean failTake,supportsWrite=true;
        int grantOnTake=READ|WRITE;
        public List<UriPermission> getPersistedUriPermissions(){
            List<UriPermission> result=new ArrayList<>();
            grants.forEach((uri,flags)->result.add(new UriPermission(uri,flags)));return result;
        }
        public void takePersistableUriPermission(Uri uri,int flags){
            takes++;lastTakenFlags=flags;
            if(failTake)throw new SecurityException("synthetic provider denied persistence");
            grants.put(uri,grants.getOrDefault(uri,0)|(flags&grantOnTake));
        }
        public void releasePersistableUriPermission(Uri uri,int flags){
            releases++;int remaining=grants.getOrDefault(uri,0)&~flags;
            if(remaining==0)grants.remove(uri);else grants.put(uri,remaining);
        }
        public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){
            return new Cursor(){
                public boolean moveToFirst(){return true;}
                public int getColumnIndex(String name){for(int i=0;i<projection.length;i++)if(projection[i].equals(name))return i;return -1;}
                public int getInt(int column){return supportsWrite?DocumentsContract.Document.FLAG_SUPPORTS_WRITE:0;}
                public String getString(int column){return "application/json";}
                public long getLong(int column){return documents.getOrDefault(uri,"").getBytes(StandardCharsets.UTF_8).length;}
                public boolean isNull(int column){return !OpenableColumns.SIZE.equals(projection[column]);}
                public void close(){}
            };
        }
        public InputStream openInputStream(Uri uri){return new ByteArrayInputStream(documents.getOrDefault(uri,"").getBytes(StandardCharsets.UTF_8));}
        public OutputStream openOutputStream(Uri uri,String mode){
            return new ByteArrayOutputStream(){@Override public void close(){writes++;documents.put(uri,new String(toByteArray(),StandardCharsets.UTF_8));}};
        }
    }
    private static final class PickerActivity extends Activity {
        final Provider provider;
        int request;
        Intent requestedIntent;
        PickerActivity(File root,Provider provider){super(root);this.provider=provider;}
        public ContentResolver getContentResolver(){return provider;}
        public void startActivityForResult(Intent intent,int request){this.request=request;requestedIntent=intent;}
    }
    private static final class Selection implements AutoCloseable {
        final File root=Files.createTempDirectory("kgg-saf-selection-").toFile();
        final Provider provider=new Provider();
        final PickerActivity activity=new PickerActivity(root,provider);
        final AtomicReference<CountDownLatch> ready=new AtomicReference<>();
        final AtomicInteger configurationPublications=new AtomicInteger();
        final KggDriveSyncBridge bridge=new KggDriveSyncBridge(activity,()->{CountDownLatch latch=ready.get();if(latch!=null)latch.countDown();});
        final KggSyncRequestCoordinator owner=new KggSyncRequestCoordinator((header,payload)->()->"true",bridge::getStatus,()->"{\"peers\":[]}",value->{});
        Selection()throws Exception{bridge.attachSyncOwner(owner,()->{configurationPublications.incrementAndGet();owner.invalidateConfiguration();});}
        void select(boolean own,int flags)throws Exception{
            select(own,flags,own?OWN:PEER);
        }
        void select(boolean own,int flags,Uri selected)throws Exception{
            CountDownLatch completed=new CountDownLatch(1);ready.set(completed);
            String options=new JSONObject().put("deviceId","device-own").put("roomId","synthetic-room").toString();
            check(own?bridge.configureOwnDriveFile(options):bridge.selectDrivePeerFiles(options),"real picker configuration must start");
            check(activity.request==(own?4302:4303),"bridge selected the wrong picker request");
            check((activity.requestedIntent.getFlags()&PERSISTABLE)!=0,"request must still ask the provider for persistable access");
            Intent result=new Intent().setData(selected).addFlags(flags);
            check(bridge.onActivityResult(activity.request,Activity.RESULT_OK,result),"real result callback was not consumed");
            check(completed.await(3,TimeUnit.SECONDS),"real serial-owner picker completion did not arrive");
            long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
            while(!owner.runBooleanWhenIdle(()->true)){
                if(System.nanoTime()>=deadline)throw new AssertionError("real picker owner did not become idle");
                Thread.sleep(1);
            }
        }
        JSONObject status(){return new JSONObject(bridge.getStatus());}
        public void close()throws Exception{
            owner.close();
            try(var files=Files.walk(root.toPath())){files.sorted(java.util.Comparator.reverseOrder()).forEach(path->{try{Files.delete(path);}catch(Exception error){throw new RuntimeException(error);}});}
        }
    }
    private static JSONObject document(String device)throws Exception{
        return new JSONObject("{\"kind\":\"kgg_cross_data_safe_sync\",\"version\":2,\"schema\":\"exercise-bank-packages-v2\","
                +"\"scopes\":[\"exerciseBank\"],\"exportedAt\":\"2026-10-23T12:00:00Z\","
                +"\"privacy\":{\"patients\":false,\"secrets\":false,\"debugPayloads\":false,\"rawData\":false},"
                +"\"exerciseBank\":[{\"id\":\"synthetic-one\",\"name\":\"Synthetic exercise\",\"updatedAt\":\"2026-10-23T12:00:00Z\","
                +"\"syncRevision\":{\"counter\":1,\"deviceId\":\"device-own\"}}],\"packages\":[],\"tombstones\":{\"exerciseBank\":[]}}")
                .put("roomId","synthetic-room").put("origin",new JSONObject().put("deviceId",device)
                        .put("therapistId",device).put("displayName","Synthetic device").put("roomId","synthetic-room"));
    }
    private interface Scenario{void run()throws Exception;}
    private static void scenario(String name,Scenario action,List<String> failures){
        try{action.run();}catch(Exception|AssertionError error){failures.add(name+": "+error.getMessage());}
    }
    public static void main(String[] args)throws Exception{
        List<String> failures=new ArrayList<>();
        scenario("existing persistable result remains accepted",()->{
            try(Selection test=new Selection()){
                test.select(true,READ|WRITE|PERSISTABLE);
                check(test.status().getBoolean("driveConfigured"),"control with optional result bit must configure");
                check(test.provider.takes==1&&test.provider.lastTakenFlags==(READ|WRITE),"persist only the required READ/WRITE rights");
            }
        },failures);
        for(int missing:new int[]{READ,WRITE})scenario("missing required own right "+missing,()->{
            try(Selection test=new Selection()){
                test.select(true,missing|PERSISTABLE);
                check(!test.status().getBoolean("driveConfigured"),"missing READ or WRITE must reject own binding");
                check(test.provider.takes==0&&test.provider.grants.isEmpty(),"missing rights must fail before persisting a grant");
                check(test.configurationPublications.get()==0,"rejected rights must not publish successful configuration");
            }
        },failures);
        scenario("real persistence failure still rejects",()->{
            try(Selection test=new Selection()){
                test.provider.failTake=true;test.select(true,READ|WRITE|PERSISTABLE);
                check(!test.status().getBoolean("driveConfigured"),"actual takePersistable failure must reject binding");
                check(test.provider.takes==1&&test.provider.grants.isEmpty(),"failure must come from actual provider persistence");
                check(test.configurationPublications.get()==0,"provider failure must not publish successful configuration");
            }
        },failures);
        scenario("incomplete persisted rights still reject",()->{
            try(Selection test=new Selection()){
                test.provider.grantOnTake=READ;test.select(true,READ|WRITE|PERSISTABLE);
                check(!test.status().getBoolean("driveConfigured"),"reported success without durable WRITE must reject");
                check(test.provider.releases==1&&test.provider.grants.isEmpty(),"partially acquired grant must be rolled back");
                check(test.configurationPublications.get()==0,"partial grant must not publish successful configuration");
            }
        },failures);
        scenario("provider without write capability still rejects",()->{
            try(Selection test=new Selection()){
                test.provider.supportsWrite=false;test.select(true,READ|WRITE|PERSISTABLE);
                check(!test.status().getBoolean("driveConfigured"),"read-only provider must reject own binding");
                check(test.provider.releases==1&&test.provider.grants.isEmpty(),"unsupported own target must not retain a new grant");
                check(test.configurationPublications.get()==0,"unsupported target must not publish successful configuration");
            }
        },failures);
        scenario("failed replacement preserves existing binding and grant",()->{
            try(Selection test=new Selection()){
                test.select(true,READ|WRITE|PERSISTABLE);
                byte[] previous=Files.readAllBytes(new File(test.root,"drive-sync/configuration.json").toPath());
                long generation=test.owner.getConfigurationGeneration();
                test.provider.failTake=true;
                test.select(true,READ|WRITE|PERSISTABLE,Uri.parse("content://synthetic/replacement"));
                check(java.util.Arrays.equals(previous,Files.readAllBytes(new File(test.root,"drive-sync/configuration.json").toPath())),"rejected replacement must keep the previous durable configuration byte-for-byte");
                check(test.provider.grants.size()==1&&test.provider.grants.get(OWN)==(READ|WRITE),"rejected replacement must preserve previous grant without accepting a new grant");
                check(test.configurationPublications.get()==1&&test.owner.getConfigurationGeneration()==generation,"failed replacement must not publish another configuration success");
            }
        },failures);
        scenario("READ WRITE without optional PERSISTABLE result bit",()->{
            try(Selection test=new Selection()){
                test.select(true,READ|WRITE);
                check(test.status().getBoolean("driveConfigured"),"valid READ|WRITE result without optional PERSISTABLE bit must configure the real bridge");
                check(test.provider.takes==1&&test.provider.grants.get(OWN)==(READ|WRITE),"provider must really persist the required rights");
                check(new File(test.root,"drive-sync/configuration.json").isFile(),"accepted binding must be durable, not only enqueued");
                check(test.bridge.writeSyncJson(document("device-own").toString()),"accepted own document must support a real transport write");
                check(test.provider.writes==1&&test.status().getBoolean("providerAccepted"),"provider ACK must follow the actual write");
            }
        },failures);
        scenario("READ-only peer without optional result bit",()->{
            try(Selection test=new Selection()){
                test.select(true,READ|WRITE|PERSISTABLE);
                test.provider.documents.put(PEER,document("device-peer").toString());
                test.select(false,READ);
                check(test.status().getInt("peerCount")==1,"valid peer READ result without optional PERSISTABLE bit must configure");
                check(test.provider.lastTakenFlags==READ&&test.provider.grants.get(PEER)==READ,"partner must receive READ only");
                JSONArray peers=new JSONObject(test.bridge.readSyncJson()).getJSONArray("peers");
                check(peers.length()==1&&peers.getJSONObject(0).getJSONObject("origin").getString("deviceId").equals("device-peer"),"real provider document must pass unchanged transport validation");
            }
        },failures);
        scenario("peer without READ keeps previous own binding",()->{
            try(Selection test=new Selection()){
                test.select(true,READ|WRITE|PERSISTABLE);int before=test.provider.takes;
                test.select(false,WRITE|PERSISTABLE);
                check(test.status().getBoolean("driveConfigured")&&test.status().getInt("peerCount")==0,"bad peer right must preserve existing own binding");
                check(test.provider.takes==before&&!test.provider.grants.containsKey(PEER),"peer WRITE-only result must fail before taking a grant");
                check(test.provider.grants.get(OWN)==(READ|WRITE)&&test.configurationPublications.get()==1,"bad peer must preserve own grant and avoid a second successful pairing publication");
            }
        },failures);
        if(!failures.isEmpty())throw new AssertionError("SAF bridge selection contract failed after "+checks+" checks:\n"+String.join("\n",failures));
        System.out.println("SAF bridge selection contract PASS ("+checks+" checks)");
    }
}
