#!/usr/bin/env python3
"""Generate and evaluate blind natural-language KGG UI repair challenges."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))
import kgg_gpt_repair_lab as repair_lab  # noqa: E402
import kgg_gpt_write_gate as write_gate  # noqa: E402


SOURCE_HTML = ROOT / "kgg-update" / "index.html"
SMOKE_SCRIPT = ROOT / "release-pipeline" / "kgg_gpt_repair_lab_smoke.js"
CRITICAL_TEST = r"cmd /c release-pipeline\run-kgg-tests.cmd --level critical"
UI_TEST = r"cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression"
CHUNK_SIZE = 72_000


class NaturalUiLabError(RuntimeError):
    pass


@dataclass(frozen=True)
class NaturalCase:
    key: str
    smoke_case: str
    title: str
    prompts: tuple[str, ...]
    mutation: repair_lab.Mutation
    sample_content: str
    intent_groups: tuple[tuple[str, ...], ...]
    diagnosis_groups: tuple[tuple[str, ...], ...]
    clarification_count: int = 0
    clarification_reply: str = ""
    input_mode: str = "combined"


def existing_case(key: str) -> repair_lab.RepairCase:
    return repair_lab.case_by_key(key)


def patch_script(body: str) -> str:
    return repair_lab.patch_script(body)


EDITOR_CASE = existing_case("tablet-editor-layout")
PHOTO_CASE = existing_case("phone-photo-menu")
ANCHOR_CASE = existing_case("phone-menu-anchor")
PANEL_CASE = existing_case("tablet-layout-panel")


NATURAL_CASES: tuple[NaturalCase, ...] = (
    NaturalCase(
        key="noisy-editor-layout",
        smoke_case=EDITOR_CASE.key,
        title="Natural tablet editor layout",
        prompts=(
            "wen ich bei ner uebung auf das zahnrad geh ist das fenster aufm tablet auf ein mal so schmal alles untereinander mach das bitte wider richtig aber nciht handy aendern",
            "im grossen editor stimmt das bild nimmer die felder quetschen sich links runter und rechts ist platz, nur tablet bitte test version",
            "das edit ding aufm tab ist kaput 1 spalte statt 2 und speichern soll unten sichtbar bleiben",
        ),
        mutation=EDITOR_CASE.mutation,
        sample_content=EDITOR_CASE.sample_content,
        intent_groups=(
            ("tablet", "tab ", "grossen editor"),
            ("editor", "zahnrad", "edit ding", "editorfenster"),
            ("spalte", "einspalt", "zweispalt", "untereinander", "schmal", "breit"),
        ),
        diagnosis_groups=(("editormodal", "editorsheet", "editor"), ("grid", "spalte", "layout")),
        input_mode="combined",
    ),
    NaturalCase(
        key="duplicate-admin-control",
        smoke_case="phone-admin-duplicate",
        title="Natural duplicate phone admin control",
        prompts=(
            "aufm handy ist oben rechts das drei punkte ding doppelt siehe gelb 1 soll weg aber das richtige muss noch auf gehen",
            "da sind zwei admin menues uebereinander eins ist wohl alt räum nur das artefakt weg und lass das echte funktionieren",
            "warum hab ich da 2 mal die drei punkte? das zweite alte ding weg ohne die knoepfe im richtigen menu zu killen",
        ),
        mutation=repair_lab.Mutation(
            "    document.body.appendChild(root);",
            (
                "    document.body.appendChild(root);\n"
                "    var duplicate=root.cloneNode(true);\n"
                "    duplicate.id=\"kggPhoneAdminMenuLegacy\";\n"
                "    duplicate.classList.add(\"kggNaturalDuplicate\");\n"
                "    duplicate.querySelectorAll(\"[id]\").forEach(function(node){node.id=node.id+\"Legacy\";});\n"
                "    var duplicateHeader=document.querySelector(\"#createPanel .planHeader\");\n"
                "    if(duplicateHeader)duplicateHeader.appendChild(duplicate);"
            ),
        ),
        sample_content=patch_script(
            """  function repair(){
    document.querySelectorAll(".kggNaturalDuplicate,#kggPhoneAdminMenuLegacy").forEach(node=>node.remove());
  }
  repair();new MutationObserver(repair).observe(document.documentElement,{childList:true,subtree:true});"""
        ),
        intent_groups=(
            ("doppelt", "zwei", "2 mal", "beide", "uebereinander", "überlag"),
            ("drei punkte", "admin men", "menueknopf", "menuknopf"),
            ("weg", "entfern", "artefakt", "nur das echte", "nicht erneut"),
        ),
        diagnosis_groups=(
            ("duplicate", "doppelt", "legacy", "alt", "klon"),
            ("kggphoneadminmenu", "admin men", "phone men"),
        ),
        input_mode="screenshot",
    ),
    NaturalCase(
        key="wrong-phone-menu-anchor",
        smoke_case="phone-menu-visual-position",
        title="Natural phone menu anchor",
        prompts=(
            "das 3 punkte menu schwimmt wider irgendwo oben und gehört in den plan kopf bei 1 mach nur die position",
            "auf handy sitzt das admin ding im falschen layer rechts aussen, es soll bei übungen im plan im kopf bleiben",
            "menü geht zwar auf aber steht komisch ausserhalb vom plan siehe kreis bitte da rein setzen",
        ),
        mutation=repair_lab.Mutation(
            (
                "    body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenu{\n"
                "      position:absolute!important;\n"
                "      top:4px!important;\n"
                "      right:0!important;"
            ),
            (
                "    body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenu{\n"
                "      position:absolute!important;\n"
                "      top:4px!important;\n"
                "      right:-180px!important;"
            ),
        ),
        sample_content=(
            '<style id="__KGG_PATCH_ID__-style">\n'
            '@media(max-width:759px){body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenu{right:0!important;}}\n'
            '</style>\n'
            + patch_script("  // Scoped CSS restores the phone menu visual anchor.")
        ),
        intent_groups=(
            ("handy", "phone", "mobil"),
            ("menü", "menu", "menue", "3 punkte", "admin ding"),
            (
                "plan kopf",
                "im kopf",
                "innerhalb des kopfs",
                "kopfbereich",
                "plan-header",
                "planheader",
                "da rein",
                "innerhalb",
                "im plan",
            ),
        ),
        diagnosis_groups=(
            ("anchor", "veranker", "layer", "position", "ausserhalb"),
            ("planheader", "plan kopf", "header", "kopfbereich"),
        ),
        input_mode="combined",
    ),
    NaturalCase(
        key="mixed-scale-and-column",
        smoke_case="tablet-scale-boundary",
        title="Natural scale and column boundary",
        prompts=(
            "bei dem regler in der mitte macht plus zwar alles grösser aber verschiebt dabei auch die spalten das darf nciht, ziehen ist breite plus minus nur größe",
            "1 plus minus = skalieren 2 links rechts ziehen = datenbank gegen plan breite, im moment mischt er beides",
            "wenn ich + drücke wandert die trennlinie mit. die soll stehen bleiben und nur der inhalt soll größer werden, drag weiter nur spalten",
        ),
        mutation=repair_lab.Mutation(
            "    if(splitPlus)splitPlus.onclick=ev=>{ev.preventDefault();ev.stopPropagation();adjustTabletSplitLayoutScale(1);};",
            (
                "    if(splitPlus)splitPlus.onclick=ev=>{ev.preventDefault();ev.stopPropagation();"
                "tabletLayoutState.leftCol='640px';"
                "document.documentElement.style.setProperty('--kgg-tablet-left-col',tabletLayoutState.leftCol);"
                "adjustTabletSplitLayoutScale(1);};"
            ),
        ),
        sample_content=patch_script(
            """  const plus=document.getElementById("tabletSplitScalePlus");
  if(plus)plus.onclick=function(ev){
    ev.preventDefault();ev.stopPropagation();
    const current=Math.max(.01,Math.min(2,Number(localStorage.getItem("kgg_tablet_ui_scale"))||1));
    const next=Math.max(.01,Math.min(2,current+.05));
    localStorage.setItem("kgg_tablet_ui_scale",String(next));
    document.documentElement.style.setProperty("--kgg-tablet-ui-scale",String(next));
    const label="Groesse "+Math.round(next*100)+"%";
    ["tabletScaleValue","tabletSplitScaleValue"].forEach(id=>{const node=document.getElementById(id);if(node)node.textContent=label;});
  };"""
        ),
        intent_groups=(
            ("plus", "+", "minus", "tasten"),
            ("skalier", "größer", "grösser", "groesse", "inhalt"),
            ("spalte", "trennlinie", "breite", "verhaeltnis", "verschieb"),
        ),
        diagnosis_groups=(("--kgg-tablet-ui-scale", "ui scale", "skalier"), ("--kgg-tablet-left-col", "left col", "spaltenbreite")),
        input_mode="combined",
    ),
    NaturalCase(
        key="blocked-layout-panel",
        smoke_case=PANEL_CASE.key,
        title="Natural blocked tablet layout panel",
        prompts=(
            "ich drück layout anpassen links es wird blau aber darunter kommt nix mehr siehe markierung",
            "der menü punkt layout tut so als wäre er an aber die plus minus box bleibt weg",
            "auf tablet öffnet layout anpassen das bedienfeld nicht mehr der button ist aktiv aber panel unsichtbar",
        ),
        mutation=PANEL_CASE.mutation,
        sample_content=PANEL_CASE.sample_content,
        intent_groups=(
            ("layout anpassen", "layout"),
            ("panel", "box", "bedienfeld", "darunter", "plus minus"),
            (
                "unsichtbar",
                "bleibt weg",
                "kommt nix",
                "nicht sichtbar",
                "erscheint nicht",
                "verborg",
                "hidden",
            ),
        ),
        diagnosis_groups=(("tabletmenulayoutpanel", "layout panel", "bedienfeld"), ("hidden", "sichtbar", "aria-expanded")),
        input_mode="combined",
    ),
    NaturalCase(
        key="ambiguous-history-button",
        smoke_case="phone-recent-drawer",
        title="Natural ambiguous history menu",
        prompts=(
            "eins von den zwei markierten dingern links geht nicht mehr auf mach das wider",
            "bei 1 oder 2 im menü reagiert das falsche nicht mehr ich weiss grad nicht wie das heisst",
            "das eine mit den gespeicherten sachen öffnet nix mehr siehe beide kreise",
        ),
        mutation=repair_lab.Mutation(
            (
                '    bindDrawerButton("recentToggle","recent");\n'
                '    bindDrawerButton("packageToggle","package");'
            ),
            (
                '    void "natural-ui-recent-binding-disabled";\n'
                '    void "natural-ui-package-binding-disabled";'
            ),
        ),
        sample_content=patch_script(
            """  const button=document.getElementById("recentToggle");
  if(button)button.addEventListener("click",function(ev){
    const api=window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045;
    if(!api||typeof api.openDrawer!=="function")return;
    ev.preventDefault();ev.stopImmediatePropagation();api.openDrawer("recent");
  },true);"""
        ),
        intent_groups=(
            ("letzte pläne", "alten plänen", "obere", "plan historie", "historie"),
            ("öff", "auf", "reagiert"),
            ("menü", "markiert", "ding"),
        ),
        diagnosis_groups=(("recenttoggle", "recent", "letzte pläne"), ("drawer", "open")),
        clarification_count=1,
        clarification_reply="das obere mit den alten plänen, nicht die übungs pakete",
        input_mode="screenshot",
    ),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def challenge_id(round_id: str, source_hash: str, case_key: str, variant: int) -> str:
    digest = hashlib.sha256(
        f"{round_id}\0{source_hash}\0{case_key}\0{variant}".encode("utf-8")
    ).hexdigest()[:16]
    return f"natural-{digest}"


def exact_test_command(identifier: str) -> str:
    return (
        "python release-pipeline/kgg_gpt_natural_ui_lab.py "
        f"--evaluate --challenge-id {identifier} --submission-file <submission.json>"
    )


def source_chunks(text: str) -> list[str]:
    return [text[index : index + CHUNK_SIZE] for index in range(0, len(text), CHUNK_SIZE)]


def mutate(source: str, case: NaturalCase) -> str:
    count = source.count(case.mutation.old)
    if count != case.mutation.expected:
        raise NaturalUiLabError(
            f"mutation anchor drift for {case.key}: expected {case.mutation.expected}, got {count}"
        )
    result = source.replace(
        case.mutation.old,
        case.mutation.new,
        case.mutation.replace_count,
    )
    if result == source:
        raise NaturalUiLabError(f"mutation did not change source for {case.key}")
    return result


def prompt_variant(case: NaturalCase, round_id: str, source_hash: str) -> tuple[int, str]:
    seed = int(
        hashlib.sha256(f"{round_id}\0{source_hash}\0{case.key}".encode("utf-8")).hexdigest()[:16],
        16,
    )
    rng = random.Random(seed)
    variant = rng.randrange(len(case.prompts))
    prompt = case.prompts[variant]
    prefixes = ("", "ok also ", "schau mal ", "wider das problem ")
    suffixes = ("", " mach erst test app", " bitte kleinster patch", " und sag nicht fertig ohne test")
    return variant, f"{rng.choice(prefixes)}{prompt}{rng.choice(suffixes)}".strip()


def required_tests(identifier: str) -> list[str]:
    return [exact_test_command(identifier), CRITICAL_TEST, UI_TEST]


def sample_payload(case: NaturalCase, identifier: str) -> dict[str, Any]:
    return {
        "request_id": f"{identifier}-attempt"[:64],
        "title": case.title,
        "summary": f"Restore the natural UI challenge behavior for {identifier}.",
        "version_slug": f"natural-{identifier.split('-', 1)[1]}"[:63],
        "touched_areas": ["Admin-Web UI"],
        "required_tests": required_tests(identifier),
        "patch_content": case.sample_content,
    }


def sample_submission(case: NaturalCase, identifier: str) -> dict[str, Any]:
    intent = " ".join(group[0] for group in case.intent_groups)
    diagnosis = " ".join(group[0] for group in case.diagnosis_groups)
    return {
        "challenge_id": identifier,
        "interpretation": {
            "observed_behavior": intent,
            "desired_behavior": intent,
            "target_elements": [diagnosis],
            "interaction_boundary": diagnosis,
            "confidence": "medium" if case.clarification_count else "high",
            "clarification_count": case.clarification_count,
            "clarification_question": (
                "Welches der beiden markierten Menues meinst du genau?"
                if case.clarification_count
                else ""
            ),
        },
        "payload": sample_payload(case, identifier),
    }


def capture_visual(html_path: Path, case: NaturalCase, screenshot: Path) -> dict[str, Any]:
    node = repair_lab.shutil.which("node")
    if not node:
        raise NaturalUiLabError("node runtime is required for visual capture")
    command = [node, str(SMOKE_SCRIPT)]
    command.extend(
        [
            "--html",
            str(html_path),
            "--case",
            case.smoke_case,
            "--capture-only",
            "--screenshot",
            str(screenshot),
        ]
    )
    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise NaturalUiLabError(
            f"visual capture timed out for {case.key} after 120 seconds"
        ) from exc
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode != 0 or not screenshot.exists():
        raise NaturalUiLabError(f"visual capture failed for {case.key}: {output[-3000:]}")
    return {"sha256": sha256_bytes(screenshot.read_bytes()), "output": output[-1000:]}


def build_public_manifest(
    case: NaturalCase,
    identifier: str,
    round_id: str,
    source_hash: str,
    broken_hash: str,
    chunk_count: int,
    prompt: str,
    screenshot_hash: str,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "challenge_id": identifier,
        "round_id": round_id,
        "natural_request": prompt,
        "input_mode": case.input_mode,
        "screenshot": {
            "path": "marked-problem.png",
            "sha256": screenshot_hash,
            "attachment_required": case.input_mode in {"screenshot", "combined"},
        },
        "viewport": {
            "width": 390 if case.smoke_case.startswith("phone-") else 1180,
            "height": 844 if case.smoke_case.startswith("phone-") else 820,
        },
        "source": {
            "full_html": "admin-broken.html",
            "chunks_index": "source/index.json",
            "chunk_count": chunk_count,
            "source_sha256": source_hash,
            "broken_sha256": broken_hash,
        },
        "submission_contract": {
            "fields": ["challenge_id", "interpretation", "payload"],
            "interpretation_fields": [
                "observed_behavior",
                "desired_behavior",
                "target_elements",
                "interaction_boundary",
                "confidence",
                "clarification_count",
                "clarification_question",
            ],
            "interpretation_types": {
                "observed_behavior": "string",
                "desired_behavior": "string",
                "target_elements": "non-empty string array",
                "interaction_boundary": "string",
                "confidence": "one of: low, medium, high",
                "clarification_count": "integer 0 or 1",
                "clarification_question": "string; empty when count is 0",
            },
            "payload_schema": "KGG modular payload v2",
            "payload_fields": [
                "request_id",
                "title",
                "summary",
                "version_slug",
                "touched_areas",
                "required_tests",
                "patch_content",
            ],
            "forbidden_payload_fields": [
                "operations",
                "path",
                "file",
                "old_text",
                "new_text",
            ],
            "patch_placeholder": "__KGG_PATCH_ID__",
            "patch_content_format": (
                "Complete executable HTML fragment. Wrap CSS in <style> and "
                "JavaScript in <script>; bare CSS or JavaScript is invalid."
            ),
            "ambiguity_policy": (
                "If one of multiple marked controls is requested and at least two "
                "matching source defects remain possible, ask exactly one target "
                "question before dispatch. Never repair both."
            ),
            "required_tests": required_tests(identifier),
        },
        "submission": (
            "Send one interpretation plus modular payload metadata through submission_json "
            "and raw patch_content through its dedicated evaluate_natural_attempt input. "
            "Omit payload.patch_content from submission_json and never double-escape patch code. "
            "For layout repairs, inspect the final cascade and patch the same container whose "
            "computed display, columns or geometry is wrong; do not guess child containers. "
            "Do not request or infer hidden intent, assertions or clean source."
        ),
    }


def generate_round(
    output: Path,
    round_id: str,
    *,
    screenshots: bool,
) -> dict[str, Any]:
    repair_lab.ensure_modular_source()
    source_raw = SOURCE_HTML.read_bytes()
    source = source_raw.decode("utf-8")
    source_hash = sha256_bytes(source_raw)
    public_root = output / "public"
    internal_root = output / "internal"
    public_root.mkdir(parents=True, exist_ok=True)
    internal_root.mkdir(parents=True, exist_ok=True)
    public_entries: list[dict[str, Any]] = []
    internal_entries: list[dict[str, Any]] = []
    for case in NATURAL_CASES:
        variant, prompt = prompt_variant(case, round_id, source_hash)
        identifier = challenge_id(round_id, source_hash, case.key, variant)
        broken = mutate(source, case)
        broken_raw = broken.encode("utf-8")
        challenge_root = public_root / "challenges" / identifier
        source_root = challenge_root / "source"
        source_root.mkdir(parents=True, exist_ok=True)
        broken_path = challenge_root / "admin-broken.html"
        broken_path.write_bytes(broken_raw)
        chunks = source_chunks(broken)
        chunk_items = []
        for number, chunk in enumerate(chunks, 1):
            filename = f"chunk-{number:03d}.txt"
            (source_root / filename).write_text(chunk, encoding="utf-8", newline="\n")
            chunk_items.append(
                {
                    "number": number,
                    "file": filename,
                    "sha256": sha256_bytes(chunk.encode("utf-8")),
                }
            )
        (source_root / "index.json").write_text(
            json.dumps(
                {"schema": 1, "challenge_id": identifier, "chunks": chunk_items},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        screenshot_hash = ""
        if screenshots:
            screenshot_path = challenge_root / "marked-problem.png"
            capture = capture_visual(broken_path, case, screenshot_path)
            screenshot_hash = capture["sha256"]
        public_manifest = build_public_manifest(
            case,
            identifier,
            round_id,
            source_hash,
            sha256_bytes(broken_raw),
            len(chunks),
            prompt,
            screenshot_hash,
        )
        (challenge_root / "challenge.json").write_text(
            json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        public_entries.append(
            {
                "challenge_id": identifier,
                "manifest": f"challenges/{identifier}/challenge.json",
                "input_mode": case.input_mode,
            }
        )
        submission = sample_submission(case, identifier)
        internal_entries.append(
            {
                "challenge_id": identifier,
                "case_key": case.key,
                "variant": variant,
                "canonical_intent_groups": case.intent_groups,
                "canonical_diagnosis_groups": case.diagnosis_groups,
                "required_clarification_count": case.clarification_count,
                "clarification_reply": case.clarification_reply,
                "sample_submission": submission,
                "sample_submission_sha256": sha256_bytes(
                    canonical_json(submission).encode("utf-8")
                ),
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
    (public_root / "index.json").write_text(
        json.dumps(public_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (internal_root / "index.json").write_text(
        json.dumps(internal_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "status": "PASS",
        "round_id": round_id,
        "source_sha256": source_hash,
        "challenge_count": len(public_entries),
        "screenshots": screenshots,
        "output": str(output),
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        raise NaturalUiLabError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise NaturalUiLabError(f"JSON object required: {path}")
    return value


def find_internal_entry(internal_manifest: Path, identifier: str) -> dict[str, Any]:
    data = load_json(internal_manifest)
    for entry in data.get("challenges", []):
        if isinstance(entry, dict) and entry.get("challenge_id") == identifier:
            return entry
    raise NaturalUiLabError(f"unknown challenge_id: {identifier}")


def case_by_key(key: str) -> NaturalCase:
    for case in NATURAL_CASES:
        if case.key == key:
            return case
    raise NaturalUiLabError(f"unknown internal case key: {key}")


def validate_interpretation(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NaturalUiLabError("interpretation must be an object")
    required = {
        "observed_behavior",
        "desired_behavior",
        "target_elements",
        "interaction_boundary",
        "confidence",
        "clarification_count",
        "clarification_question",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise NaturalUiLabError(f"interpretation missing fields: {missing}")
    if not isinstance(value["target_elements"], list) or not value["target_elements"]:
        raise NaturalUiLabError("interpretation target_elements must be a non-empty list")
    if value["confidence"] not in {"low", "medium", "high"}:
        raise NaturalUiLabError("interpretation confidence must be low, medium or high")
    if value["clarification_count"] not in {0, 1}:
        raise NaturalUiLabError("interpretation clarification_count must be 0 or 1")
    for key in [
        "observed_behavior",
        "desired_behavior",
        "interaction_boundary",
        "clarification_question",
    ]:
        if not isinstance(value[key], str):
            raise NaturalUiLabError(f"interpretation {key} must be a string")
    return value


def normalize_semantic_text(value: str) -> str:
    expanded = (
        value.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    decomposed = unicodedata.normalize("NFKD", expanded)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def semantic_marker_matches(normalized: str, tokens: list[str], marker: str) -> bool:
    wanted = normalize_semantic_text(marker)
    if wanted in normalized:
        return True
    if " " in wanted or len(wanted) < 5:
        return False
    root = wanted
    for suffix in ("ern", "en", "er", "es", "em", "e", "n", "s"):
        if len(root) - len(suffix) >= 5 and root.endswith(suffix):
            root = root[: -len(suffix)]
            break
    return len(root) >= 5 and any(root in token for token in tokens)


def semantic_score(text: str, groups: list[list[str]] | tuple[tuple[str, ...], ...]) -> dict[str, Any]:
    normalized = normalize_semantic_text(text)
    tokens = normalized.split()
    matches = []
    for group in groups:
        hit = next(
            (
                marker
                for marker in group
                if semantic_marker_matches(normalized, tokens, marker)
            ),
            "",
        )
        matches.append({"matched": bool(hit), "marker": hit})
    passed = sum(1 for item in matches if item["matched"])
    total = len(matches)
    return {
        "percent": round((passed / total) * 100) if total else 100,
        "passed": passed,
        "total": total,
        "matches": matches,
    }


def submission_text(interpretation: dict[str, Any]) -> str:
    return " ".join(
        [
            interpretation["observed_behavior"],
            interpretation["desired_behavior"],
            " ".join(str(item) for item in interpretation["target_elements"]),
            interpretation["interaction_boundary"],
            interpretation["clarification_question"],
        ]
    )


def validate_patch_fragment(patch_content: str) -> None:
    if not re.search(r"<(?:style|script)\b", patch_content, re.IGNORECASE):
        raise NaturalUiLabError(
            "patch_content must be an executable HTML fragment wrapped in <style> or <script>"
        )


def classify_evaluation_error(message: str) -> str:
    lowered = message.lower()
    if any(
        marker in lowered
        for marker in [
            "interpretation missing fields",
            "interpretation target_elements",
            "interpretation confidence must",
            "interpretation clarification_count must",
            "interpretation observed_behavior must",
            "interpretation desired_behavior must",
            "interpretation interaction_boundary must",
            "interpretation clarification_question must",
        ]
    ):
        return "payload_schema"
    if "interpretation" in lowered or "clarification" in lowered:
        return "natural_language"
    if any(
        marker in lowered
        for marker in [
            "forbidden generated-output token",
            "payload missing exact required_tests",
            "payload json",
            "patch_content",
        ]
    ):
        return "payload_schema"
    if any(marker in lowered for marker in ["browser repair probe failed", '"status":"fail"', "pageerror"]):
        return "ui_logic"
    if any(marker in lowered for marker in ["playwright", "chromium", "missing tool", "npm"]):
        return "ci_tooling"
    if any(marker in lowered for marker in ["challenge manifest", "broken challenge hash", "unknown challenge_id"]):
        return "challenge_integrity"
    return "evaluator_failure"


def write_evaluation_outcome(
    artifacts_dir: Path,
    identifier: str,
    submission_file: Path,
    status: str,
    *,
    error: str = "",
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    request_id = "unknown-request"
    try:
        request_id = str(load_json(submission_file).get("payload", {}).get("request_id") or request_id)
    except Exception:  # noqa: BLE001
        pass
    feedback = error.strip().replace(str(ROOT), "<repo>")
    if len(feedback) > 1600:
        feedback = feedback[-1600:]
    outcome: dict[str, Any] = {
        "schema": 1,
        "status": status,
        "round_id": os.environ.get("KGG_NATURAL_UI_ROUND_ID", ""),
        "challenge_id": identifier,
        "request_id": request_id,
        "run_id": int(os.environ["GITHUB_RUN_ID"])
        if os.environ.get("GITHUB_RUN_ID", "").isdigit()
        else None,
        "error_class": None if status == "PASS" else classify_evaluation_error(feedback),
        "feedback": (
            "Natural-language, payload and browser UI checks passed."
            if status == "PASS"
            else feedback
        ),
    }
    if report:
        outcome["scores"] = report.get("scores")
        outcome["payload_sha256"] = report.get("payload_sha256")
    (artifacts_dir / "outcome.json").write_text(
        json.dumps(outcome, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return outcome


def evaluate_attempt(
    challenge_dir: Path,
    internal_manifest: Path,
    identifier: str,
    submission_file: Path,
    artifacts_dir: Path,
) -> dict[str, Any]:
    entry = find_internal_entry(internal_manifest, identifier)
    case = case_by_key(str(entry["case_key"]))
    public_manifest = load_json(challenge_dir / "challenge.json")
    if public_manifest.get("challenge_id") != identifier:
        raise NaturalUiLabError("challenge manifest id mismatch")
    broken_path = challenge_dir / "admin-broken.html"
    broken_raw = broken_path.read_bytes()
    if sha256_bytes(broken_raw) != public_manifest.get("source", {}).get("broken_sha256"):
        raise NaturalUiLabError("broken challenge hash mismatch")
    submission = load_json(submission_file)
    if submission.get("challenge_id") != identifier:
        raise NaturalUiLabError("submission challenge_id mismatch")
    interpretation = validate_interpretation(submission.get("interpretation"))
    payload_value = submission.get("payload")
    if not isinstance(payload_value, dict):
        raise NaturalUiLabError("submission payload must be an object")
    payload = write_gate.validate_payload(json.dumps(payload_value, ensure_ascii=False))
    validate_patch_fragment(payload["patch_content"])
    required = set(required_tests(identifier))
    missing = sorted(required.difference(payload["required_tests"]))
    if missing:
        raise NaturalUiLabError(f"payload missing exact required_tests: {missing}")
    combined = submission_text(interpretation)
    intent = semantic_score(combined, entry["canonical_intent_groups"])
    diagnosis = semantic_score(combined, entry["canonical_diagnosis_groups"])
    wanted_clarifications = int(entry["required_clarification_count"])
    clarification_pass = (
        interpretation["clarification_count"] == wanted_clarifications
        and (
            wanted_clarifications == 0
            or len(interpretation["clarification_question"].strip()) >= 12
        )
    )
    if intent["percent"] < 100:
        raise NaturalUiLabError(f"interpretation intent score below 100: {intent}")
    if diagnosis["percent"] < 100:
        raise NaturalUiLabError(f"interpretation diagnosis score below 100: {diagnosis}")
    if not clarification_pass:
        raise NaturalUiLabError(
            "interpretation clarification policy mismatch: "
            f"expected {wanted_clarifications}, got {interpretation['clarification_count']}"
        )
    repaired = repair_lab.inject_patch(
        broken_raw.decode("utf-8"),
        payload,
        identifier.replace("natural-", "repair-"),
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    repaired_path = artifacts_dir / "admin-repaired.html"
    repaired_path.write_text(repaired, encoding="utf-8", newline="\n")
    probe = repair_lab.run_browser(
        repaired_path,
        case.smoke_case,
        artifacts_dir / "repaired.png",
    )
    report = {
        "status": "PASS" if probe["returncode"] == 0 else "FAIL",
        "challenge_id": identifier,
        "scores": {
            "natural_language_intent": intent,
            "ui_diagnosis": diagnosis,
            "clarification_policy": {
                "status": "PASS" if clarification_pass else "FAIL",
                "expected": wanted_clarifications,
                "actual": interpretation["clarification_count"],
            },
            "patch_safety": {"status": "PASS"},
            "browser_behavior": {
                "status": "PASS" if probe["returncode"] == 0 else "FAIL"
            },
            "visible_result": {
                "status": "PASS"
                if probe.get("probe", {}).get("status") == "PASS"
                else "FAIL"
            },
        },
        "payload_sha256": sha256_bytes(canonical_json(payload).encode("utf-8")),
        "repaired_sha256": sha256_bytes(repaired.encode("utf-8")),
        "probe": probe,
    }
    (artifacts_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if probe["returncode"] != 0:
        raise NaturalUiLabError(probe["output"] or "browser repair probe failed")
    return report


def tracked_hashes() -> dict[str, str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    result = {}
    for name in proc.stdout.splitlines():
        path = ROOT / name
        if path.is_file():
            result[name] = sha256_bytes(path.read_bytes())
    return result


def assert_public_is_blind(public_root: Path, internal_root: Path) -> None:
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in public_root.rglob("*")
        if path.is_file() and path.suffix in {".json", ".txt"}
    )
    internal = load_json(internal_root / "index.json")
    forbidden_keys = [
        "canonical_intent_groups",
        "canonical_diagnosis_groups",
        "sample_submission",
        "clarification_reply",
    ]
    for key in forbidden_keys:
        if key in public_text:
            raise NaturalUiLabError(f"public challenge leaks private evaluator key: {key}")
    for entry in internal.get("challenges", []):
        sample = entry.get("sample_submission", {})
        patch_content = str(sample.get("payload", {}).get("patch_content", ""))
        if patch_content and patch_content in public_text:
            raise NaturalUiLabError("public challenge leaks sample repair content")


def self_test(browser: bool) -> dict[str, Any]:
    before = tracked_hashes()
    phone_anchor = case_by_key("wrong-phone-menu-anchor")
    inflected = semantic_score(
        "Auf dem Handy soll das Menu rechts innerhalb des Kopfs von Uebungen im Plan-Header verankert bleiben.",
        phone_anchor.intent_groups,
    )
    if inflected["percent"] != 100:
        raise NaturalUiLabError(
            "semantic aliases reject valid inflected phone-menu intent"
        )
    editor_case = case_by_key("noisy-editor-layout")
    compound = semantic_score(
        "Der Tablet-Editor braucht wieder ein zweispaltiges Raster.",
        editor_case.intent_groups,
    )
    if compound["percent"] != 100:
        raise NaturalUiLabError(
            "semantic stem matching rejects valid German compound wording"
        )
    duplicate_case = case_by_key("duplicate-admin-control")
    punctuation = semantic_score(
        "Im Phone-Viewport wird zusätzlich zum echten Admin-Menü ein geklonter "
        "Legacy-Menüknoten eingefügt; beide Menüs liegen übereinander. Nur das "
        "echte Menü bleibt sichtbar, der Klon wird entfernt und darf nicht erneut erscheinen.",
        duplicate_case.intent_groups,
    )
    if punctuation["percent"] != 100:
        raise NaturalUiLabError(
            "semantic normalization rejects valid umlaut and hyphen wording"
        )
    panel_case = case_by_key("blocked-layout-panel")
    hidden_panel = semantic_score(
        "Der Menüpunkt Layout ist aktiv, aber das zugehörige Panel mit der "
        "Plus/Minus-Steuerung bleibt verborgen.",
        panel_case.intent_groups,
    )
    if hidden_panel["percent"] != 100:
        raise NaturalUiLabError(
            "semantic aliases reject valid hidden layout-panel wording"
        )
    try:
        validate_patch_fragment(
            '(function(){document.body.dataset.kggPatch="__KGG_PATCH_ID__";})();'
        )
    except NaturalUiLabError:
        pass
    else:
        raise NaturalUiLabError("bare JavaScript patch_content must be rejected")
    with tempfile.TemporaryDirectory(prefix="kgg-natural-ui-self-") as temp_name:
        temp = Path(temp_name)
        generated = generate_round(
            temp,
            "natural-self-test-a",
            screenshots=browser,
        )
        if generated["challenge_count"] != 6:
            raise NaturalUiLabError("natural UI self-test challenge count mismatch")
        assert_public_is_blind(temp / "public", temp / "internal")
        internal = load_json(temp / "internal" / "index.json")
        checks = []
        for entry in internal["challenges"]:
            identifier = str(entry["challenge_id"])
            case = case_by_key(str(entry["case_key"]))
            challenge_root = temp / "public" / "challenges" / identifier
            submission_path = temp / "internal" / f"{identifier}-submission.json"
            submission_path.write_text(
                json.dumps(entry["sample_submission"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            payload = write_gate.validate_payload(
                json.dumps(entry["sample_submission"]["payload"], ensure_ascii=False)
            )
            repaired = repair_lab.inject_patch(
                (challenge_root / "admin-broken.html").read_text(encoding="utf-8"),
                payload,
                identifier.replace("natural-", "repair-"),
            )
            if "__KGG_PATCH_ID__" in repaired:
                raise NaturalUiLabError(f"unresolved patch placeholder: {case.key}")
            check: dict[str, Any] = {
                "case": case.key,
                "blind_manifest": "PASS",
                "sample_submission": "PASS",
            }
            if browser:
                screenshot = challenge_root / "marked-problem.png"
                if not screenshot.exists() or screenshot.stat().st_size < 1000:
                    raise NaturalUiLabError(f"missing marked screenshot: {case.key}")
                golden_probe = repair_lab.run_browser(SOURCE_HTML, case.smoke_case)
                broken_probe = repair_lab.run_browser(
                    challenge_root / "admin-broken.html",
                    case.smoke_case,
                )
                report = evaluate_attempt(
                    challenge_root,
                    temp / "internal" / "index.json",
                    identifier,
                    submission_path,
                    temp / "artifacts" / identifier,
                )
                if golden_probe["returncode"] != 0:
                    raise NaturalUiLabError(
                        f"golden probe failed for {case.key}: {golden_probe['output']}"
                    )
                if broken_probe["returncode"] == 0:
                    raise NaturalUiLabError(
                        f"broken probe unexpectedly passed for {case.key}"
                    )
                if report["status"] != "PASS":
                    raise NaturalUiLabError(f"sample repair failed for {case.key}")
                check.update(
                    {
                        "golden_browser": "PASS",
                        "broken_browser": "EXPECTED_FAIL",
                        "sample_browser": "PASS",
                        "marked_screenshot": "PASS",
                    }
                )
            checks.append(check)
        outcome_dir = temp / "outcome"
        first = internal["challenges"][0]
        submission_path = temp / "internal" / f"{first['challenge_id']}-submission.json"
        failed = write_evaluation_outcome(
            outcome_dir,
            str(first["challenge_id"]),
            submission_path,
            "FAIL",
            error="interpretation clarification policy mismatch",
        )
        if failed["error_class"] != "natural_language":
            raise NaturalUiLabError("natural outcome classification failed")
        invalid_shape = write_evaluation_outcome(
            outcome_dir / "invalid-shape",
            str(first["challenge_id"]),
            submission_path,
            "FAIL",
            error="interpretation confidence must be low, medium or high",
        )
        if invalid_shape["error_class"] != "payload_schema":
            raise NaturalUiLabError("interpretation shape must classify as payload_schema")
    after = tracked_hashes()
    if before != after:
        raise NaturalUiLabError("natural UI self-test modified tracked repository files")
    return {
        "status": "PASS",
        "test": "kgg_gpt_natural_ui_lab",
        "browser": browser,
        "cases": checks,
    }


def control_round(output: Path, round_id: str) -> dict[str, Any]:
    generated = generate_round(output, round_id, screenshots=True)
    internal_path = output / "internal" / "index.json"
    reports = []
    for entry in load_json(internal_path)["challenges"]:
        identifier = str(entry["challenge_id"])
        case = case_by_key(str(entry["case_key"]))
        challenge_root = output / "public" / "challenges" / identifier
        golden = repair_lab.run_browser(
            SOURCE_HTML,
            case.smoke_case,
            output / "artifacts" / identifier / "golden.png",
        )
        broken = repair_lab.run_browser(
            challenge_root / "admin-broken.html",
            case.smoke_case,
            output / "artifacts" / identifier / "broken.png",
        )
        if golden["returncode"] != 0:
            raise NaturalUiLabError(
                f"golden control failed for {identifier}: {golden['output']}"
            )
        if broken["returncode"] == 0:
            raise NaturalUiLabError(
                f"broken control unexpectedly passed for {identifier}"
            )
        submission_path = output / "internal" / f"{identifier}-submission.json"
        submission_path.write_text(
            json.dumps(entry["sample_submission"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        repaired = evaluate_attempt(
            challenge_root,
            internal_path,
            identifier,
            submission_path,
            output / "artifacts" / identifier,
        )
        reports.append(
            {
                "challenge_id": identifier,
                "golden": "PASS",
                "broken": "EXPECTED_FAIL",
                "sample_repair": repaired["status"],
                "scores": repaired["scores"],
            }
        )
    result = {**generated, "status": "PASS", "controls": reports}
    (output / "control-report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--evaluate", action="store_true")
    mode.add_argument("--control-round", action="store_true")
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--screenshots", action="store_true")
    parser.add_argument("--round-id", default="natural-ui-round")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--challenge-id")
    parser.add_argument("--challenge-dir", type=Path)
    parser.add_argument("--internal-manifest", type=Path)
    parser.add_argument("--submission-file", type=Path)
    parser.add_argument("--artifacts-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.self_test:
            result = self_test(args.browser)
        elif args.generate:
            if not args.output:
                raise NaturalUiLabError("--output is required with --generate")
            result = generate_round(
                args.output.resolve(),
                args.round_id,
                screenshots=args.screenshots,
            )
        elif args.control_round:
            if not args.output:
                raise NaturalUiLabError("--output is required with --control-round")
            result = control_round(args.output.resolve(), args.round_id)
        else:
            required = [
                args.challenge_id,
                args.challenge_dir,
                args.internal_manifest,
                args.submission_file,
                args.artifacts_dir,
            ]
            if any(value is None for value in required):
                raise NaturalUiLabError(
                    "--evaluate requires --challenge-id, --challenge-dir, "
                    "--internal-manifest, --submission-file and --artifacts-dir"
                )
            result = evaluate_attempt(
                args.challenge_dir.resolve(),
                args.internal_manifest.resolve(),
                str(args.challenge_id),
                args.submission_file.resolve(),
                args.artifacts_dir.resolve(),
            )
            write_evaluation_outcome(
                args.artifacts_dir.resolve(),
                str(args.challenge_id),
                args.submission_file.resolve(),
                "PASS",
                report=result,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        if (
            args.evaluate
            and args.artifacts_dir
            and args.challenge_id
            and args.submission_file
        ):
            try:
                write_evaluation_outcome(
                    args.artifacts_dir.resolve(),
                    str(args.challenge_id),
                    args.submission_file.resolve(),
                    "FAIL",
                    error=str(exc),
                )
            except Exception:  # noqa: BLE001
                pass
        print(
            json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
