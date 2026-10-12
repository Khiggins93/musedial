# Contribuir / Contributing

Issues and pull requests are welcome in Spanish or English. Discuss new boards and major control changes before implementation. Keep the offline/no-PSRAM baseline operational.

1. Fork and create a branch.
2. Follow `docs/BUILD.md` or `docs/BUILD.en.md` using pinned dependencies.
3. Run `python -m unittest discover -s tests -v`, `python tools/build.py` and release verification.
4. For behavior changes, include tests for thresholds, effect cancellation and both themes. For visual changes, include screenshots and rendering commands.
5. Report hardware, version, measured fps/memory and which physical inputs you tested. Do not label simulated USB actions as physical confirmation.

Never commit `backups/`, full-flash images, NVS, tokens, personal logs, device MAC addresses or absolute home-directory paths. Commit animation resources only after reviewing their provenance and updating the lock hash. Do not silently update dependencies or remove recovery checks.

Contributions to project-authored material are made under Apache 2.0, subject to `NOTICE`; retain all upstream notices. No CLA is required.
