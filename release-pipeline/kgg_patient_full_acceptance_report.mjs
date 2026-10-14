#!/usr/bin/env node
// Aggregates existing, synthetic-only KGG parity evidence. No product changes, uploads or Gemini API.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SHA = /^[a-f0-9]{40}$/i;
const MODES = ["legacy", "react"];
const EXPECTED_VARIANTS = ["phone:legacy", "phone:react", "tablet:legacy", "tablet:react"];
const MANIFEST_URL = "https://docs.google.com/document/d/17AA3z1oGFIxdywK52yEkUlvrDPIMoH9INlP2X_Xd-oE/edit";
const INVENTORY_PATH=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..","docs","quality","patient-react-feature-inventory-20261013.json");
export const GROUPS = [
  { id:"unit", label:"Einheiten / Startwerte / Fortschritt / Summary / History / Reload",
    ids:["PAT-UNIT-001","PAT-UNIT-002","PAT-START-001","PAT-PROG-001","PAT-SUM-001","PAT-HIST-001","PAT-STOR-001"],
    screenshot:"unit" },
  { id:"days", label:"Trainingstage / Historie / mehrere Pläne / Abschluss-QR",
    ids:["PAT-DAY-001","PAT-DAY-002","PAT-DAY-003","PAT-DAY-004","PAT-HIST-001","PAT-STOR-001","PAT-MULTI-003","PAT-FIN-001","PAT-QR-001","PAT-QR-002","PAT-QR-004"],
    screenshot:"days" },
  { id:"pain", label:"Optionale Schmerzwerte pro Satz – Einstellungen, Tage, Reload und Wechsel",
    ids:["PAT-PAIN-004"], screenshot:null }
];
const PENDING = [
  "QR-Kopieren (tatsächlicher System-Clipboard-Inhalt), Scan-/Kamera-Fallbacks und QR-Planimport sind noch nicht vollständig als Alt/Neu-Flow geprüft",
  "Übungsdatenbank, Zusatzübungen, Einstellungen, Medien/Lightbox und Progressionsauswahl noch nicht durchgängig als identischer Legacy/React-Flow belegt",
  "PWA-Installationsdialog, Offline-/Update-Recovery, Plan ersetzen/löschen und iOS-Sonderfälle bleiben durch eigene Testbatterien und reale Geräte abzusichern",
  "Die optionale Satzschmerz-Speicherfunktion ist mit eigenem Legacy/React-Gate abgedeckt; die separate neue Blitz-Darstellung aus PR #306 bleibt ein eigener nicht gemergter Produktworkstream",
  "Physisches Oppo/Android-Chrome und iPhone/Safari sind durch Playwright Chromium/WebKit nicht real getestet",
  "Gemini-Videofund grauer Frames aus vorherigem Kandidaten ist in Issue #308 ungeklärt; er darf kein automatischer PASS sein",
  "Die einmalige vollständige menschliche Geräte-/End-to-End-Abnahme ist noch nicht durchgeführt"
];

