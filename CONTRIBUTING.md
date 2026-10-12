# Contribuir / Contributing

Comparto MuseDial para que puedas experimentar con él y ayudarme a mejorarlo. Puedes abrir issues y pull requests en español o inglés. Antes de añadir soporte para otras placas o cambiar los controles principales, conversemos en un issue.

I'm sharing MuseDial so you can experiment with it and help me improve it. I welcome issues and pull requests in Spanish or English. Please discuss new boards and major control changes with me in an issue before implementation. Keep the offline/no-PSRAM baseline operational.

1. Fork and create a branch.
2. Follow `docs/BUILD.md` or `docs/BUILD.en.md` using pinned dependencies.
3. Run `python -m unittest discover -s tests -v`, `python tools/build.py` and release verification.
4. For behavior changes, include tests for thresholds, effect cancellation and both themes. For visual changes, include screenshots and rendering commands.
5. Report hardware, version, measured fps/memory and which physical inputs you tested. Do not label simulated USB actions as physical confirmation.

Never commit `backups/`, full-flash images, NVS, tokens, personal logs, device MAC addresses or absolute home-directory paths. Commit animation resources only after reviewing their provenance and updating the lock hash. Do not silently update dependencies or remove recovery checks.

Contributions to project-authored material are made under Apache 2.0, subject to `NOTICE`; retain all upstream notices. No CLA is required.
