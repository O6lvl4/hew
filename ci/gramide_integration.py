"""Exercise the linked grammars through hew itself, not a mock provider."""
from pathlib import Path
import os,subprocess,tempfile
hew=Path(__file__).resolve().parents[1]/'hew'
env=dict(os.environ,HEW_OUTLINE_BIN='')
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
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'editing.py'
 for opening in ['(','[','{']:
  # a bracket left open ends where a statement begins at the opener's
  # indentation or less: `next` is a method again; one written deeper is not
  p.write_text('class Box:\n def good(self): return 1\n x = '+opening+'\n def next(self): pass\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide-recovered)' in outline and 'Box.good' in outline and 'Box.next' in outline,outline
  body=subprocess.check_output([str(hew),str(p),'--symbol','Box.good'],env=env,text=True)
  assert 'return 1' in body and 'next' not in body and 'gramide-recovered' in body,body
  p.write_text('class Box:\n def good(self): return 1\n x = '+opening+'\n     def phantom(self): pass\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide-recovered)' in outline and 'Box.good' in outline and 'phantom' not in outline,outline
 p.write_text('def before(): pass\nx = (1)\ndef after(): pass\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'after' in outline,outline
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'editing.py'
 for bad in [')',']','}','$','`','?']:
  p.write_text('class Box:\n def good(self): return 1\n '+bad+'\n def next(self): return 2\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide-recovered)' in outline and 'Box.good' in outline and 'Box.next' in outline,outline
  for name,text in [('Box.good','return 1'),('Box.next','return 2')]:
   body=subprocess.check_output([str(hew),str(p),'--symbol',name],env=env,text=True)
   assert text in body and 'gramide-recovered' in body,(name,body)
 p.write_text('def broken$():\n def phantom(): pass\ndef real(): pass\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide-recovered)' in outline and 'real' in outline and 'phantom' not in outline,outline
with tempfile.TemporaryDirectory() as tmp:
 for ext in ['js','mjs','cjs']:
  p=Path(tmp)/('sample.'+ext)
  p.write_text('export default class Widget extends Base {\n  static #n = 0\n  get size() { return /re/.test(this.x) ? 1 : 2 }\n  static of(...xs) { return new Widget(xs[0]) }\n}\nexport const helper = async (a, b = 2) => a ** b\nconst handlers = { onClick() { return `x${1}y` } }\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide)' in outline and 'Widget.size' in outline and 'function  helper' in outline and 'handlers.onClick' in outline,outline
  body=subprocess.check_output([str(hew),str(p),'--symbol','Widget.of'],env=env,text=True)
  assert 'new Widget' in body and 'helper' not in body and '(gramide)' in body,body
  body=subprocess.check_output([str(hew),str(p),'--symbol','helper'],env=env,text=True)
  assert 'export const helper' in body and 'onClick' not in body,body
 p=Path(tmp)/'editing.js'
 p.write_text('export class Box {\n  read() { return 1 }\n  broken( {\n  also(x) { return x }\n}\nexport function f() {}\nfunction g( {\nfunction h() {}\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide-recovered)' in outline and 'Box.read' in outline and 'Box.also' in outline and 'function  f' in outline and 'function  h' in outline and 'broken' not in outline and ' g ' not in outline,outline
 for name,text in [('Box.also','return x'),('h','function h')]:
  body=subprocess.check_output([str(hew),str(p),'--symbol',name],env=env,text=True)
  assert text in body and 'broken' not in body and 'gramide-recovered' in body,(name,body)
with tempfile.TemporaryDirectory() as tmp:
 for ext in ['ts','mts','cts']:
  p=Path(tmp)/('sample.'+ext)
  p.write_text('export interface Shape { area(): number }\nexport abstract class Box<T> implements Shape {\n  constructor(private readonly x: T) {}\n  abstract area(): number\n  size(): number { return (this.x as unknown as number) ** 2 }\n}\nexport const make = <T,>(x: T): Box<T> => new Impl<T>(x)\nexport namespace ns { export type Id<T> = T extends infer U ? U : never }\n')
  outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
  assert '; gramide)' in outline and 'Shape.area' in outline and 'Box.constructor' in outline and 'function  make' in outline and 'namespace ns' in outline and 'type      ns.Id' in outline,outline
  body=subprocess.check_output([str(hew),str(p),'--symbol','Box.size'],env=env,text=True)
  assert '** 2' in body and 'constructor' not in body and '(gramide)' in body,body
 p=Path(tmp)/'view.tsx'
 p.write_text('export function View<T>({ items }: { items: T[] }) {\n  return <ul>{items.map((i) => <li key={String(i)}>{i}</li>)}</ul>\n}\nexport const pick = <T,>(a: T) => <Select<T> value={a} />\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'function  View' in outline and 'function  pick' in outline,outline
 p=Path(tmp)/'view.jsx'
 p.write_text('export function View({ items }) {\n  return <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>\n}\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide)' in outline and 'function  View' in outline,outline
 p=Path(tmp)/'editing.ts'
 p.write_text('export class Box {\n  read(): number { return 1 }\n  broken(: {\n  also(x: string) { return x }\n}\nexport function f(): void {}\n')
 outline=subprocess.check_output([str(hew),'outline',str(p)],env=env,text=True)
 assert '; gramide-recovered)' in outline and 'Box.read' in outline and 'Box.also' in outline and 'function  f' in outline and 'broken' not in outline,outline
 body=subprocess.check_output([str(hew),str(p),'--symbol','Box.also'],env=env,text=True)
 assert 'return x' in body and 'broken' not in body and 'gramide-recovered' in body,body
print('Linked grammars passed: Rust envelopes, Python nesting and stubs, JavaScript, JSX, TypeScript and TSX declarations, recovered declarations around every kind of damage')
