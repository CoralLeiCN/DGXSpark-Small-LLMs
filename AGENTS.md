# Agent Instructions

- Use `uv` for dependency management and Python command execution.
- Target Python 3.12 for development and runtime assumptions.
- Do not add tests unless the user explicitly asks for tests or the change is a regression fix that needs a regression test.
- Use pytest for Python tests.
- Treat this repository as a container-first DGX Spark model-serving hub.
- Keep supported inference engines limited to vLLM and SGLang unless the project scope changes.
- Prefer thin top-level scripts that call shared Python CLI code.
- Keep model-serving dependencies inside model-specific Docker environments, not the host Python environment.
- Do not assume one vLLM or SGLang version works for every model.
- Keep model-specific launch flags in the relevant model engine folder.
- Keep service-specific tests in the relevant model engine folder.
- Keep documentation proportional to implemented behavior; avoid speculative
  per-engine or troubleshooting docs before the corresponding recipe or
  observation exists.
- Document important assumptions, tradeoffs, and user corrections directly in
  the relevant authoritative spec, guide, or model documentation as they arise.
- If the user corrects an architectural direction, update its authoritative
  documentation rather than keeping a separate duplicate correction history.
- Maintain append-only inference experiment journals under
  `docs/experiments/<model>/<engine>/<hardware>/` by following
  `docs/experiments/README.md`.
- Store every experiment turn in its own UTC-timestamped Markdown file named
  `<YYYY-MM-DDTHH-MM-SSZ>-<short-slug>.md`, and keep the target directory's
  `README.md` index updated.
- Assign every turn the next target-local, zero-padded ID (`RUN-0001`,
  `RUN-0002`, and so on). Put it immediately below the turn title, list it in
  the index, and never reuse or renumber an assigned ID.
- Record every observed failure from Docker build or runtime operations, inference
  engine startup, model loading, health checks, and inference validation. Add the
  entry before ending the work session, even when the failure is still unresolved.
- Each failed experiment entry must include the redacted command and error, relevant
  environment and version details, evidence-based diagnosis, attempted or confirmed
  fix, verification result, status, and a reusable lesson for building reliable
  inference services.
- Keep model recipe slugs globally unique and store provider identity in the
  model manifest instead of a provider directory.
- Treat `model + engine + hardware target` as the deployable pack. Keep each
  target's Dockerfile, Compose file, launch script, environment example, and
  service tests under `models/<model>/<engine>/targets/<hardware>/`.
- Preserve journal chronology: do not add later findings to an earlier turn file.
  Create a new turn file that links to the earlier turn, never fabricate historical
  runs, and never record credentials or other secrets.
