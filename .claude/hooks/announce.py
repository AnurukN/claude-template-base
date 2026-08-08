#!/usr/bin/env python
"""Cross-platform (Windows/Linux/macOS) voice announcement hook.
Speaks the given text aloud via the OS's TTS engine and always emits a
visible systemMessage, so the alert still shows up even when no TTS
engine is available or audio is muted.

Usage: python announce.py "<message>"
"""
import json
import platform
import shutil
import subprocess
import sys


def speak(text):
    system = platform.system()
    try:
        if system == "Windows":
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('%s')"
                % text.replace("'", "''")
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_script],
                timeout=10, check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True

        if system == "Darwin" and shutil.which("say"):
            subprocess.run(["say", text], timeout=10, check=False,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        # Linux / other POSIX: try common TTS engines in order.
        for cmd in (["spd-say", text], ["espeak-ng", text], ["espeak", text]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd, timeout=10, check=False,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
        if shutil.which("festival"):
            subprocess.run(["festival", "--tts"], input=text.encode(),
                            timeout=10, check=False,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except Exception:
        pass
    return False


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    if not text:
        return
    spoke = speak(text)
    icon = "\U0001F50A" if spoke else "\U0001F515"
    print(json.dumps({"systemMessage": "%s %s" % (icon, text)}))


if __name__ == "__main__":
    main()
