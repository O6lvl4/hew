# Reproducible checks

Run `bash ci/check.sh` from a checkout with Almide installed, or set
`ALMIDE_BIN` to an absolute compiler path. This runs the existing tests, builds
`hew`, and checks the built CLI against temporary fixtures. No model API or
credentials are used.

CI pins Almide to `dff9a458f2e581631bb6537c856a7974036e4153` and Rust to
`1.94.0`. Upgrade these deliberately and rerun the checks together. The compiler
binary cache is keyed by both versions. Smoke fixtures are regression coverage,
not a competitive benchmark or proof of general language correctness.

`GRAMIDE_BIN=/absolute/path/to/gramide python3 ci/gramide_integration.py`
checks the actual parser/reader boundary: Rust attributes and raw strings, plus
Python decorators, nested same-named declarations, async methods and `.pyi`
discovery. The GitHub workflow builds a pinned gramide with Python support and
runs this integration test. The checks require the `gramide` engine label so a
heuristic fallback cannot silently pass them.

Recovery integration also checks that an unfinished Python method is omitted
while its intact sibling methods stay selectable, with the `gramide-recovered`
engine label. Provider fixtures reject unknown policies, contradictory complete
flags, missing/invalid error ranges and declarations overlapping those ranges.
