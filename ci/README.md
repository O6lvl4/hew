# Reproducible checks

Run `bash ci/check.sh` from a checkout with Almide installed, or set
`ALMIDE_BIN` to an absolute compiler path. This runs the tests, builds `hew`
— fetching gramide's engine and its four language packages at the commits
`almide.lock` records — and checks the built CLI against temporary fixtures.
No model API or credentials are used.

CI pins Almide to `dff9a458f2e581631bb6537c856a7974036e4153` and Rust to
`1.94.0`. Upgrade these deliberately and rerun the checks together. The compiler
binary cache is keyed by both versions. Smoke fixtures are regression coverage,
not a competitive benchmark or proof of general language correctness.

`ci/gramide_integration.py` checks the linked grammars through hew itself:
Rust attributes and raw strings, Python decorators, nested same-named
declarations, async methods and `.pyi` discovery, all requiring the `gramide`
engine label so a heuristic fallback cannot silently pass them. It also checks
that an unfinished Python method is omitted while its intact sibling methods
stay selectable, with the `gramide-recovered` label, around every kind of
damage the Python package recovers from. `ci/providers.py` covers the
`HEW_OUTLINE_BIN` contract — an explicit provider wins, a provider that breaks
the contract is ignored — and the lossless `read-json` read. The document
validation itself is unit-tested in `src/outline.almd`.
