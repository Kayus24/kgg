"""Run the real SAF transport state machine on the JVM, without Android or Drive.

Uses an already installed JDK and an already cached JSON-java test runtime.
No download, Android installation, credentials or external IO is performed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android-wrapper/app/src/main/java/de/kgg/app/KggDriveSyncTransport.java"
TEST = ROOT / "release-pipeline/tests/java/de/kgg/app/KggDriveSyncTransportTest.java"
ASYNC_SOURCE = ROOT / "android-wrapper/app/src/main/java/de/kgg/app/KggSyncRequestCoordinator.java"
ASYNC_TEST = ROOT / "android-wrapper/app/src/test/java/de/kgg/app/KggSyncRequestCoordinatorTest.java"
FOLLOW_TEST = ROOT / "release-pipeline/tests/java/de/kgg/app/KggSyncFollowConfigTest.java"
LOCAL_SOURCE = ROOT / "android-wrapper/app/src/main/java/de/kgg/app/KggSyncBridge.java"


def android_preference_boundary(directory: Path) -> list[Path]:
    # Only the four Android surfaces used by the real local bridge. No fake
    # sync, configuration logic, file IO or coordinator behavior lives here.
    stubs = {
        "android/webkit/JavascriptInterface.java": "package android.webkit; public @interface JavascriptInterface {}",
        "android/os/Environment.java": 'package android.os; public class Environment { public static final String DIRECTORY_DOCUMENTS="Documents",MEDIA_MOUNTED="mounted"; public static java.io.File getExternalStoragePublicDirectory(String value){return new java.io.File(System.getProperty("kgg.test.storage"),value);} public static String getExternalStorageState(){return "unmounted";} }',
        "android/content/SharedPreferences.java": 'package android.content; public interface SharedPreferences {String getString(String key,String fallback); Editor edit(); interface Editor {Editor putString(String key,String value);void apply();}}',
        "android/content/Context.java": '''package android.content;
public class Context {
 public static final int MODE_PRIVATE=0; private final java.io.File root;
 private final java.util.Map<String,String> values=new java.util.concurrent.ConcurrentHashMap<>();
 public Context(java.io.File root){this.root=root;}
 public Context getApplicationContext(){return this;} public String getPackageName(){return "de.kgg.synthetic";}
 public java.io.File getFilesDir(){return root;} public java.io.File getCacheDir(){return root;}
 public SharedPreferences getSharedPreferences(String name,int mode){return new SharedPreferences(){
  public String getString(String key,String fallback){return values.getOrDefault(name+key,fallback);}
  public Editor edit(){return new Editor(){private String key,value;public Editor putString(String key,String value){this.key=name+key;this.value=value;return this;}public void apply(){values.put(key,value);}};}
 };}
}''',
    }
    paths = []
    for relative, source in stubs.items():
        path = directory / "android-boundary" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--json-jar", type=Path)
    parser.add_argument("--document", type=Path, help="Validate and roundtrip a synthetic document produced by the real HTML builder")
    args = parser.parse_args()
    assert SOURCE.is_file(), "SAF transport is missing; automatic provider IO is not implemented"
    java_home = args.java_home or Path(os.environ.get("JAVA_HOME", "C:/Program Files/Android/Android Studio/jbr"))
    suffix = ".exe" if os.name == "nt" else ""
    java, javac = java_home / f"bin/java{suffix}", java_home / f"bin/javac{suffix}"
    if not java.is_file() or not javac.is_file():
        raise SystemExit("Provide an installed JDK with --java-home; this test never installs one")
    jars = sorted((Path.home() / ".gradle/caches/modules-2/files-2.1/org.json/json").glob("*/*/json-*.jar"))
    jars = [path for path in jars if not path.name.endswith(("-sources.jar", "-javadoc.jar"))]
    json_jar = args.json_jar or (jars[-1] if jars else None)
    if not json_jar or not json_jar.is_file():
        raise SystemExit("Provide an existing JSON-java runtime with --json-jar; no download is performed")
    with tempfile.TemporaryDirectory(prefix="kgg-drive-native-") as directory:
        sources = [SOURCE, TEST, ASYNC_TEST, LOCAL_SOURCE, FOLLOW_TEST, *android_preference_boundary(Path(directory))]
        # The independent reflection-based contract still compiles before the
        # production coordinator exists and reports a precise missing capability.
        if ASYNC_SOURCE.is_file():
            sources.append(ASYNC_SOURCE)
        subprocess.run([str(javac), "-encoding", "UTF-8", "-cp", str(json_jar), "-d", directory,
                        *(str(path) for path in sources)], cwd=ROOT, check=True)
        command = [str(java), "-cp", os.pathsep.join((directory, str(json_jar))), "de.kgg.app.KggDriveSyncTransportTest"]
        if args.document:
            command.append(str(args.document.resolve(strict=True)))
        subprocess.run(command, cwd=ROOT, check=True)
        subprocess.run([str(java), "-cp", os.pathsep.join((directory, str(json_jar))),
                        "de.kgg.app.KggSyncRequestCoordinatorTest"], cwd=ROOT, check=True)
        subprocess.run([str(java), "-cp", os.pathsep.join((directory, str(json_jar))),
                        "de.kgg.app.KggSyncFollowConfigTest"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