function assert(condition, message) { if(!condition) throw new Error(message); }
function boundedJson(filename, max = 1000000) {
  if(!fs.existsSync(filename)) return null;
  const stat=fs.lstatSync(filename);
  assert(stat.isFile()&&!stat.isSymbolicLink()&&stat.size>0&&stat.size<=max,
    "Invalid report evidence file");
  return JSON.parse(fs.readFileSync(filename,"utf8"));
}
function inventoryCoverage() {
  const inventory=boundedJson(INVENTORY_PATH,250000);
  if(!inventory) return {status:"MISSING",message:"Funktionsinventar fehlt; kein vollständiger Coverage-Nachweis"};
  const features=inventory.features||[];
  const ids=features.map(f=>f.id);
  if(inventory.schema!=="kgg/patient-react-inventory-snapshot/v1" ||
    !Array.isArray(inventory.features) || features.length<50 ||
    ids.some(id=>typeof id!=="string"||!/^PAT-[A-Z]+-\d{3}$/.test(id)) ||
    new Set(ids).size!==ids.length) {
    return {status:"INVALID",message:"Ungültiges oder unvollständiges Funktionsinventar"};
  }
  const unmapped=features.filter(f=>f.comparisonMapping==="NOT_MAPPED_IN_LEGACY_REACT_COMPARE");
  const mapped=features.filter(f=>f.comparisonMapping==="SCOPED_OR_PARTIAL");
  if(mapped.length+unmapped.length!==features.length){
    return {status:"INVALID",message:"Unbekannte Mapping-Kategorie"};
  }
  const categories={};
  for(const f of unmapped)categories[f.section]=(categories[f.section]||0)+1;
  const byCategory=Object.entries(categories).map(([category,count])=>({category,count}))
    .sort((a,b)=>b.count-a.count);
  return {status:"SNAPSHOT_ONLY",documentDate:inventory.source?.snapshotDate||null,
    total:features.length,mapped:mapped.length,notMapped:unmapped.length,
    byCategory,unmappedExamples:unmapped.slice(0,24).map(f=>({id:f.id,label:f.label})),
    note:"Zuordnung ist kein bestandener Test; fehlende Parity-Zuordnung bedeutet nicht ungetestete Funktion"};
}
const esc = value => String(value??"").replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function proofStatus(proof,engine,mode,sha,ids) {
  if(!proof) return {status:"NOT_EVIDENCED",reason:"Kein maschinenlesbarer Ausführungsnachweis"};
  if(!proof || proof.schema!==1 || proof.syntheticOnly!==true ||
    proof.engine!==engine || proof.mode!==mode || !Array.isArray(proof.featureIds) ||
    !ids.every(id=>proof.featureIds.includes(id))) {
    return {status:"INVALID",reason:"Nachweis-Schema/Funktionsumfang passt nicht"};
  }
  if(proof.sourceSha!==sha) return {status:"STALE",reason:"Andere Kandidaten-SHA"};
  if(proof.status!=="PASS" || !proof.assertions ||
    Object.keys(proof.assertions).length===0 ||
    Object.values(proof.assertions).some(x=>x!==true)) {
    return {status:"FAIL",reason:"Fehlende oder nicht bestandene Einzel-Assertions"};
  }
  return {status:"PASS",assertionCount:Object.keys(proof.assertions).length};
}

