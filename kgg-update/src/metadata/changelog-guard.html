
<!-- BEGIN kgg-changelog-size-guard: console/helper warning when embedded changelog grows too large -->
<script id="kgg-changelog-size-guard">
(function(){
  "use strict";
  var FALLBACK_POLICY = {
    warnAtEntries: 18,
    maxEmbeddedEntries: 30,
    warnAtBytes: 35000,
    maxEmbeddedBytes: 55000
  };
  function readJsonBlock(id){
    var el = document.getElementById(id);
    if(!el) return null;
    try{ return JSON.parse((el.textContent||"").trim()); }
    catch(err){ return {__parseError:String(err)}; }
  }
  function changelogSizeReport(){
    var el = document.getElementById("kgg-changelog");
    var rules = readJsonBlock("kgg-patch-rules") || {};
    var policy = (rules && rules.changelogSizePolicy) || FALLBACK_POLICY;
    var text = el ? (el.textContent || "") : "";
    var entries = 0;
    var parseError = "";
    try{
      var data = text ? JSON.parse(text) : {};
      entries = Array.isArray(data.entries) ? data.entries.length : 0;
    }catch(err){
      parseError = String(err);
    }
    var bytes = 0;
    try{ bytes = new TextEncoder().encode(text).length; }
    catch(err){ bytes = text.length; }
    var warnings = [];
    if(!el) warnings.push("kgg-changelog block missing");
    if(parseError) warnings.push("kgg-changelog parse error: " + parseError);
    if(entries >= Number(policy.warnAtEntries || FALLBACK_POLICY.warnAtEntries)){
      warnings.push("embedded changelog entries approaching limit: " + entries + "/" + (policy.maxEmbeddedEntries || FALLBACK_POLICY.maxEmbeddedEntries));
    }
    if(bytes >= Number(policy.warnAtBytes || FALLBACK_POLICY.warnAtBytes)){
      warnings.push("embedded changelog bytes approaching limit: " + bytes + "/" + (policy.maxEmbeddedBytes || FALLBACK_POLICY.maxEmbeddedBytes));
    }
    return {
      entries: entries,
      bytes: bytes,
      policy: policy,
      warnings: warnings,
      shouldWarn: warnings.length > 0
    };
  }
  window.KGG_PATCH_GUARD = window.KGG_PATCH_GUARD || {};
  window.KGG_PATCH_GUARD.readSourceTruth = function(){ return readJsonBlock("kgg-source-truth"); };
  window.KGG_PATCH_GUARD.readChangelog = function(){ return readJsonBlock("kgg-changelog"); };
  window.KGG_PATCH_GUARD.readPatchRules = function(){ return readJsonBlock("kgg-patch-rules"); };
  window.KGG_PATCH_GUARD.checkChangelogSize = changelogSizeReport;
  var report = changelogSizeReport();
  window.KGG_PATCH_GUARD.lastChangelogSizeReport = report;
  if(report.shouldWarn && console && console.warn){
    console.warn("KGG changelog/source-truth warning:", report);
  }
})();
</script>
<!-- END kgg-changelog-size-guard -->
