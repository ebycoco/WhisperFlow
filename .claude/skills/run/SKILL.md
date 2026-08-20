---
name: run
description: Launch WhisperFlow from source and manually verify a change actually works — tray icon, login, global hotkey, floating overlay, and text injection. Use this whenever the user wants to run, start, test, or check the WhisperFlow app, or asks "does this work" / "did my change work" after editing anything under src/. There is no automated test suite in this repo, so this manual walkthrough is the only way to verify behavior.
---

# Run and verify WhisperFlow

WhisperFlow is a Windows system-tray app driven by a global hotkey and a real microphone — it cannot be
meaningfully tested by a headless script or a generic browser/CLI check. "Does it work" means walking
through the actual dictation flow by hand and reading the log file, not simulating it.

## Launch

```
venv\Scripts\activate
pip install -r requirements.txt   # only if dependencies changed
python -m src.main
```

Run this with `run_in_background` (or in a terminal the user can watch) since it's a long-lived tray
process — it won't exit on its own.

## What "it started" actually looks like

There is no console window (`console=False` in the packaging spec) — success is silent. Confirm startup
by:
- A WhisperFlow icon appearing in the Windows system tray.
- The log file `%APPDATA%/WhisperFlow/logs/whisperflow.log` (rotating, 5MB × 3 backups) showing the
  `WhisperFlow starting up` banner with no `CRITICAL` line after it. Read this file instead of guessing
  when something seems off — it's the only visibility into a background Tkinter/tray process.

## Manual smoke-test checklist

Walk the user through this in order — each step depends on the previous one succeeding, per the app's
own startup sequence (`src/app.py`):

1. **App starts without crashing** → tray icon visible.
2. **Auth gate**: if not already logged in, a login window appears (Supabase auth is required before the
   hotkey listener starts at all — see `App._on_login_success`). Log in or confirm the user is already
   authenticated before expecting the hotkey to do anything.
3. **Hold the hotkey** (default `ctrl+shift+space`, hold-to-record mode by default) with focus in a text
   field (Notepad is a good target) → the floating overlay should appear showing a "listening" state.
4. **Release the hotkey** → overlay transitions to "processing", then "success" (or "error" — check the
   log if so).
5. **Text appears in the focused field**, injected via clipboard + simulated Ctrl+V, with a trailing
   space. If nothing is typed, check the log for transcription or injection errors before assuming the
   hotkey itself is broken — the pipeline has several independent failure points (mic capture →
   transcription engine → cleaner → injector).

If the user changed the transcription engine (`local`/`groq`), also confirm which engine is configured in
Settings (tray icon → right-click → Settings) — `WhisperEngine` lazy-loads its model on first use, so the
first dictation after switching engines or restarting will be slower while the model loads; that's
expected, not a bug.

## Reporting results

Be explicit that this was a manual walkthrough, not an automated test — there is nothing in this repo to
run instead. If a step fails, quote the relevant log line(s) rather than speculating about the cause.
