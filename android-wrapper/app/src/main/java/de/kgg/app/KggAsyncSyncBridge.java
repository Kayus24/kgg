package de.kgg.app;

import android.webkit.JavascriptInterface;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.Callable;
import java.util.function.Consumer;

/** Optional promise-capable adapter. Existing local/SAF validators remain authoritative. */
final class KggAsyncSyncBridge implements AutoCloseable {
    // Activity recreation must not create a second provider writer while the
    // previous Activity's accepted jobs drain. Capacity remains 1+1 process-wide.
    private static final KggSyncRequestCoordinator.SerialOwner IO_OWNER=KggSyncRequestCoordinator.newExecutor();
    private final KggSyncBridge local;
    private final KggDriveSyncBridge drive;
    private final KggSyncRequestCoordinator coordinator;
    private volatile String peerMetadata=emptyPeers();
    private final Handler initializationHandler=new Handler(Looper.getMainLooper());
    private volatile boolean closed;
    private Runnable initialize;
    KggAsyncSyncBridge(KggSyncBridge local,KggDriveSyncBridge drive,Consumer<String> completion,Runnable ready){
        this.local=local;this.drive=drive;
        coordinator=new KggSyncRequestCoordinator(this::prepare,this::statusFromWorker,()->peerMetadata,completion,IO_OWNER);
        drive.attachSyncOwner(coordinator,()->{peerMetadata=emptyPeers();coordinator.invalidateConfiguration();});
        local.attachSyncOwner(coordinator,()->{
            peerMetadata=emptyPeers();coordinator.invalidateConfiguration();
        });
        initialize=()->{if(!closed&&!coordinator.enqueueControl(()->{},ready))
            initializationHandler.postDelayed(initialize,250);};
        initialize.run();
    }
    @JavascriptInterface public int getAsyncVersion(){return 1;}
    @JavascriptInterface public String getCapabilities(){
        return "{\"version\":1,\"operations\":[\"read\",\"write\",\"configureOwnDriveFile\",\"selectDrivePeerFiles\",\"disconnectDrive\"]}";
    }
    @JavascriptInterface public long getConfigurationGeneration(){return coordinator.getConfigurationGeneration();}
    @JavascriptInterface public String getStatusSnapshot(){return coordinator.getStatusSnapshot();}
    @JavascriptInterface public String getPeerSnapshot(){return coordinator.getPeerSnapshot();}
    @JavascriptInterface public String getFollowConfigSnapshot(){return local.readFollowConfig();}
    @JavascriptInterface public boolean writeFollowConfig(String json){return local.writeFollowConfig(json);}
    @JavascriptInterface public boolean requestSyncJson(String header,String payload){return coordinator.requestSyncJson(header,payload);}
    private Callable<String> prepare(String header,String payload){
        // Header <=2 KB; no payload parse/quote or provider access on the bridge
        // thread. The captured generation is checked again by the serial owner.
        final String operation;final long generation;
        try{JSONObject request=new JSONObject(header);operation=request.getString("operation");generation=request.getLong("configurationGeneration");}
        catch(Exception invalid){throw new IllegalArgumentException("invalid_header");}
        final String immutablePayload=payload;
        final String boundFollowConfiguration=local.readFollowConfig();
        return ()->perform(operation,immutablePayload,boundFollowConfiguration,generation);
    }
    private String perform(String operation,String payload,String boundFollowConfiguration,long generation)throws Exception{
        switch(operation){
            case "read":{
                boolean configured=new JSONObject(drive.getStatus()).optBoolean("driveConfigured");
                String raw=configured?drive.readSyncJson():local.readSyncJson(boundFollowConfiguration);
                JSONObject document=new JSONObject(raw);
                if("kgg_sync_transport_error".equals(document.optString("kind")))throw new IllegalStateException(document.optString("error","read_failed"));
                String peers=metadata(document);coordinator.publishIfCurrent(generation,()->peerMetadata=peers);return raw;
            }
            case "write":{
                boolean configured=new JSONObject(drive.getStatus()).optBoolean("driveConfigured");
                boolean accepted=drive.writeSyncJson(payload);
                return Boolean.toString(configured?accepted:local.writeSyncJson(payload,boundFollowConfiguration));
            }
            case "configureOwnDriveFile":return Boolean.toString(drive.configureOwnDriveFile(payload));
            case "selectDrivePeerFiles":return Boolean.toString(drive.selectDrivePeerFiles(payload));
            case "disconnectDrive":return Boolean.toString(drive.disconnectDrive());
            default:throw new IllegalStateException("unsupported_operation");
        }
    }
    private String statusFromWorker(){
        try{
            JSONObject saf=new JSONObject(drive.getStatus());
            if(saf.optBoolean("driveConfigured"))return saf.put("available",true).put("platform","android").toString();
            JSONObject status=new JSONObject(local.getStatus());
            java.util.Iterator<String> keys=saf.keys();while(keys.hasNext()){String key=keys.next();status.put(key,saf.get(key));}
            return status.toString();
        }catch(Exception failure){throw new IllegalStateException("snapshot_failed");}
    }
    private static String emptyPeers(){return "{\"kind\":\"kgg_cross_data_safe_sync_mesh\",\"version\":1,\"roomId\":\"\",\"peers\":[],\"stale\":true,\"updatedAt\":\"\"}";}
    private static String metadata(JSONObject document)throws Exception{
        JSONArray sources=document.optJSONArray("peers"),result=new JSONArray();
        if(sources==null)sources=new JSONArray().put(document);
        for(int i=0;i<sources.length();i++){
            JSONObject peer=sources.getJSONObject(i),origin=peer.optJSONObject("origin");if(origin==null)continue;
            JSONObject small=new JSONObject();for(String field:new String[]{"deviceId","therapistId","displayName","roomId"})if(origin.has(field))small.put(field,origin.optString(field));
            result.put(new JSONObject().put("origin",small).put("exportedAt",peer.optString("exportedAt")));
        }
        return new JSONObject().put("kind","kgg_cross_data_safe_sync_mesh").put("version",1)
                .put("roomId",document.optString("roomId")).put("peers",result)
                .put("stale",false).put("updatedAt",java.time.Instant.now().toString()).toString();
    }
    @Override public void close(){closed=true;initializationHandler.removeCallbacks(initialize);coordinator.close();}
}
