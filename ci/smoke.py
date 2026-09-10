"""Exercise the built CLI without network or model credentials."""
from pathlib import Path
import subprocess
import tempfile

BIN = Path(__file__).resolve().parents[1] / "hew"

def run(*args, code=0):
    p = subprocess.run([str(BIN), *map(str, args)], capture_output=True, text=True, timeout=30)
    assert p.returncode == code, (args, p.returncode, p.stdout, p.stderr)
    return p.stdout

with tempfile.TemporaryDirectory() as tmp:
    source = Path(tmp) / "comments.rs"
    source.write_text("fn real() {\n    /* }\nfn phantom() {}\n    */\n    let value = 1;\n}\nfn next() {}\n")
    outline = run("outline", source)
    assert "phantom" not in outline, outline
    assert "L1-6" in outline and "L7-7" in outline, outline
    selected = run(source, "--symbol", "real")
    assert "let value = 1;" in selected, selected
    assert "fn next" not in selected, selected
print("CLI smoke passed: comment-aware outline and complete symbol selection")
