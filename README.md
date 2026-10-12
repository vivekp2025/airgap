# Offline Python Wheel Hub — GitHub Pages + Actions

This project generates offline wheel ZIP bundles with complete pip-resolved PyPI dependencies for Windows x64, Windows x86, Windows ARM64, or compatible Linux x64.

## Create your website

1. Create a **public or private** GitHub repo, for example `airgap-wheelhub`, and upload the files **preserving `.github/workflows/build-wheelhouse.yml`**. GitHub Pages availability depends on your GitHub plan/repository visibility.
2. Under **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`, and save.
3. Open the resulting Pages URL, usually `https://YOUR-USERNAME.github.io/airgap-wheelhub/`.
4. Enter your package requirements (or load a local requirements.txt), Python version, platform and repo name. Click **Open GitHub Actions** and run the workflow with corresponding inputs. An Actions download cannot be initiated anonymously from a static website; the GitHub interface provides authenticated download.
5. Download the artifact ZIP from the completed Actions run, extract it, and transfer `offline-wheels-*.zip` to the air-gapped machine. Extract that ZIP too and run `INSTALL_OFFLINE.bat` (or your explicit Python executable).

## Example for Flask

Input:
```text
Flask
waitress
```
The build resolves Flask dependencies and packages the wheels, exact manifest, a no-index installer and verification scripts.

## Notes

- For an offline WinPython Python 3.11 64-bit interpreter, choose **3.11** and **win_amd64**. Always check your target computer rather than assuming its version.
- Wheel-only resolution fails if an architecture/Python version lacks a published wheel. This is safer than silently bundling source archives that cannot install offline.
- `pip download` computes transitive dependencies, but dependency markers for a different OS can sometimes differ from the runner's OS. A clean-target test is recommended for complex stacks. For Flask the stack is normally platform-independent.
- The downloaded bundle needs an existing Python installation with pip; it does not contain Python itself.
- GitHub-hosted workflow execution and artifact retention are subject to GitHub account limits.
- Avoid private/proprietary requirements in a public repository's workflow inputs; they may be visible in logs.