export function summarizeAcceptance(dir) {
  const output=path.resolve(dir);
  assert(path.basename(output)==="patient-ui-parity","Expected isolated patient-ui-parity artifact");
  const coverage=inventoryCoverage();
  const report=boundedJson(path.join(output,"report.json"));
  const sha=report?.candidateSha;
  if(!report || !SHA.test(String(sha||"")) || report.syntheticOnly!==true) {
    return {schema:1,sourceSha:null,engine:"unknown",syntheticOnly:true,
      status:"INCOMPLETE",blocks:[{id:"parity",status:"NOT_EVIDENCED"}],
      pending:PENDING,advisory:{status:"NOT_RUN"},coverage,reviewRequired:true,
      manualAcceptancePending:true};
  }
  const engine=report.engine;
  const hasVariants=EXPECTED_VARIANTS.every(k=>(report.variants||[]).some(v=>v.viewport+":"+v.mode===k));
  const hardChecks=(report.checks||[]).filter(c=>c.pass===true).length;
  const failures=(report.checks||[]).filter(c=>c.pass===false).length;
  const parityPass=(["chromium","webkit"].includes(engine) && report.status==="PASS" &&
    hasVariants && hardChecks>=300 && failures===0 &&
    Array.isArray(report.unexpectedDifferences) &&
    report.unexpectedDifferences.length===0);
  const blocks=[{id:"parity",label:"NumPad / Transfer / Pixel / Persistenz",
    status:parityPass?"PASS":"FAIL",hardChecks,failures,
    observations:(report.checks||[]).filter(c=>c.pass===null).length,
    featureIds:["PAT-NUM-002","PAT-NUM-003","PAT-NUM-004","PAT-NUM-005","PAT-PREV-002","PAT-PREV-003","PAT-PREV-004","PAT-PREV-007","PAT-STATE-002"]}];
  for(const group of GROUPS) {
    const variants=MODES.map(mode=>{
      const file=group.id+"-"+mode+".json";
      const result=proofStatus(boundedJson(path.join(output,file),64000),engine,mode,sha,group.ids);
      return {mode,...result};
    });
    const status=variants.every(v=>v.status==="PASS")?"PASS":
      variants.some(v=>v.status==="FAIL"||v.status==="INVALID"||v.status==="STALE")?"REVIEW_REQUIRED":"NOT_EVIDENCED";
    blocks.push({id:group.id,label:group.label,status,featureIds:group.ids,variants});
  }
  const review=boundedJson(path.join(output,"gemini-web-review.json"),64000);
  const advisory=!review?{status:"NOT_RUN"}:
    review.advisoryOnly!==true || review.sourceSha!==sha ||
      !["PASS","REVIEW_REQUIRED","UNAVAILABLE","INCONCLUSIVE"].includes(review.status)
      ? {status:"STALE_OR_INVALID"}
      : {status:review.status,findings:(review.findings||[]).slice(0,20)};
  const scopePass=blocks.every(g=>g.status==="PASS");
  const reviewRequired=!scopePass || coverage.status!=="SNAPSHOT_ONLY" ||
    ["REVIEW_REQUIRED","STALE_OR_INVALID"].includes(advisory.status);
  return {schema:1,sourceSha:sha,engine,syntheticOnly:true,
    status:reviewRequired?"REVIEW_REQUIRED":"AUTOMATED_SCOPE_PASS_FINAL_PENDING",
    reviewRequired,manualAcceptancePending:true,blocks,advisory,coverage,pending:PENDING,
    coverageStatement:"Nur explizit nachgewiesene synthetische Flows; keine gesamte App- oder Hardware-Freigabe",
    canonicalManifest:MANIFEST_URL,
    issue308:"https://github.com/Kayus24/kgg/issues/308"};
}

