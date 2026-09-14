"""Check the external provider contract and lossless bounded reads."""
from pathlib import Path
import json,os,subprocess,tempfile,sys
BIN=Path(__file__).resolve().parents[1]/'hew'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);p=root/'sample.rs';p.write_text('pub fn\nreal() {\n  let x = 1;\n}\n')
 provider=root/'outline'
 payload={'lang':'rust','total_lines':4,'symbols':[{'kind':'function','name':'real','start':1,'end':4}]}
 env=dict(os.environ,HEW_OUTLINE_BIN=str(provider))
 def install(data,code=0):
  provider.write_text('#!'+sys.executable+'\nimport sys\nprint('+repr(json.dumps(data))+')\nsys.exit('+str(code)+')\n');provider.chmod(0o755)
 def run(*args,e=env):return subprocess.check_output([str(BIN),*map(str,args)],env=e,text=True)
 # An explicit provider wins over the linked grammar, and says so.
 install(payload);out=run('outline',p);assert '; provider)' in out and 'L1-4' in out,out
 selected=run(p,'--symbol','real');assert 'pub fn' in selected and 'let x = 1;' in selected,selected
 # A provider that breaks the contract is ignored; the linked grammar answers instead.
 for bad in [{},dict(payload,total_lines=99),dict(payload,lang='go'),dict(payload,symbols=[{'kind':'fn','name':'bad','start':0,'end':9}])]:
  install(bad);assert '; gramide)' in run('outline',p)
 install(payload,1);assert '; gramide)' in run('outline',p)
 # A language no grammar knows falls back to the provider, then to heuristics.
 future=root/'sample.future';future.write_text('custom declaration\n')
 custom={'lang':'future','total_lines':1,'symbols':[{'kind':'function','name':'future_symbol','start':1,'end':1}]}
 install(custom);assert 'future_symbol' in run('outline',future)
 assert '; heuristic)' in run('outline',future,e=dict(os.environ,HEW_OUTLINE_BIN=''))
 # Source bytes are not reconstructed from split lines or display output.
 text='日本語\r\n'+('a'*350)+'\nlast line'
 p.write_bytes(text.encode())
 for limit in [3,1000]:
  d=json.loads(run('read-json',p,'--max-chars',limit))
  assert d['content']==text[:limit] and d['complete']==(len(text)<=limit),d
  assert d['total_chars']==len(text)
 # --version names what was linked.
 version=run('--version').splitlines()
 assert version[0].startswith('hew ') and any(l.startswith('gramide ') for l in version) and any('gramide-python' in l for l in version),version
print('Provider and lossless-read contracts passed')
