#!/usr/bin/env python3
"""Generate and evaluate blind full-app KGG Repair-Lab challenges."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))
import kgg_gpt_write_gate as write_gate  # noqa: E402
import kgg_new_patch as module_patch  # noqa: E402


SOURCE_HTML = ROOT / "kgg-update" / "index.html"
SMOKE_SCRIPT = ROOT / "release-pipeline" / "kgg_gpt_repair_lab_smoke.js"
CRITICAL_TEST = r"cmd /c release-pipeline\run-kgg-tests.cmd --level critical"
UI_TEST = r"cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression"
CHUNK_SIZE = 72_000


class RepairLabError(RuntimeError):
    pass


@dataclass(frozen=True)
class Mutation:
    old: str
    new: str
    expected: int = 1
    replace_count: int = 1


@dataclass(frozen=True)
class RepairCase:
    key: str
    title: str
    symptom: str
    expected_behavior: tuple[str, ...]
    mutation: Mutation
    sample_content: str
    holdout: bool = False


def patch_script(body: str) -> str:
    return (
        '<script id="__KGG_PATCH_ID__">\n'
        '(function(){\n'
        '  "use strict";\n'
        '  const PATCH_ID="__KGG_PATCH_ID__";\n'
        f"{body.rstrip()}\n"
        '  window.KGG_PATCHES=window.KGG_PATCHES||{};\n'
        '  window.KGG_PATCHES[PATCH_ID]={installed:true,source:"repair-lab"};\n'
        '})();\n'
        '</script>\n'
    )


CASES: tuple[RepairCase, ...] = (
    RepairCase(
        key="phone-admin-menu",
        title="Phone admin menu restore",
        symptom="Im Handy-Adminmodus fehlt das Drei-Punkte-Menue im Plan-Kopf; die enthaltenen Adminaktionen sind nicht erreichbar.",
        expected_behavior=("Menue ist im Plan-Kopf sichtbar.", "Ein Tap oeffnet das vorhandene Untermenue."),
        mutation=Mutation('root.id="kggPhoneAdminMenu";', 'root.id="kggPhoneAdminMenuBroken";'),
        sample_content=patch_script(
            """  function repair(){
    const broken=document.getElementById("kggPhoneAdminMenuBroken");
    if(broken)broken.id="kggPhoneAdminMenu";
    const menu=document.getElementById("kggPhoneAdminMenu");
    const header=document.querySelector("#createPanel.planMode .planHeader")||document.querySelector("#createPanel .planHeader");
    if(menu&&header&&!header.contains(menu))header.appendChild(menu);
  }
  repair();[80,240,700].forEach(ms=>setTimeout(repair,ms));"""
        ),
    ),
    RepairCase(
        key="phone-photo-menu",
        title="Phone photo menu restore",
        symptom="Der kleine Foto-Auswahlgriff im Scan-Button fehlt; Kamera und Galerie lassen sich ueber diesen Griff nicht aufklappen.",
        expected_behavior=("Foto-Griff liegt im Scan-Button.", "Ein Tap oeffnet das Foto-Menue."),
        mutation=Mutation('toggle.id="phonePhotoMenuToggle";', 'toggle.id="phonePhotoMenuToggleBroken";', expected=2, replace_count=2),
        sample_content=patch_script(
            """  function repair(){
    if(document.getElementById("phonePhotoMenuToggle"))return;
    const nodes=Array.from(document.querySelectorAll('[id="phonePhotoMenuToggleBroken"]'));
    const scan=document.getElementById("scanBtn");
    const keep=nodes.find(node=>scan&&scan.contains(node))||nodes[nodes.length-1];
    nodes.forEach(node=>{if(node!==keep)node.remove();});
    if(keep)keep.id="phonePhotoMenuToggle";
  }
  repair();[80,240,700].forEach(ms=>setTimeout(repair,ms));"""
        ),
    ),
    RepairCase(
        key="bank-thumbnails",
        title="Exercise bank thumbnails restore",
        symptom="Uebungen mit lokalem Bild zeigen in der Uebungsdatenbank keinen Bildplatzhalter und kein Vorschaubild mehr.",
        expected_behavior=("Bilduebung rendert einen Thumbnail-Knoten.", "Fehlender Blob bleibt als sichtbarer Fallback erkennbar."),
        mutation=Mutation(
            'return \'<span class="bankThumb bankThumbFallback" data-bank-thumb-id="\'+escapeHtml(media.id)+\'" title="Bild vorhanden" aria-hidden="true"></span>\';',
            'return \'<span class="bankThumb bankThumbFallback" data-bank-thumb-disabled="\'+escapeHtml(media.id)+\'" title="Bild vorhanden" aria-hidden="true"></span>\';',
        ),
        sample_content=patch_script(
            """  function repair(root){
    (root||document).querySelectorAll("[data-bank-thumb-disabled]").forEach(node=>{
      node.setAttribute("data-bank-thumb-id",node.getAttribute("data-bank-thumb-disabled")||"");
      node.removeAttribute("data-bank-thumb-disabled");
      node.classList.add("bankThumbFallback");
    });
  }
  repair();new MutationObserver(()=>repair()).observe(document.documentElement,{childList:true,subtree:true});"""
        ),
    ),
    RepairCase(
        key="clear-live-input",
        title="Live exercise clear restore",
        symptom="Das X an der Uebungseingabe leert den aktuellen Text nicht mehr; ein daraus erzeugter Live-Entwurf bleibt im Plan stehen.",
        expected_behavior=("X leert die Texteingabe.", "Der Live-Text-Entwurf verschwindet, bestehende Planuebungen bleiben erhalten."),
        mutation=Mutation("$('clearInput').onclick=()=>{clearInputAndRemoveLiveTextExercises();};", "$('clearInput').onclick=()=>{};"),
        sample_content=patch_script(
            """  const clear=document.getElementById("clearInput");
  if(clear)clear.addEventListener("click",function(ev){
    ev.preventDefault();ev.stopImmediatePropagation();
    const input=document.getElementById("exerciseInput");
    if(!input)return;
    input.value="";input.dispatchEvent(new Event("input",{bubbles:true}));
  },true);"""
        ),
    ),
    RepairCase(
        key="phone-history-drawers",
        title="Phone history drawers restore",
        symptom="Auf dem Handy reagieren Letzte Plaene und Uebungspakete nicht mehr als sichere Drawer; Inhalte werden nicht verlaesslich geoeffnet und geschlossen.",
        expected_behavior=("Letzte Plaene oeffnet den sicheren Drawer.", "Uebungspakete oeffnet danach den sicheren Drawer ohne Seitenfehler."),
        mutation=Mutation(
            'bindDrawerButton("recentToggle","recent");\n    bindDrawerButton("packageToggle","package");',
            'void "repair-disabled-recent";\n    void "repair-disabled-package";',
        ),
        sample_content=patch_script(
            """  function bind(id,kind){
    const button=document.getElementById(id);
    if(!button||button.dataset.repairLabDrawer==="1")return;
    button.dataset.repairLabDrawer="1";
    button.addEventListener("click",function(ev){
      const api=window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045;
      if(!api||typeof api.openDrawer!=="function")return;
      ev.preventDefault();ev.stopImmediatePropagation();api.openDrawer(kind);
    },true);
  }
  function repair(){bind("recentToggle","recent");bind("packageToggle","package");}
  repair();[80,240,700].forEach(ms=>setTimeout(repair,ms));"""
        ),
    ),
    RepairCase(
        key="tablet-editor-layout",
        title="Tablet editor layout restore",
        symptom="Der Uebungseditor faellt auf dem Tablet in ein schmales Einspalten-Layout zurueck; Medien und Felder stehen nicht mehr nebeneinander.",
        expected_behavior=("Editor ist ein zweispaltiges Grid.", "Speichern und Abbrechen bleiben im sichtbaren Dialog."),
        mutation=Mutation(
            "#editorModal .editorSheet{\n      width:min(94vw,920px)!important;",
            "#editorModalBroken .editorSheet{\n      width:min(94vw,920px)!important;",
        ),
        sample_content=(
            '<style id="__KGG_PATCH_ID__-style">\n'
            '@media(min-width:760px){#editorModal .editorSheet{width:min(94vw,920px)!important;max-height:min(90vh,760px)!important;overflow:hidden!important;display:grid!important;grid-template-columns:minmax(0,1fr) minmax(300px,.92fr)!important;grid-template-areas:"header header" "name media" "sets media" "units media" "start media" "advanced media" "actions actions" "cancel cancel"!important;column-gap:14px!important;row-gap:9px!important;padding:16px!important}}\n'
            '</style>\n'
            + patch_script("  // Layout restoration is provided by the scoped style above.")
        ),
    ),
    RepairCase(
        key="tablet-card-reorder",
        title="Tablet card reorder restore",
        symptom="Langes Druecken auf die freie Flaeche einer Plan-Karte startet auf dem Tablet kein Reorder mehr; nur der kleine Drag-Handle besitzt noch die interne Funktion.",
        expected_behavior=("Langes Druecken auf die Kartenflaeche startet Reorder.", "Loslassen beendet den Zustand ohne Lift- oder Platzhalter-Reste."),
        mutation=Mutation(
            "card.addEventListener('pointerdown',ev=>{\n        if(!isTabletLayout())return;",
            "card.addEventListener('kgg-disabled-pointerdown',ev=>{\n        if(!isTabletLayout())return;",
        ),
        sample_content=patch_script(
            """  document.addEventListener("pointerdown",function(ev){
    if(!window.matchMedia("(min-width:760px)").matches)return;
    const card=ev.target&&ev.target.closest&&ev.target.closest("#planList .planCard[data-plan-id]");
    if(!card||ev.target.closest("button,input,textarea,select,a,.planCardActions,.drag"))return;
    const handle=card.querySelector(".drag[data-sort-id]");if(!handle)return;
    handle.dispatchEvent(new PointerEvent("pointerdown",{bubbles:true,cancelable:true,pointerId:ev.pointerId,pointerType:ev.pointerType||"touch",isPrimary:true,clientX:ev.clientX,clientY:ev.clientY,button:0,buttons:1}));
  },true);"""
        ),
    ),
    RepairCase(
        key="tablet-scale-persistence",
        title="Tablet scale persistence restore",
        symptom="Eine gespeicherte Tablet-UI-Skalierung wird beim Neustart ignoriert; weitere Plus/Minus-Aenderungen landen nicht mehr unter dem bestehenden Einstellungs-Schluessel.",
        expected_behavior=("Gespeicherte 125 Prozent werden beim Start angewendet.", "Plus schreibt den neuen Wert wieder in denselben Schluessel."),
        mutation=Mutation("scale:'kgg_tablet_ui_scale'", "scale:'kgg_tablet_ui_scale_broken'"),
        sample_content=patch_script(
            """  const stableKey="kgg_tablet_ui_scale",brokenKey="kgg_tablet_ui_scale_broken";
  function apply(value){
    if(value==null)value=Number(localStorage.getItem(stableKey))||1;
    localStorage.setItem(stableKey,String(value));localStorage.setItem(brokenKey,String(value));
    document.documentElement.style.setProperty("--kgg-tablet-ui-scale",String(value));
    ["tabletScaleValue","tabletSplitScaleValue"].forEach(id=>{const node=document.getElementById(id);if(node)node.textContent=Math.round(value*100)+"%";});
  }
  apply();
  document.addEventListener("click",function(ev){
    const button=ev.target.closest("#tabletScalePlus,#tabletScaleMinus");if(!button)return;
    ev.preventDefault();ev.stopImmediatePropagation();
    const delta=button.id==="tabletScalePlus"?.05:-.05;
    apply(Math.max(.01,Math.min(2,(Number(localStorage.getItem(stableKey))||1)+delta)));
  },true);"""
        ),
    ),
    RepairCase(
        key="tablet-layout-panel",
        title="Tablet layout panel restore",
        symptom="Der Menuepunkt Layout anpassen markiert den Bearbeitungsmodus, aber das zugehoerige Bedienpanel bleibt verborgen.",
        expected_behavior=("Layout anpassen aktiviert den Bearbeitungsmodus.", "Das Bedienpanel wird sichtbar und aria-expanded ist korrekt."),
        mutation=Mutation("if(panel)panel.hidden=!next;", "if(panel)panel.hidden=true;", expected=2, replace_count=1),
        sample_content=patch_script(
            """  document.addEventListener("click",function(ev){
    const button=ev.target.closest("#tabletMenuLayoutBtn");if(!button)return;
    ev.preventDefault();ev.stopImmediatePropagation();
    const panel=document.getElementById("tabletMenuLayoutPanel");
    document.body.classList.add("tabletLayoutEditMode");if(panel)panel.hidden=false;
    button.setAttribute("aria-expanded","true");
  },true);"""
        ),
        holdout=True,
    ),
    RepairCase(
        key="phone-menu-anchor",
        title="Phone menu anchor restore",
        symptom="Das Admin-Menue wird auf dem Handy erzeugt und laesst sich oeffnen, schwebt aber ausserhalb des Plan-Kopfes im falschen Layer.",
        expected_behavior=("Menue bleibt funktionsfaehig.", "Menue ist exakt im Plan-Kopf verankert."),
        mutation=Mutation("if(menu&&header&&!header.contains(menu))header.appendChild(menu);", "if(menu&&header&&!header.contains(menu))document.body.appendChild(menu);", expected=3, replace_count=3),
        sample_content=patch_script(
            """  function repair(){const menu=document.getElementById("kggPhoneAdminMenu");const header=document.querySelector("#createPanel.planMode .planHeader")||document.querySelector("#createPanel .planHeader");if(menu&&header&&!header.contains(menu))header.appendChild(menu);}
  repair();[80,240,700].forEach(ms=>setTimeout(repair,ms));new MutationObserver(repair).observe(document.documentElement,{childList:true,subtree:true});"""
        ),
        holdout=True,
    ),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def challenge_id(round_id: str, source_hash: str, case_key: str) -> str:
    digest = hashlib.sha256(f"{round_id}\0{source_hash}\0{case_key}".encode("utf-8")).hexdigest()[:16]
    return f"repair-{digest}"


def exact_test_command(identifier: str) -> str:
    return f"python release-pipeline/kgg_gpt_repair_lab.py --evaluate --challenge-id {identifier} --payload-file <payload.json>"


def mutate(source: str, case: RepairCase) -> str:
    count = source.count(case.mutation.old)
    if count != case.mutation.expected:
        raise RepairLabError(f"mutation anchor drift for {case.key}: expected {case.mutation.expected}, got {count}")
    result = source.replace(case.mutation.old, case.mutation.new, case.mutation.replace_count)
    if result == source:
        raise RepairLabError(f"mutation did not change source for {case.key}")
    return result


def selected_cases(include_holdouts: bool) -> list[RepairCase]:
    return [case for case in CASES if include_holdouts or not case.holdout]


def source_chunks(text: str) -> list[str]:
    return [text[index : index + CHUNK_SIZE] for index in range(0, len(text), CHUNK_SIZE)]


def build_public_manifest(case: RepairCase, identifier: str, round_id: str, source_hash: str, broken_hash: str, chunk_count: int) -> dict[str, Any]:
    return {
        "schema": 1,
        "challenge_id": identifier,
        "round_id": round_id,
        "title": case.title,
        "symptom": case.symptom,
        "expected_behavior": list(case.expected_behavior),
        "source": {
            "full_html": "admin-broken.html",
            "chunks_index": "source/index.json",
            "chunk_count": chunk_count,
            "source_sha256": source_hash,
            "broken_sha256": broken_hash,
        },
        "payload_contract": {
            "schema": "KGG modular payload v2",
            "fields": ["request_id", "title", "summary", "version_slug", "touched_areas", "required_tests", "patch_content"],
            "forbidden_fields": ["operations", "path", "file", "old_text", "new_text"],
            "patch_placeholder": "__KGG_PATCH_ID__",
            "required_tests": [exact_test_command(identifier), CRITICAL_TEST, UI_TEST],
        },
        "submission": "Dispatch evaluate_attempt with this challenge_id and payload_json. Do not request or infer hidden assertions.",
    }


def ensure_modular_source() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/build_therapist_source.py", "--check"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RepairLabError((proc.stdout + "\n" + proc.stderr).strip())


def generate_round(output: Path, round_id: str, include_holdouts: bool) -> dict[str, Any]:
    ensure_modular_source()
    source_raw = SOURCE_HTML.read_bytes()
    source = source_raw.decode("utf-8")
    source_hash = sha256_bytes(source_raw)
    public_root = output / "public"
    internal_root = output / "internal"
    public_root.mkdir(parents=True, exist_ok=True)
    internal_root.mkdir(parents=True, exist_ok=True)
    public_entries: list[dict[str, Any]] = []
    internal_entries: list[dict[str, Any]] = []
    for case in selected_cases(include_holdouts):
        identifier = challenge_id(round_id, source_hash, case.key)
        broken = mutate(source, case)
        broken_raw = broken.encode("utf-8")
        challenge_root = public_root / "challenges" / identifier
        source_root = challenge_root / "source"
        source_root.mkdir(parents=True, exist_ok=True)
        (challenge_root / "admin-broken.html").write_bytes(broken_raw)
        chunks = source_chunks(broken)
        chunk_items = []
        for number, chunk in enumerate(chunks, 1):
            filename = f"chunk-{number:03d}.txt"
            (source_root / filename).write_text(chunk, encoding="utf-8", newline="\n")
            chunk_items.append({"number": number, "file": filename, "sha256": sha256_bytes(chunk.encode("utf-8"))})
        (source_root / "index.json").write_text(
            json.dumps({"schema": 1, "challenge_id": identifier, "chunks": chunk_items}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest = build_public_manifest(case, identifier, round_id, source_hash, sha256_bytes(broken_raw), len(chunks))
        (challenge_root / "challenge.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        public_entries.append({"challenge_id": identifier, "title": case.title, "manifest": f"challenges/{identifier}/challenge.json"})
        sample = sample_payload(case, identifier)
        internal_entries.append(
            {
                "challenge_id": identifier,
                "case_key": case.key,
                "holdout": case.holdout,
                "sample_payload": sample,
                "sample_payload_sha256": sha256_bytes(canonical_json(sample).encode("utf-8")),
            }
        )
    public_index = {
        "schema": 1,
        "round_id": round_id,
        "source_sha256": source_hash,
        "challenge_count": len(public_entries),
        "challenges": public_entries,
    }
    internal_index = {
        "schema": 1,
        "round_id": round_id,
        "source_sha256": source_hash,
        "challenges": internal_entries,
    }
    (public_root / "index.json").write_text(json.dumps(public_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (internal_root / "index.json").write_text(json.dumps(internal_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"status": "PASS", "round_id": round_id, "source_sha256": source_hash, "challenge_count": len(public_entries), "output": str(output)}


def sample_payload(case: RepairCase, identifier: str) -> dict[str, Any]:
    return {
        "request_id": f"{identifier}-attempt"[:64],
        "title": case.title,
        "summary": f"Restore the observed Repair-Lab behavior for {identifier}.",
        "version_slug": f"repair-{identifier.split('-', 1)[1]}"[:63],
        "touched_areas": ["Admin-Web UI"],
        "required_tests": [exact_test_command(identifier), CRITICAL_TEST, UI_TEST],
        "patch_content": case.sample_content,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        raise RepairLabError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RepairLabError(f"JSON object required: {path}")
    return value


def find_internal_entry(internal_manifest: Path, identifier: str) -> dict[str, Any]:
    data = load_json(internal_manifest)
    for entry in data.get("challenges", []):
        if isinstance(entry, dict) and entry.get("challenge_id") == identifier:
            return entry
    raise RepairLabError(f"unknown challenge_id: {identifier}")


def case_by_key(key: str) -> RepairCase:
    for case in CASES:
        if case.key == key:
            return case
    raise RepairLabError(f"unknown internal case key: {key}")


def inject_patch(html: str, payload: dict[str, Any], identifier: str) -> str:
    patch_id = f"kgg-lab-{identifier.removeprefix('repair-')}"
    content = payload["patch_content"].replace("__KGG_PATCH_ID__", patch_id)
    rendered = module_patch.render_patch_module(patch_id, payload["title"], content).decode("utf-8")
    marker = "</body>"
    if html.count(marker) != 1:
        raise RepairLabError("broken HTML must contain exactly one </body> marker")
    return html.replace(marker, rendered + marker)


def run_browser(html_path: Path, case_key: str, screenshot: Path | None = None) -> dict[str, Any]:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or shutil.which("npm")
    if npm:
        command = [npm, "exec", "--yes", "--package=playwright@1.61.1", "--", "node", str(SMOKE_SCRIPT)]
    else:
        command = ["node", str(SMOKE_SCRIPT)]
    command.extend(["--html", str(html_path), "--case", case_key])
    if screenshot:
        command.extend(["--screenshot", str(screenshot)])
    proc = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, env=os.environ.copy())
    output = (proc.stdout + "\n" + proc.stderr).strip()
    result: dict[str, Any] = {"returncode": proc.returncode, "output": output[-5000:]}
    for line in reversed((proc.stdout + "\n" + proc.stderr).splitlines()):
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            result["probe"] = parsed
            break
    return result


def evaluate_attempt(
    challenge_dir: Path,
    internal_manifest: Path,
    identifier: str,
    payload_file: Path,
    artifacts_dir: Path,
) -> dict[str, Any]:
    entry = find_internal_entry(internal_manifest, identifier)
    case = case_by_key(str(entry["case_key"]))
    public_manifest = load_json(challenge_dir / "challenge.json")
    if public_manifest.get("challenge_id") != identifier:
        raise RepairLabError("challenge manifest id mismatch")
    broken_path = challenge_dir / "admin-broken.html"
    broken_raw = broken_path.read_bytes()
    expected_hash = public_manifest.get("source", {}).get("broken_sha256")
    if sha256_bytes(broken_raw) != expected_hash:
        raise RepairLabError("broken challenge hash mismatch")
    payload_raw = payload_file.read_text(encoding="utf-8-sig")
    payload = write_gate.validate_payload(payload_raw)
    required = {exact_test_command(identifier), CRITICAL_TEST, UI_TEST}
    missing = sorted(required.difference(payload["required_tests"]))
    if missing:
        raise RepairLabError(f"payload missing exact required_tests: {missing}")
    repaired = inject_patch(broken_raw.decode("utf-8"), payload, identifier)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    repaired_path = artifacts_dir / "admin-repaired.html"
    repaired_path.write_text(repaired, encoding="utf-8", newline="\n")
    probe = run_browser(repaired_path, case.key, artifacts_dir / "repaired.png")
    report = {
        "status": "PASS" if probe["returncode"] == 0 else "FAIL",
        "challenge_id": identifier,
        "case_fingerprint": hashlib.sha256(case.key.encode("utf-8")).hexdigest()[:12],
        "payload_sha256": sha256_bytes(canonical_json(payload).encode("utf-8")),
        "repaired_sha256": sha256_bytes(repaired.encode("utf-8")),
        "probe": probe,
    }
    (artifacts_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if probe["returncode"] != 0:
        raise RepairLabError(probe["output"] or "browser repair probe failed")
    return report


def tracked_hashes() -> dict[str, str]:
    proc = subprocess.run(["git", "ls-files"], cwd=str(ROOT), text=True, capture_output=True, check=True)
    result = {}
    for name in proc.stdout.splitlines():
        path = ROOT / name
        if path.is_file():
            result[name] = sha256_bytes(path.read_bytes())
    return result


def self_test(browser: bool) -> dict[str, Any]:
    before = tracked_hashes()
    ensure_modular_source()
    source = SOURCE_HTML.read_text(encoding="utf-8")
    source_hash = sha256_bytes(source.encode("utf-8"))
    checks = []
    with tempfile.TemporaryDirectory(prefix="kgg-repair-self-") as temp_name:
        temp = Path(temp_name)
        generated = generate_round(temp, "self-test-a", include_holdouts=True)
        if generated["challenge_count"] != len(CASES):
            raise RepairLabError("self-test challenge count mismatch")
        for case in CASES:
            identifier = challenge_id("self-test-a", source_hash, case.key)
            challenge_root = temp / "public" / "challenges" / identifier
            broken = (challenge_root / "admin-broken.html").read_text(encoding="utf-8")
            if broken == source:
                raise RepairLabError(f"broken challenge equals golden source: {case.key}")
            validated = write_gate.validate_payload(json.dumps(sample_payload(case, identifier), ensure_ascii=False))
            repaired = inject_patch(broken, validated, identifier)
            if "__KGG_PATCH_ID__" in repaired:
                raise RepairLabError(f"unresolved patch placeholder: {case.key}")
            check = {"case": case.key, "mutation": "PASS", "sample_payload": "PASS"}
            if browser:
                golden_path = temp / f"golden-{case.key}.html"
                broken_path = challenge_root / "admin-broken.html"
                repaired_path = temp / f"repaired-{case.key}.html"
                golden_path.write_text(source, encoding="utf-8", newline="\n")
                repaired_path.write_text(repaired, encoding="utf-8", newline="\n")
                golden_probe = run_browser(golden_path, case.key)
                broken_probe = run_browser(broken_path, case.key)
                repaired_probe = run_browser(repaired_path, case.key)
                if golden_probe["returncode"] != 0:
                    raise RepairLabError(f"golden probe failed for {case.key}: {golden_probe['output']}")
                if broken_probe["returncode"] == 0:
                    raise RepairLabError(f"broken probe unexpectedly passed for {case.key}")
                if repaired_probe["returncode"] != 0:
                    raise RepairLabError(f"sample repair failed for {case.key}: {repaired_probe['output']}")
                check["golden_browser"] = "PASS"
                check["broken_browser"] = "EXPECTED_FAIL"
                check["sample_browser"] = "PASS"
            checks.append(check)
    after = tracked_hashes()
    if before != after:
        raise RepairLabError("Repair-Lab self-test modified tracked repository files")
    return {"status": "PASS", "test": "kgg_gpt_repair_lab", "browser": browser, "cases": checks}


def control_round(output: Path, round_id: str, include_holdouts: bool) -> dict[str, Any]:
    generated = generate_round(output, round_id, include_holdouts)
    internal = output / "internal" / "index.json"
    reports = []
    for entry in load_json(internal).get("challenges", []):
        identifier = str(entry["challenge_id"])
        case = case_by_key(str(entry["case_key"]))
        challenge_root = output / "public" / "challenges" / identifier
        golden_result = run_browser(SOURCE_HTML, case.key, output / "artifacts" / identifier / "golden.png")
        broken_result = run_browser(challenge_root / "admin-broken.html", case.key, output / "artifacts" / identifier / "broken.png")
        if golden_result["returncode"] != 0:
            raise RepairLabError(f"golden control failed for {identifier}: {golden_result['output']}")
        if broken_result["returncode"] == 0:
            raise RepairLabError(f"broken control unexpectedly passed for {identifier}")
        payload_path = output / "internal" / f"{identifier}-sample.json"
        payload_path.write_text(json.dumps(entry["sample_payload"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        repaired_report = evaluate_attempt(
            challenge_root,
            internal,
            identifier,
            payload_path,
            output / "artifacts" / identifier,
        )
        reports.append({"challenge_id": identifier, "golden": "PASS", "broken": "EXPECTED_FAIL", "sample_repair": repaired_report["status"]})
    result = {**generated, "status": "PASS", "controls": reports}
    (output / "control-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--evaluate", action="store_true")
    mode.add_argument("--control-round", action="store_true")
    parser.add_argument("--browser", action="store_true", help="Include Chromium controls in --self-test.")
    parser.add_argument("--round-id", default="repair-round")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-holdouts", action="store_true")
    parser.add_argument("--challenge-id")
    parser.add_argument("--challenge-dir", type=Path)
    parser.add_argument("--internal-manifest", type=Path)
    parser.add_argument("--payload-file", type=Path)
    parser.add_argument("--artifacts-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.self_test:
            result = self_test(args.browser)
        elif args.generate:
            if not args.output:
                raise RepairLabError("--output is required with --generate")
            result = generate_round(args.output.resolve(), args.round_id, args.include_holdouts)
        elif args.control_round:
            if not args.output:
                raise RepairLabError("--output is required with --control-round")
            result = control_round(args.output.resolve(), args.round_id, args.include_holdouts)
        else:
            required = [args.challenge_id, args.challenge_dir, args.internal_manifest, args.payload_file, args.artifacts_dir]
            if any(value is None for value in required):
                raise RepairLabError("--evaluate requires --challenge-id, --challenge-dir, --internal-manifest, --payload-file and --artifacts-dir")
            result = evaluate_attempt(
                args.challenge_dir.resolve(),
                args.internal_manifest.resolve(),
                str(args.challenge_id),
                args.payload_file.resolve(),
                args.artifacts_dir.resolve(),
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
