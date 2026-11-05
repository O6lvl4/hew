"""Two hew binaries on the same calls over one corpus: fresh processes, wall
time, alternating order (A B B A ...), the median and minimum of each, and
whether the two print the same bytes.

    python3 bench/old_vs_new.py <hew A> <hew B> <corpus dir>
"""
import os
import statistics
import subprocess
import sys
import time

a, b, root = sys.argv[1], sys.argv[2], sys.argv[3]
samples = 15
env = dict(os.environ, HEW_OUTLINE_BIN="")


def p(rel):
    return os.path.join(root, rel)


CALLS = [
    ("outline .rs (large)", ["outline", p("crates/almide-mir/src/render_native.rs")]),
    ("outline .rs dir", ["outline", p("crates/almide-frontend/src/check")]),
    ("outline .almd", ["outline", p("stdlib/json.almd")]),
    ("outline .md", ["outline", p("docs/CHEATSHEET.md")]),
    ("--symbol .rs", [p("crates/almide-mir/src/render_native.rs"), "--symbol", "render_native_items"]),
    ("--grep .rs", [p("crates/almide-mir/src/render_native.rs"), "--grep", "fn [a-z_]+\\(", "--around", "1"]),
    ("grep dir", ["grep", "IntOp::Mul", p("crates")]),
    ("tree", ["tree", p("crates"), "--depth", "2"]),
]


def run(binary, args):
    t = time.perf_counter()
    r = subprocess.run([binary] + args, capture_output=True, env=env)
    return time.perf_counter() - t, r.returncode, r.stdout


print(f"{'call':22s} {'A med ms':>9s} {'B med ms':>9s} {'B/A':>6s} {'A min':>7s} {'B min':>7s}  same output")
for name, args in CALLS:
    run(a, args)
    run(b, args)
    ta, tb = [], []
    for i in range(samples):
        order = (a, b) if i % 2 == 0 else (b, a)
        for binary in order:
            dt, _, _ = run(binary, args)
            (ta if binary == a else tb).append(dt * 1000)
    _, ca, oa = run(a, args)
    _, cb, ob = run(b, args)
    same = "yes" if (ca, oa) == (cb, ob) else f"NO (exit {ca}/{cb}, {len(oa)}/{len(ob)} bytes)"
    ma, mb = statistics.median(ta), statistics.median(tb)
    print(f"{name:22s} {ma:9.1f} {mb:9.1f} {mb / ma:6.2f} {min(ta):7.1f} {min(tb):7.1f}  {same}")
for label, binary in (("A", a), ("B", b)):
    print(f"{label} size {os.path.getsize(binary):,} bytes")
