---
name: release
description: Build WhisperFlow's standalone .exe with PyInstaller and cut a GitHub release by pushing a version tag. Use this whenever the user wants to build the WhisperFlow executable, package a release, cut a new version, or push a release tag — even if they just say "build the exe" or "make a release."
---

# Release WhisperFlow

Two separate build paths exist for this repo — don't conflate them:

- **Local build** (this skill): `pyinstaller whisperflow.spec`
- **CI build** (`.github/workflows/build.yml`): `pyinstaller --noconfirm --onefile --windowed --name WhisperFlow src/main.py`, triggered by a `v*` tag push or manual `workflow_dispatch`, runs on `windows-latest`, uploads `dist/WhisperFlow.exe` via `softprops/action-gh-release@v1`.

A local build is for sanity-checking the packaging before you ship a tag; the real release artifact is the one CI produces.

## Steps

1. **Confirm the working tree is clean and on the intended commit.** `git status` — an uncommitted release is not a real release. Don't stash or discard anything without asking.

2. **Build locally with the spec file** (not the raw CI args — the spec is the source of truth for local builds):
   ```
   pip install pyinstaller   # if not already installed
   pyinstaller whisperflow.spec
   ```
   Output lands in `dist/WhisperFlow.exe`.

3. **Check the known asset-bundling gotcha before declaring the build good.** `whisperflow.spec` currently has `datas=[]`, so `assets/` (the tray icons and start/stop sounds) is **not** copied into the exe, even though `src/utils/resources.py::resource_path()` looks for it under `sys._MEIPASS` when frozen. This means a packaged build can run with a missing icon / silent sounds while the dev-mode run looks fine. Before calling a release good:
   - Verify whether `datas=[]` is still empty (it may have been fixed since this skill was written — check, don't assume).
   - If still empty, tell the user explicitly: icons/sounds won't be bundled, and the real fix is adding an entry like `datas=[('assets', 'assets')]` to `whisperflow.spec`. Ask whether to fix it now or ship as-is — don't silently patch the spec without asking, since it changes what CI produces too.

4. **Smoke-test the built exe** by launching `dist/WhisperFlow.exe` directly (not `python -m src.main`) so packaging issues actually surface. There's no automated test suite in this repo, so this manual launch is the only verification available — don't claim the build works without doing it. If icons/sounds are missing, that's consistent with the gotcha above, not a new bug.

5. **Cut the release by pushing a version tag** — this is what actually triggers the CI build and GitHub release, not the local build. Ask the user for the version number if they haven't given one, and confirm with them before pushing, since a tag push is a shared/remote action:
   ```
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   Never force-push or overwrite an existing tag without explicit confirmation.

6. After pushing, tell the user the CI run is what produces the actual release asset, and point them at the Actions tab / `gh run watch` if they want to follow it — don't claim the release is done just because the tag push succeeded.
