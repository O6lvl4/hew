# hew

Read code the way a model should. `hew` is a replacement for the `cat` / `grep` / `sed -n` /
`awk '/^fn x/,/^}/'` pipelines that coding agents run hundreds of times a session, built so
that every call returns exactly what was asked for, numbered, sized, and aware of the code's
structure.

[日本語](README_ja.md)

```
hew src/lower.rs --symbol lower_match       one function, found by name
hew src/lower.rs --grep "Expr::Match" --around 4   matches with context, labelled by enclosing fn
hew src/lower.rs --lines 120-160            a range, numbered
hew outline src/lower.rs                    the table of contents
hew grep "unwrap()" src                     grep that folds repeats and names the symbol
hew tree src --depth 2                      a directory, skipping vcs / build / deps
```

## Why

An agent that reads a 4,000-line file to answer a question about one function pays for the
whole file on every later turn. Agents know this, and narrow with shell pipelines. Those
pipelines are brittle (`awk` ranges break on nested braces, `sed -n` needs line numbers the
model has to find first, `grep -n` results say nothing about *where* a match is). `hew`
does the narrowing properly, once, in one binary:

- **Structure-aware.** `--symbol` cuts out a function, type, class, impl method or test by
  name. Almide, Rust, Go, Python, JavaScript and TypeScript, JSX and `.tsx` included, are
  parsed by [gramide](https://github.com/O6lvl4/gramide)'s grammars, linked into the binary;
  a Python, JavaScript or TypeScript file halfway through an edit is read through its
  recovered declarations. `HEW_OUTLINE_BIN` plugs in an outline provider for any other
  language.
- **Numbered and sized.** Every line carries its number so the next call can be
  `--lines A-B`. Long lines are clipped. Gaps are marked with how many lines were skipped.
  The header says how big the whole file is; the footer says how much was shown.
- **Grep that tells you where.** Matches are grouped per file, identical lines are folded
  (`×3`), each match names the enclosing symbol, per-file and total caps keep the output
  bounded.
- **Never withholds.** `hew` only returns what was asked for. There is no summarisation and
  no budget; the model decides.

## What the model sees

```
$ hew src/cmds/git/git.rs --symbol compact_diff
# src/cmds/git/git.rs  (4720 lines, 168 KB)
       ⋮  (647 lines)
     ── fn compact_diff ──
 648│ pub fn compact_diff(input: &str, opts: &DiffOpts) -> String {
 649│     let mut out = String::new();
 …
 821│ }
       ⋮  (3899 lines)
# shown: 174 lines, 6 KB
```

```
$ hew grep "fn run_" src/cmds/git
# 14 matches in 3 files
src/cmds/git/git.rs  (9)
  112│ pub fn run_diff(args: &[String]) -> Result<()>    ‹run_diff›
  230│ pub fn run_log(args: &[String]) -> Result<()>     ‹run_log›
  …
src/cmds/git/stash.rs  (2)
   40│ pub fn run_stash(args: &[String]) -> Result<()>   ‹run_stash›
```

```
$ hew src/lower.rs --grep "Expr::Match" --around 2
# src/lower.rs  (1210 lines, 41 KB)
       ⋮  (310 lines)
     ── in fn lower_expr ──
 311│         Expr::If { .. } => self.lower_if(e),
 312│         Expr::Match { scrutinee, arms } => self.lower_match(scrutinee, arms),
 313│         Expr::Block(b) => self.lower_block(b),
       ⋮  (402 lines)
     ── in fn lower_match ──
 716│     // Expr::Match with a single arm is a let
 …
# shown: 12 lines, 640 B
```

## Install

```bash
almide install github.com/O6lvl4/hew      # one native binary → ~/.local/bin/hew
```

One binary, no runtime, no other tools required: the parsers are inside it, and
`hew --version` names the engine and grammar versions it was built with. Optionally,
`HEW_OUTLINE_BIN=<program>` names an outline provider (called with a path, must print
`{"lang","total_lines","symbols":[{"kind","name","start","end"}]}`); when set, its answer is
used for `--symbol`, `outline` and grep labels, for any language it knows. Any tree-sitter
based tool that speaks this contract can be plugged in.

## Teach your agent

Add to `CLAUDE.md` (or the equivalent for your agent):

```
Read code with `hew`, not cat / sed -n / awk:
- `hew <file> --symbol NAME`            one function or type
- `hew <file> --grep RE [--around N]`   matches with context
- `hew <file> --lines A-B`              a range (output is numbered, so you can come back)
- `hew outline <file|dir>`              what is in a file before reading it
- `hew grep RE [path]`                  search that names the enclosing symbol
```

## Commands

```
hew <file> [--lines A-B] [--symbol NAME] [--grep RE] [--around N] [--head N] [--tail N] [--clip N]
hew outline <file|dir> [--max N]
hew grep <RE> [path...] [--per-file N] [--max-files N] [--clip N]
hew tree <dir> [--depth N]
```

`--around` defaults to 3, `--clip` to 200 characters, `--per-file` to 20 matches,
`--max-files` to 50. Regexes are Rust-syntax without `\b` or lazy quantifiers (Almide's
regex). `grep` and `tree` skip `.git`, `target`, `node_modules`, `dist`, `build`, `vendor`,
virtualenvs and files over 2 MB.

## Architecture

![hew architecture](docs/architecture.svg)

The agent calls `hew` through Bash. `main` parses the arguments, picks the command and
composes three modules:

- **view** — takes the line windows to show and produces numbered lines, clipping, gap
  markers, header and footer.
- **outline** — the table of contents. Almide, Rust, Go, Python, JavaScript (with JSX) and
  TypeScript (with `.tsx`) are parsed by the gramide grammars in **parsers** (strict first,
  then the recovered document where the package offers one). Otherwise — a provider that
  broke its contract — a per-language table of declaration rules finds declaration lines
  and brace matching (indentation for Python) finds their ranges, behind a stateful lexical
  mask that hides comments and literals. Those remain heuristics: multiline headers, regex
  literals and template interpolation are not a full grammar. `find(name)` looks a symbol
  up by name, `enclosing(line)` by line.
- **search** — walks directories (skipping vcs / build / deps / binaries), groups matches per
  file, folds identical lines, applies caps, and asks outline for the enclosing symbol.

Everything is built in, the grammars included. `HEW_OUTLINE_BIN` can name an external
outline program whose JSON answer replaces the built-in rules.

Written in [Almide](https://github.com/almide/almide). Dual-licensed MIT / Apache-2.0.

## Against ast-grep's outline

`ast-grep outline` (0.45) is the other structure-aware outline a coding agent can
call today, over tree-sitter grammars. Measured on this machine, fresh processes,
minimum of nine runs ([evidence](docs/evidence/ast-grep-outline.json)):

| | files | hew | ast-grep |
|---|---:|---:|---:|
| Node `lib/` (JavaScript) | 427 | 0.059 s | 0.057 s |
| TypeScript 5.9 `src/` | 701 | 0.153 s | 0.172 s |

The TypeScript number is bounded by one file: `checker.ts` is 3.1 MB and parses in
about 0.10 s, and no arm can finish before the arm holding it. The files are dealt
to the eight arms largest first, each to the arm with the least bytes so far, and
the answers come out as one write; cutting the list into equal byte ranges instead
put that file and 2.5 MB of neighbours in one slice, and printing 49,000 lines one
at a time cost as much as the parsing.

On a class whose third member's header is broken (`broken( {`), hew lists the two
intact methods and the function after the class from the recovered parse, labelled
`gramide-recovered`; ast-grep answers `nothing found`. What hew does not have is
ast-grep's language count: six grammars against tree-sitter's hundreds, with the
`HEW_OUTLINE_BIN` contract as the way to plug the rest in.

## Parser-backed reading

hew links [gramide](https://github.com/O6lvl4/gramide) — the engine — and its
six language packages ([Almide](https://github.com/O6lvl4/gramide-almide),
[Go](https://github.com/O6lvl4/gramide-go), [Rust](https://github.com/O6lvl4/gramide-rust),
[Python 3.14](https://github.com/O6lvl4/gramide-python),
[JavaScript](https://github.com/O6lvl4/gramide-javascript),
[TypeScript 5.9](https://github.com/O6lvl4/gramide-typescript)) as ordinary Almide
dependencies, pinned in `almide.lock`: the same composition the `gramide`
command ships, called in-process, so a directory outline costs a parse per
file rather than a process per file, and nothing has to be on `PATH`.
Directory outlines read every extension a linked package answers `symbols`
for, `.pyi` included. The grammar provides declaration ranges, including Rust
attributes, multiline headers and Python decorators. Python nested classes and
functions have qualified paths, such as `Outer.Inner.method` and
`Outer.method.helper`, so `--symbol` can select same-named declarations
precisely. An explicit `HEW_OUTLINE_BIN` provider takes precedence. A failed
parse uses the explicit recovered-declaration contract where the package
offers one, then the built-in heuristics. Outline headers and selected-symbol
labels identify `gramide`, `gramide-recovered`, `provider` or `heuristic`;
fallback is not parser parity.

The document each source produces is checked the same way — language, line
count, well-formed ranges within the actual file, and for the strict grammar
path schema version 1 and a complete parse — whether it came from the linked
engine or from a provider. No tree-sitter installation is required.

`hew read-json FILE --max-chars 24000` returns versioned JSON with the exact
`content`, requested `path`, `total_chars` and `complete`. It preserves line endings
and long lines, with no display labels. Limits count Unicode characters (not
bytes). A false `complete` means the content is a prefix, unsuitable for replacing
the whole file. The supported limit range is 1–1,000,000 characters.

For incomplete Python, hew reads the recovered document after strict parsing
fails. It validates the recovery policy, diagnostic, ordered error ranges and
declaration ranges, rejecting declarations that overlap errors. Intact sibling
methods remain selectable by qualified name; an enclosing class or function
containing an error is omitted. Output says `gramide-recovered`. This does not
make the file syntactically valid; damage the package cannot bound still uses
the labeled heuristic fallback.
