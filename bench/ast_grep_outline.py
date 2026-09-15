"""hew outline against ast-grep outline: fresh processes, wall time, and what
each answers on a file that does not parse. Writes the evidence the README
cites.

    python3 bench/ast_grep_outline.py <ast-grep binary> <dir>... --out docs/evidence/ast-grep-outline.json

Both tools are warmed once, then run in deterministic alternating order,
`--samples` times per directory (default 5); the minimum wall time is
reported, with the median beside it. hew is run with HEW_OUTLINE_BIN unset
so the linked grammars answer. Nothing here is an incremental-parse or
editor-latency measurement; it is the cost an agent pays for one call."""
from pathlib import Path
import json, os, platform, statistics, subprocess, sys, tempfile, time

args = sys.argv[1:]
out = Path(args[args.index("--out") + 1]) if "--out" in args else None
samples = int(args[args.index("--samples") + 1]) if "--samples" in args else 5
positional = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--out", "--samples"))]
sg, dirs = positional[0], positional[1:]
hew = Path(__file__).resolve().parents[1] / "hew"
env = dict(os.environ, HEW_OUTLINE_BIN="")

def timed(cmd):
    t = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return time.perf_counter() - t, p

def measure(cmd):
    timed(cmd)
    return [timed(cmd)[0] for _ in range(samples)]

results = {"platform": platform.platform(), "cpus": os.cpu_count(), "samples": samples,
           "ast_grep_version": subprocess.check_output([sg, "--version"], text=True).strip(),
           "hew_version": subprocess.check_output([str(hew), "--version"], text=True, env=env).splitlines()[0],
           "directories": [], "broken_file": {}}
for d in dirs:
    files = [p for p in Path(d).rglob("*") if p.suffix in (".js", ".mjs", ".cjs", ".ts", ".mts", ".cts")]
    row = {"dir": d, "files": len(files), "bytes": sum(p.stat().st_size for p in files)}
    for name, cmd in [("hew", [str(hew), "outline", d, "--max", "100000"]), ("ast_grep", [sg, "outline", "--json=stream", "--items", "structure", d])]:
        ts = [tools for tools in measure(cmd)]
        _, p = timed(cmd)
        row[name] = {"min_seconds": round(min(ts), 4), "median_seconds": round(statistics.median(ts), 4), "output_lines": len(p.stdout.splitlines())}
    results["directories"].append(row)

# a class whose third member's header is broken: what each tool still lists
with tempfile.TemporaryDirectory() as tmp:
    for ext, text in [("ts", "export class A {\n  ok(): number { return 1 }\n  broken(: {\n  also(x: string) { return x }\n}\nexport function f(): void {}\n"),
                      ("js", "export class A {\n  ok() { return 1 }\n  broken( {\n  also(x) { return x }\n}\nexport function f() {}\n")]:
        p = Path(tmp) / ("broken." + ext); p.write_text(text)
        h = subprocess.run([str(hew), "outline", str(p)], capture_output=True, text=True, env=env).stdout
        s = subprocess.run([sg, "outline", str(p)], capture_output=True, text=True).stdout
        results["broken_file"][ext] = {"hew": [l.strip() for l in h.splitlines()[1:]], "ast_grep": [l.strip() for l in s.splitlines()[1:]] or ["nothing found"] if "nothing found" in s else [l.strip() for l in s.splitlines()[1:]]}

print(json.dumps({k: v for k, v in results.items() if k != "platform"}, indent=1)[:3000])
if out:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n")