export function renderAcceptanceHtml(summary) {
  const row=g=>"<tr><th>"+esc(g.label||g.id)+"</th><td>"+esc(g.status)+"</td><td>"+
    esc((g.variants||[]).map(v=>v.mode+": "+v.status).join(" · ")||String(g.hardChecks??""))+"</td></tr>";
  const preview=(name,title)=>"<figure><img loading='lazy' src='"+esc(name)+
    "' alt='"+esc(title)+"'/><figcaption>"+esc(title)+"</figcaption></figure>";
  const imgs=[
    ["unit-legacy.png","Unit/History – Legacy"],
    ["unit-react.png","Unit/History – React"],
    ["days-legacy-interim-qr.png","Zwischenstands-QR – Legacy"],
    ["days-react-interim-qr.png","Zwischenstands-QR – React"],
    ["days-legacy-final-qr.png","Finaler QR – Legacy"],
    ["days-react-final-qr.png","Finaler QR – React"],
    ["days-legacy-history-100.png","Tag 100 History – Legacy"],
    ["days-react-history-100.png","Tag 100 History – React"]
  ].map(a=>preview(...a)).join("");
  const coverage=summary.coverage||{status:"MISSING"};
  const mappedContent=coverage.status==="SNAPSHOT_ONLY"
    ? "<p><strong>"+esc(coverage.mapped)+" von "+esc(coverage.total)+
      " dokumentierten Funktionen</strong> besitzen eine Zuordnung zu einem Alt/Neu-Test."+
      " Für "+esc(coverage.notMapped)+" fehlt diese Zuordnung.</p>"+
      "<p>"+esc(coverage.note)+"</p>"+
      "<details><summary>Noch nicht zugeordnete Funktionsbereiche</summary><ul>"+
      coverage.byCategory.map(x=>"<li>"+esc(x.category)+": "+esc(x.count)+"</li>").join("")+
      "</ul></details>"
    : "<p>Funktionsinventar nicht hinreichend belegt: "+esc(coverage.status)+
      ". Eine Gesamtabnahme ist nicht möglich.</p>";
  const css="*{box-sizing:border-box}body{font:16px/1.5 system-ui;margin:0 auto;padding:24px;max-width:1150px;color:#1f2937;background:#f8fafc}"+
    "h1{font-size:1.7rem}h2{font-size:1.2rem;margin-top:2rem}a{color:#075db5}"+
    "table{width:100%;border-collapse:collapse;background:white}td,th{text-align:left;padding:12px;border-bottom:1px solid #e5e7eb}"+
    ".figures{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:white;padding:8px;border:1px solid #e5e7eb;border-radius:12px}img{max-width:100%;max-height:650px;display:block;margin:auto}figcaption{text-align:center;font-size:.9rem}"+
    ".meta{padding:10px 0;border-bottom:1px solid #cbd5e1}li{margin-bottom:10px}@media(max-width:650px){.figures{grid-template-columns:1fr}}";
  return "<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"+
    "<title>KGG – Legacy/React Gesamtabnahme-Evidenz</title><style>"+css+"</style></head><body>"+
    "<h1>KGG – automatische Legacy/React Gesamtabnahme-Vorbereitung</h1>"+
    "<p class='meta'><strong>"+esc(summary.status)+"</strong> · Engine "+esc(summary.engine)+
    " · SHA <code>"+esc(summary.sourceSha||"unknown")+"</code></p>"+
    "<p>Dies ist ein belegter Testausschnitt, keine komplette App- oder Hardware-Abnahme. "+
    "<a href='report.html'>NumPad-Videos und Pixelvergleiche ansehen</a></p>"+
    "<h2>Prüfblöcke</h2><table><thead><tr><th>Testbereich</th><th>Ergebnis</th><th>Varianten/Assertions</th></tr></thead><tbody>"+
    summary.blocks.map(row).join("")+"</tbody></table>"+
    "<h2>Gesamtes Patienten-Funktionsinventar (Drive-Snapshot)</h2>"+mappedContent+
    "<h2>Gemini-Web-Zusatzreview</h2><p>"+esc(summary.advisory.status)+
    ". Ein externes Modell ersetzt weder Playwright-Assertions noch die Realgeräteprüfung. "+
    "<a href='"+esc(summary.issue308)+"'>Separates Bildaussetzer-Ticket</a></p>"+
    "<h2>Weitere Abnahme- und Coverage-Lücken</h2><ul>"+
    summary.pending.map(p=>"<li>"+esc(p)+"</li>").join("")+"</ul>"+
    "<p>Quelle: <a href='"+esc(summary.canonicalManifest)+"'>kanonisches Patienten-Featuremanifest</a>.</p>"+
    "<h2>Legacy/React-Vergleich: Einheiten, History, finaler QR</h2><div class='figures'>"+
    imgs+"</div><p>Fehlende Bilder bedeuten fehlende Evidenz, nicht bestanden.</p></body></html>";
}
async function main(){
  if(process.argv.length!==3)throw new Error("Usage: node kgg_patient_full_acceptance_report.mjs PATH_TO_patient-ui-parity");
  const dir=path.resolve(process.argv[2]);
  const summary=summarizeAcceptance(dir);
  fs.writeFileSync(path.join(dir,"acceptance.json"),JSON.stringify(summary,null,2)+"\n");
  fs.writeFileSync(path.join(dir,"acceptance.html"),renderAcceptanceHtml(summary));
  console.log("KGG unified acceptance: "+summary.status+"; blocks="+summary.blocks.map(x=>x.id+"="+x.status).join(","));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  main().catch(e=>{console.error("KGG acceptance report failed: "+e.message);process.exitCode=1});
}
