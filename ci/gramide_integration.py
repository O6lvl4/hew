"""Exercise the real parser/reader contract, not a mock provider."""
from pathlib import Path
import os,subprocess,tempfile
hew=Path(__file__).resolve().parents[1]/'hew'
gramide=Path(os.environ['GRAMIDE_BIN']).resolve()
env=dict(os.environ,PATH=str(gramide.parent)+os.pathsep+os.environ.get('PATH',''),HEW_OUTLINE_BIN='')
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'sample.rs'
 p.write_text('#[inline]\npub fn\nreal() {\n let raw = r#"}\nfn phantom() {}\n"#;\n}\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'L1-7' in outline and 'phantom' not in outline,outline
 body=subprocess.check_output([str(hew),str(p),'--symbol','real'],env=env,text=True)
 assert '#[inline]' in body and 'pub fn' in body and '7│ }' in body,body
print('Real gramide → hew integration passed')
