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
DRIVE_BRIDGE_SOURCE = ROOT / "android-wrapper/app/src/main/java/de/kgg/app/KggDriveSyncBridge.java"
SELECTION_TEST = ROOT / "release-pipeline/tests/java/de/kgg/app/KggDriveSyncBridgeSelectionTest.java"


def android_preference_boundary(directory: Path) -> list[Path]:
    # Only the four Android surfaces used by the real local bridge. No fake
    # sync, configuration logic, file IO or coordinator behavior lives here.
    stubs = {
        "android/webkit/JavascriptInterface.java": "package android.webkit; public @interface JavascriptInterface {}",
        "android/os/Environment.java": 'package android.os; public class Environment { public static final String DIRECTORY_DOCUMENTS="Documents",MEDIA_MOUNTED="mounted"; public static java.io.File getExternalStoragePublicDirectory(String value){return new java.io.File(System.getProperty("kgg.test.storage"),value);} public static String getExternalStorageState(){return "unmounted";} }',
        "android/content/SharedPreferences.java": 'package android.content; public interface SharedPreferences {String getString(String key,String fallback); Editor edit(); interface Editor {Editor putString(String key,String value);void apply();boolean commit();}}',
        "android/content/Context.java": '''package android.content;
public class Context {
 public static final int MODE_PRIVATE=0; private final java.io.File root;
 private final java.util.Map<String,String> values=new java.util.concurrent.ConcurrentHashMap<>();
 public Context(java.io.File root){this.root=root;}
 public Context getApplicationContext(){return this;} public String getPackageName(){return "de.kgg.synthetic";}
 public java.io.File getFilesDir(){return root;} public java.io.File getCacheDir(){return root;}
 public SharedPreferences getSharedPreferences(String name,int mode){return new SharedPreferences(){
  public String getString(String key,String fallback){return values.getOrDefault(name+key,fallback);}
  public Editor edit(){return new Editor(){private String key,value;public Editor putString(String key,String value){this.key=name+key;this.value=value;return this;}public void apply(){values.put(key,value);}public boolean commit(){apply();return true;}};}
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


def android_saf_boundary(directory: Path) -> list[Path]:
    # SDK surfaces only. The real bridge owns result validation, grant decisions,
    # configuration persistence and its unchanged transport/coordinator.
    stubs = {
        "android/app/Activity.java": '''package android.app;
public abstract class Activity extends android.content.Context {
 public static final int RESULT_OK=-1;
 public Activity(java.io.File root){super(root);}
 public abstract android.content.ContentResolver getContentResolver();
 public void runOnUiThread(Runnable action){action.run();}
 public abstract void startActivityForResult(android.content.Intent intent,int request);
}''',
        "android/content/Intent.java": '''package android.content;
public class Intent {
 public static final int FLAG_GRANT_READ_URI_PERMISSION=1,FLAG_GRANT_WRITE_URI_PERMISSION=2,FLAG_GRANT_PERSISTABLE_URI_PERMISSION=64;
 public static final String ACTION_CREATE_DOCUMENT="create",ACTION_OPEN_DOCUMENT="open",CATEGORY_OPENABLE="openable",EXTRA_TITLE="title",EXTRA_ALLOW_MULTIPLE="multiple";
 private int flags;private android.net.Uri data;private ClipData clip;
 public Intent(){}public Intent(String action){}
 public Intent addCategory(String value){return this;}public Intent setType(String value){return this;}
 public Intent addFlags(int value){flags|=value;return this;}public int getFlags(){return flags;}
 public Intent putExtra(String key,String value){return this;}public Intent putExtra(String key,boolean value){return this;}
 public Intent setData(android.net.Uri value){data=value;return this;}public android.net.Uri getData(){return data;}
 public Intent setClipData(ClipData value){clip=value;return this;}public ClipData getClipData(){return clip;}
}''',
        "android/content/ClipData.java": '''package android.content;
public class ClipData {
 private final java.util.List<Item> items=new java.util.ArrayList<>();
 public ClipData(android.net.Uri... uris){for(android.net.Uri uri:uris)items.add(new Item(uri));}
 public int getItemCount(){return items.size();}public Item getItemAt(int index){return items.get(index);}
 public static class Item{private final android.net.Uri uri;public Item(android.net.Uri value){uri=value;}public android.net.Uri getUri(){return uri;}}
}''',
        "android/content/ContentResolver.java": '''package android.content;
public abstract class ContentResolver {
 public abstract java.util.List<UriPermission> getPersistedUriPermissions();
 public abstract void takePersistableUriPermission(android.net.Uri uri,int flags);
 public abstract void releasePersistableUriPermission(android.net.Uri uri,int flags);
 public abstract android.database.Cursor query(android.net.Uri uri,String[] projection,String selection,String[] args,String order);
 public abstract java.io.InputStream openInputStream(android.net.Uri uri)throws java.io.FileNotFoundException;
 public abstract java.io.OutputStream openOutputStream(android.net.Uri uri,String mode)throws java.io.FileNotFoundException;
}''',
        "android/content/UriPermission.java": '''package android.content;
public final class UriPermission {
 private final android.net.Uri uri;private final int flags;
 public UriPermission(android.net.Uri uri,int flags){this.uri=uri;this.flags=flags;}
 public android.net.Uri getUri(){return uri;}public boolean isReadPermission(){return(flags&1)!=0;}public boolean isWritePermission(){return(flags&2)!=0;}
}''',
        "android/net/Uri.java": '''package android.net;
public final class Uri {
 private final String value;private Uri(String value){this.value=value;}
 public static Uri parse(String value){return new Uri(value);}public String getScheme(){return java.net.URI.create(value).getScheme();}
 public String toString(){return value;}public boolean equals(Object other){return other instanceof Uri&&value.equals(((Uri)other).value);}public int hashCode(){return value.hashCode();}
}''',
        "android/database/Cursor.java": '''package android.database;
public interface Cursor extends AutoCloseable {
 boolean moveToFirst();int getColumnIndex(String name);int getInt(int column);String getString(int column);long getLong(int column);boolean isNull(int column);void close();
}''',
        "android/provider/DocumentsContract.java": '''package android.provider;
public final class DocumentsContract {public static final class Document {
 public static final String COLUMN_FLAGS="flags",COLUMN_MIME_TYPE="mime",MIME_TYPE_DIR="directory";public static final int FLAG_SUPPORTS_WRITE=2;
}}''',
        "android/provider/OpenableColumns.java": 'package android.provider; public interface OpenableColumns {String SIZE="size";}',
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
        sources = [SOURCE, TEST, ASYNC_TEST, LOCAL_SOURCE, FOLLOW_TEST, DRIVE_BRIDGE_SOURCE, SELECTION_TEST,
                   *android_preference_boundary(Path(directory)), *android_saf_boundary(Path(directory))]
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
        subprocess.run([str(java), "-cp", os.pathsep.join((directory, str(json_jar))),
                        "de.kgg.app.KggDriveSyncBridgeSelectionTest"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
