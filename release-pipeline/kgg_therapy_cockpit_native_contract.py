"""Static contract checks for the Android Therapy-Cockpit app-link handoff.

The Android build itself runs in the repository CI workflow.  This local check
keeps the bounded intent filter and the WebView handoff reviewable when the
machine running the source batteries has no Android SDK or Gradle installation.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID_MANIFEST = ROOT / "android-wrapper" / "app" / "src" / "main" / "AndroidManifest.xml"
MAIN_ACTIVITY = (
    ROOT
    / "android-wrapper"
    / "app"
    / "src"
    / "main"
    / "java"
    / "de"
    / "kgg"
    / "app"
    / "MainActivity.java"
)
COCKPIT_PATCH = ROOT / "kgg-update" / "src" / "patches" / "v082-therapy-cockpit.html"

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class ContractError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ContractError(message)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")


def check_manifest() -> None:
    try:
        root = ET.fromstring(read(ANDROID_MANIFEST))
    except ET.ParseError as exc:
        fail(f"AndroidManifest.xml is not valid XML: {exc}")
    activities = root.findall("./application/activity")
    main = next(
        (
            activity
            for activity in activities
            if activity.get(ANDROID_NS + "name") == ".MainActivity"
        ),
        None,
    )
    if main is None:
        fail("MainActivity declaration is missing")
    if main.get(ANDROID_NS + "exported") != "true":
        fail("MainActivity must remain exported for the external app-link")
    if main.get(ANDROID_NS + "launchMode") != "singleTop":
        fail("MainActivity must use singleTop so a foreground task receives onNewIntent")

    view_filter = None
    for intent_filter in main.findall("intent-filter"):
        actions = {
            node.get(ANDROID_NS + "name")
            for node in intent_filter.findall("action")
        }
        categories = {
            node.get(ANDROID_NS + "name")
            for node in intent_filter.findall("category")
        }
        data_nodes = intent_filter.findall("data")
        if "android.intent.action.VIEW" in actions and {
            "android.intent.category.DEFAULT",
            "android.intent.category.BROWSABLE",
        }.issubset(categories):
            view_filter = data_nodes
            break
    if not view_filter or len(view_filter) != 1:
        fail("exactly one bounded VIEW/DEFAULT/BROWSABLE cockpit data entry is required")
    data = view_filter[0]
    expected = {
        "scheme": "https",
        "host": "kayus24.github.io",
        "path": "/kgg/kgg-update/index.html",
    }
    for key, value in expected.items():
        if data.get(ANDROID_NS + key) != value:
            fail(f"cockpit app-link data {key} must be {value!r}")
    if data.get(ANDROID_NS + "pathPrefix") or data.get(ANDROID_NS + "pathPattern"):
        fail("cockpit app-link must not widen the exact public path")


def check_activity_source() -> None:
    source = read(MAIN_ACTIVITY)
    required = {
        'COCKPIT_DEEP_LINK_PREFIX = "KGGTC1:"': "KGGTC1 prefix",
        'COCKPIT_DEEP_LINK_HOST = "kayus24.github.io"': "trusted host",
        'COCKPIT_DEEP_LINK_PATH = "/kgg/kgg-update/index.html"': "trusted path",
        "MAX_COCKPIT_DEEP_LINK_CHARS = 30_000": "payload size bound",
        "MAX_COCKPIT_DELIVERY_ATTEMPTS = 25": "bounded WebView retry",
        "protected void onNewIntent(Intent intent)": "foreground intent handoff",
        "extractCockpitCode(Intent intent)": "native payload validation",
        "isTrustedCockpitUri(Uri data)": "origin/path validation",
        "getQueryParameters(parameter)": "duplicate query key rejection",
        "getQueryParameterNames().contains(\"cockpit\")": "query presence guard",
        "localWebAppUrlWithCockpit(String cockpitCode)": "local URL handoff",
        "queueCockpitCode(String cockpitCode)": "RAM-only pending handoff",
        "deliverPendingCockpitCode()": "same-WebView delivery",
        "window.KGGTherapyCockpit": "web cockpit API handoff",
        "api.importCode(": "web import call",
        "JSONObject.quote(cockpitCode)": "JavaScript string escaping",
        "webView.postDelayed(this::deliverPendingCockpitCode, 160L)": "bounded retry delay",
        "showCockpitLinkError()": "invalid-link guard",
    }
    missing = [label for token, label in required.items() if token not in source]
    if missing:
        fail("MainActivity cockpit handoff contract missing: " + ", ".join(missing))
    if "webView.loadUrl(data.toString())" in source or "webView.loadUrl(cockpitCode)" in source:
        fail("native code must never navigate WebView to an unvalidated external payload")
    if "Log." in source and "cockpitCode" in source:
        fail("cockpit payload must never be written to Android logs")
    if 'android.intent.action.VIEW' in source:
        fail("Android intent declarations belong in the manifest, not executable source")


def check_web_contract() -> None:
    source = read(COCKPIT_PATCH)
    marker = 'PUBLIC_BASE="https://kayus24.github.io/kgg/kgg-update/index.html"'
    if marker not in source:
        fail("web codec public base must match the native app-link")
    parsed = urllib.parse.urlparse("https://kayus24.github.io/kgg/kgg-update/index.html")
    if (parsed.scheme, parsed.netloc, parsed.path) != (
        "https",
        "kayus24.github.io",
        "/kgg/kgg-update/index.html",
    ):
        fail("web public base has an unexpected origin/path")
    if "MAX_CODE_CHARS=30000" not in source:
        fail("web codec and native handoff must share the 30000 character bound")


def main() -> int:
    try:
        check_manifest()
        check_activity_source()
        check_web_contract()
    except ContractError as exc:
        print(f"Therapie-Cockpit native contract: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "contract": "therapy-cockpit-native-deeplink-v1",
                "manifest": "exact_https_view_filter",
                "handoff": "validated_query_to_local_webview",
                "retry": 25,
                "status": "PASS",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
