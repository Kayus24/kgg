#!/usr/bin/env node
// Static offline visual evidence page; synthetic artifacts only.
import fs from "node:fs";
import path from "node:path";

const dir = path.resolve(process.argv[2] || "");
if (!dir || dir === path.parse(dir).root || path.basename(dir) !== "patient-ui-parity") {
  throw new Error("Expected isolated patient-ui-parity artifact directory");
}
const file = path.join(dir, "report.json");
const report = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) :
  { status: "INCOMPLETE", engine: "unknown", checks: [], unexpectedDifferences: [] };
if (report.syntheticOnly === false) throw new Error("Non-synthetic evidence is forbidden");
const esc = v => String(v ?? "").replace(/[&<>"']/g, m => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[m]);
const steps = [
  ["pair-kg", "kg geÃ¶ffnet Â· dreigeteilte Ãœbernahme"],
  ["pair-wdh", "Wdh ausgewÃ¤hlt"],
  ["remaining-kg", "Wdh Ã¼bernommen Â· ein kg-Segment bleibt"],
  ["manual-zero", "Manuelle Eingabe / Backspace / 0"],
  ["saved-zero", "0 mit OK bestÃ¤tigt"]
];
const differences = report.unexpectedDifferences || [];
let sections = "";
for (const view of ["phone", "tablet"]) {
  sections += "<h2>" + esc(view) + " â€“ Videos</h2><div class='comparison'>";
  for (const mode of ["legacy", "react"]) {
    const name = view + "-" + mode + ".webm";
    sections += "<article><h3>" + esc(mode) + "</h3>" +
      (fs.existsSync(path.join(dir, name))
        ? "<video controls playsinline preload='metadata' src='" + name + "'></video>"
        : "<p>Video fehlt: " + esc(name) + "</p>") + "</article>";
  }
  sections += "</div>";
  for (const [step, label] of steps) {
    sections += "<h3>" + esc(view + " Â· " + label) + "</h3><div class='comparison'>";
    for (const mode of ["legacy", "react"]) {
      const name = view + "-" + mode + "-" + step + ".png";
      sections += "<article><h4>" + esc(mode) + "</h4>" +
        (fs.existsSync(path.join(dir, name))
          ? "<img loading='lazy' src='" + name + "' alt='" + esc(mode + " " + label) + "' />"
          : "<p>Screenshot fehlt</p>") + "</article>";
    }
    sections += "</div>";
  }
}
const findings = differences.length
  ? "<ul>" + differences.map(d => "<li><strong>" + esc(d.viewport + " / " + d.step) +
      "</strong> Â· " + esc(d.kind) + " Â· " + esc(JSON.stringify(d).slice(0, 350)) + "</li>").join("") + "</ul>"
  : "<p>Keine unerwarteten Unterschiede im geprÃ¼ften Scope gemeldet.</p>";
const css = "*{box-sizing:border-box}body{max-width:1300px;margin:0 auto;padding:20px;font:16px/1.45 system-ui;color:#172033;background:#f4f7fb}" +
  "h1{margin:0}h2{margin-top:44px;border-bottom:2px solid #dde5ef;padding-bottom:8px}h3{margin-top:26px}" +
  ".comparison{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}" +
  "article{background:#fff;border:1px solid #d3deed;border-radius:14px;padding:12px;min-width:0}article h3,article h4{margin:0 0 10px}" +
  "video,img{width:100%;max-height:760px;object-fit:contain;background:#fff}" +
  ".note{border-left:4px solid #64748b;background:#fff;padding:12px;margin:14px 0}" +
  "@media(max-width:650px){.comparison{grid-template-columns:1fr}}";
const html = [
  "<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
  "<title>KGG UI Legacy/React Parity</title><style>" + css + "</style></head><body>",
  "<h1>KGG Â· Legacy/React Gesamtabnahme-Vorbereitung</h1>",
  "<p><strong>Deterministische Tests: " + esc(report.status) + "</strong> Â· " + esc(report.engine) +
    " Â· " + esc((report.checks || []).filter(c => c.pass === true).length) + " PrÃ¼fungen</p>",
  "<p>Quell-SHA: <code>" + esc(report.gitSha || "unknown") + "</code></p>",
  "<div class='note'>Synthetische Daten. Erlaubte Unterschiede: neuer React-Kopf, NEU-Label und Transferleiste." +
    " UnverÃ¤nderte Tasten/Aktionsbereiche werden pixelgenau geprÃ¼ft." +
    " Abgedeckt: NumPad, Übernahme, Links/Rechts, Sekunden und Neuladen; Schmerz pro Satz wird separat geprüft. Nicht die gesamte Patienten-App. Absolute Scroll-Offsets verschiedener Karten sind nur Beobachtungen, keine bestandenen Invarianten.</div>",
  "<h2>Abweichungen</h2>" + findings,
  sections,
  "<p>FÃ¼r die endgÃ¼ltige Gesamtabnahme bleiben nicht automatisierte App-Flows gesondert zu prÃ¼fen.</p>",
  "</body></html>"
].join("\n");
fs.writeFileSync(path.join(dir, "report.html"), html);
if (process.env.GITHUB_STEP_SUMMARY) {
  fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,
    "## KGG Legacy/React parity\n\n**" + report.status + "** Â· " +
    esc(report.engine) + " Â· " + (report.checks || []).filter(c => c.pass === true).length + " checks Â· " +
    differences.length + " differences\n\nDownload artifact â†’ unzip â†’ open **report.html**.\n\n");
}
console.log("KGG visual parity report: " + report.status + " (report.html)");
