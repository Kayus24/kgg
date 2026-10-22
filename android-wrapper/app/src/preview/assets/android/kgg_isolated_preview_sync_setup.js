(function () {
  'use strict';
  // Loaded only by the explicitly named isolated Preview Debug build.
  // This is a private Followconfig/empty-local-mesh test setup, not a sync transport.
  if (window.KGGIsolatedPreviewSyncSetup) return;
  if (window.KGGAndroidSync) throw new Error('unexpected_local_bridge');
  // Reuse the Core's private fallback key so pairing before native-ready survives.
  var followKey = 'kgg_sync_pair_follow_config_v1';
  function followConfig() {
    var raw = localStorage.getItem(followKey);
    if (raw === null) return {therapistId:'', syncRoomId:'', followedTherapists:[]};
    var config = JSON.parse(raw);
    if (!config || typeof config !== 'object' || Array.isArray(config)) throw new Error('private_follow_config_invalid');
    return config;
  }
  function emptyMesh() {
    return JSON.stringify({
      kind:'kgg_cross_data_safe_sync_mesh', version:1,
      roomId:String(followConfig().syncRoomId || localStorage.getItem('kgg_sync_room_id_v1') || ''),
      peers:[]
    });
  }
  window.KGGAndroidSync = Object.freeze({
    getStatus:function () {
      return JSON.stringify({
        available:true, platform:'android', transport:'local',
        syncRoomId:String(followConfig().syncRoomId || ''), peerCount:0,
        writeUsesSharedFolder:false, isolatedPreviewSetup:true
      });
    },
    readSyncJson:emptyMesh,
    listPeerSyncJson:emptyMesh,
    // The unchanged common Bootstrap stages the genuine native private outbox first.
    // Until SAF setup this false keeps the real Core dirty/retrying, never cloud-success.
    writeSyncJson:function () { return false; },
    readFollowConfig:function () { return JSON.stringify(followConfig()); },
    writeFollowConfig:function (text) {
      try {
        var config = JSON.parse(text);
        if (!config || typeof config !== 'object' || Array.isArray(config)) return false;
        localStorage.setItem(followKey, JSON.stringify(config));
        return true;
      } catch (err) { return false; }
    }
  });
  window.KGGIsolatedPreviewSyncSetup = Object.freeze({
    kind:'kgg_isolated_preview_sync_setup', version:1, privateFollowConfigShim:true
  });
})();
