#!/usr/bin/env python3
"""Local native-app evidence using the existing bridge, NOT plugin acceptance.

Serve worktree bytes on loopback, seed only synthetic browser storage, use the
existing native-app test setup, then observe -> real click -> observe. A fixture
DOM check verifies the actual numpad/editor, without adding fake state markers.
No installed host, tunnel, production data or app source is modified.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
from pathlib import Path
import queue
import struct
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kgg-plugin" / "mcp"))
from real_browser import BrowserBootstrap  # noqa: E402
import server as ui_lab  # noqa: E402

PATIENT_PLAN = {"i": "issue376-synthetic", "t": "KGG synthetischer Testplan", "v": 1, "d": 6,
                "e": [["Beinpresse", 2, "B", "kg", "Wdh", "40", "10"]]}
THERAPIST_STATE = {"plan": [{"id": "issue376-synthetic", "localId": "issue376-synthetic",
                            "name": "Beinpresse synthetisch", "sets": 2, "unit": "Wdh", "weightUnit": "kg"}],
                   "patient": {}, "packages": [], "bankOpen": False, "editId": None,
                   "sortMenuId": None, "reorderSuppressClick": False, "largePdfMode": False, "textSyncing": False}


def fixture_script(app: str) -> str:
    # Mirrors kgg_patient_compact_transfer_playwright / ticket_015_admin setup.
    seed = "localStorage.kggInstallAsked='1';" if app == "patient" else (
        "localStorage.setItem('kgg_html_app_v2_state'," + json.dumps(json.dumps(THERAPIST_STATE)) + ");"
        "localStorage.setItem('kgg_pwa_install_prompt_seen_v1',String(Date.now()));")
    return "<script>" + seed + """
    window.addEventListener('load',()=>{
      const app=APP,started=Date.now(); let sent=false;
      const visible=n=>!!n&&n.getBoundingClientRect().width>0&&n.getBoundingClientRect().height>0&&getComputedStyle(n).visibility!=='hidden';
      const report=value=>fetch('/__issue376_fixture',{method:'POST',body:JSON.stringify(value)});
      const timer=setInterval(()=>{
        if(Date.now()-started>15000){clearInterval(timer);report({error:'fixture_setup_timeout'});return;}
        if(app==='therapist'){
          const config=document.querySelector('#adminSecretsModal.open');
          if(config){document.getElementById('closeAdminSecrets')?.click();return;}
        }
        if(!sent){
          let target;
          if(app==='patient'){
            const card=document.querySelector('#list .ex');
            if(!card||Date.now()-started<1100)return;
            if(!card.classList.contains('kggOpen')){card.querySelector('h3')?.click();return;}
            const input=card.querySelector('input.num');
            target=[...card.querySelectorAll('.kggCompactTapProxy')].find(p=>p.__kggInput===input)||input;
          }else target=document.querySelector('#planList [data-planedit]');
          if(!visible(target))return;
          target.scrollIntoView({block:'center'});
          const r=target.getBoundingClientRect();
          if(r.left<0||r.top<0||r.right>innerWidth||r.bottom>innerHeight)return;
          sent=true;report({phase:'ready',x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
        }else{
          const target=app==='patient'?document.querySelector('#pad:not(.hide) .padBox'):document.querySelector('#editorModal.open .editorSheet');
          if(visible(target)){clearInterval(timer);report({phase:'after',state:app==='patient'?'patient-numpad':'therapist-editor'});}
        }
      },100);
    });
    </script>""".replace("APP", json.dumps(app))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "issue376" / "native-apps")
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to(ROOT)  # Deliberately worktree-only artifacts.
    output.mkdir(parents=True, exist_ok=True)
    events: queue.Queue = queue.Queue()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def log_message(self, *a):
            pass

        def do_GET(self):
            route = urlsplit(self.path).path
            app = {"/index.html": "patient", "/kgg-update/index.html": "therapist"}.get(route)
            if not app:
                return super().do_GET()
            source = (ROOT / route.lstrip("/")).read_text(encoding="utf-8")
            content = source.replace("<head>", "<head>" + fixture_script(app), 1).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            if self.path != "/__issue376_fixture" or int(self.headers.get("Content-Length", 0)) > 1024:
                self.send_error(400)
                return
            events.put(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(204)
            self.end_headers()

    bootstrap = BrowserBootstrap.from_environment()
    if not bootstrap.enabled:
        parser.error("Explicit local opt-in required: KGG_REAL_BROWSER=1")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    source_sha = subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {"source_sha": source_sha, "scope": "LOCAL_ONLY_NOT_CHATGPT_PLUGIN_PASS",
                "browser_mode": "real_playwright_chromium_headless", "fixture": "synthetic storage and native DOM setup; no state markers",
                "source_files": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ("index.html", "kgg-update/index.html")}, "cases": []}
    try:
        for app in ("patient", "therapist"):
            for width, height in ((390, 844), (820, 1180)):
                case = f"{app}-{width}x{height}"
                url = f"http://127.0.0.1:{httpd.server_port}/" + ("index.html" if app == "patient" else "kgg-update/index.html")
                if app == "patient":
                    plan = base64.urlsafe_b64encode(json.dumps(PATIENT_PLAN).encode()).decode().rstrip("=")
                    url += "?plan=" + quote("KGGH2:" + plan)
                runtime = ui_lab.Runtime(browser_bootstrap=bootstrap)
                sid = "issue376-" + case
                now = datetime.now(timezone.utc)
                runtime.start({
                    "schema": ui_lab.SESSION_SCHEMA, "session_id": sid, "status": "created", "active_actor": "codex", "request_id": sid + "-start",
                    "lease": {"owner": "codex", "issued_at": now.isoformat(), "expires_at": (now + timedelta(minutes=30)).isoformat()},
                    "runner": {"runner_id": "issue376-local", "version": ui_lab.SERVER_VERSION, "browser_revision": "host-default-chromium",
                               "capabilities": ["browser", "capture", "visual_loop"]},
                    "app": {"name": "patient" if app == "patient" else "admin", "url": url, "main_sha": source_sha, "preview_sha": None},
                    "device_profile": "custom", "viewport": {"width": width, "height": height, "device_scale_factor": 1},
                    "quick_flow": {"name": "screenshot-evidence", "version": "1.0.0"}, "timeout": {"timeout_ms": 15000, "cleanup_on_cancel": True}, "artifacts": [],
                })
                def request(operation):
                    return {"schema": ui_lab.REQUEST_SCHEMA, "session_id": sid, "request_id": sid + "-" + operation.replace("_", "-"),
                            "actor": "codex", "operation": operation, "main_sha": source_sha,
                            "payload_sha256": hashlib.sha256(case.encode()).hexdigest()}
                try:
                    # The first observe creates the page; fixture setup then settles it.
                    runtime.observe_visual(request("observe_visual_state"))
                    ready = events.get(timeout=20)
                    if ready.get("phase") != "ready":
                        raise RuntimeError(str(ready))
                    # Refresh the observation on the SAME page after synthetic setup.
                    before = runtime._record_visual_observation(runtime.sessions[sid], runtime.visual_sessions[sid].observe())
                    expected = "patient-numpad" if app == "patient" else "therapist-editor"
                    result = runtime.execute_visual_action(request("execute_visual_action"), {
                        "operation": "click", "label": "synthetic-input" if app == "patient" else "synthetic-editor",
                        "observation_id": before["observation"]["id"], "expected_state_after": expected,
                        "coordinates": {"x": ready["x"], "y": ready["y"]},
                    })
                    after_event = events.get(timeout=10)
                    if after_event.get("phase") != "after":
                        raise RuntimeError(str(after_event))
                    row = {"case": case, "status": "LOCAL_CAPTURE_VERIFIED", "viewport": [width, height],
                           "verified_after": after_event["state"], "runtime_evidence": result["evidence"],
                           "decision_coordinates": [ready["x"], ready["y"]], "screenshots": []}
                    for index, phase in enumerate(("initial", "post-click")):
                        image = base64.b64decode(result["_images"][index]["data_base64"], validate=True)
                        digest = hashlib.sha256(image).hexdigest()
                        assert digest == result["result"]["artifacts"][index]["sha256"]
                        assert image[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", image[16:24]) == (width, height)
                        filename = f"{case}-{phase}.png"
                        (output / filename).write_bytes(image)
                        row["screenshots"].append({"file": filename, "sha256": digest, "host_state": result["result"]["state_before" if index == 0 else "state_after"]})
                    assert row["screenshots"][0]["sha256"] != row["screenshots"][1]["sha256"]
                    manifest["cases"].append(row)
                    print(case + ": LOCAL_CAPTURE_VERIFIED", flush=True)
                    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                finally:
                    runtime._close_visual(sid)
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
