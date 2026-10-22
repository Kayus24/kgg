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
        subprocess.run([str(javac), "-encoding", "UTF-8", "-cp", str(json_jar), "-d", directory,
                        str(SOURCE), str(TEST)], cwd=ROOT, check=True)
        command = [str(java), "-cp", os.pathsep.join((directory, str(json_jar))), "de.kgg.app.KggDriveSyncTransportTest"]
        if args.document:
            command.append(str(args.document.resolve(strict=True)))
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
