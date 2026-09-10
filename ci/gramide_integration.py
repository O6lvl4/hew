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
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'sample.py'
 p.write_text('class Outer:\n @decorate\n def method(self):\n  def helper(): return "日本語"\n  return helper()\n\n # comment between declarations\n class Inner:\n  async def method(self): return 2\n\ndef method(): return 3\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'Outer.Inner.method' in outline,outline
 for name,include,exclude in [('Outer.method','@decorate','class Inner'),('Outer.method.helper','日本語','return helper()'),('Outer.Inner.method','async def method','return 3')]:
  body=subprocess.check_output([str(hew),str(p),'--symbol',name],env=env,text=True)
  assert include in body and exclude not in body,(name,body)
 p=p.with_suffix('.pyi');p.write_text('class Stub:\n def method(self) -> int: ...\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'Stub.method' in outline,outline
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'editing.py'
 p.write_text('class Box:\n def good(self): return 1\n def bad(self):\n  x = "unfinished\n def next(self): return 2\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide-recovered)' in outline and 'Box.good' in outline and 'Box.next' in outline and 'Box.bad' not in outline,outline
 for name,text in [('Box.good','return 1'),('Box.next','return 2')]:
  body=subprocess.check_output([str(hew),str(p),'--symbol',name],env=env,text=True)
  assert text in body and 'unfinished' not in body and 'gramide-recovered' in body,(name,body)
 p.write_text('if broken\n def phantom(): pass\ndef real(): pass\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide-recovered)' in outline and 'real' in outline and 'phantom' not in outline,outline
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'editing.py'
 for family in ['f','t']:
  p.write_text('class Box:\n def good(self): return 1\n def bad(self):\n  x = '+family+'"{value}unfinished\n def next(self): return 2\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide-recovered)' in outline and 'Box.good' in outline and 'Box.next' in outline and 'Box.bad' not in outline,outline
  for name,text in [('Box.good','return 1'),('Box.next','return 2')]:
   body=subprocess.check_output([str(hew),str(p),'--symbol',name],env=env,text=True)
   assert text in body and 'unfinished' not in body and 'gramide-recovered' in body,(name,body)
  p.write_text('def before(): return 1\nx = '+family+'"""unfinished\ndef phantom(): pass\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide-recovered)' in outline and 'before' in outline and 'phantom' not in outline,outline
print('Real gramide → hew integration passed')
