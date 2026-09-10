"""Check provider selection, contract failures and lossless bounded reads."""
from pathlib import Path
import json,os,subprocess,tempfile,sys
BIN=Path(__file__).resolve().parents[1]/'hew'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);p=root/'sample.rs';p.write_text('pub fn\nreal() {\n  let x = 1;\n}\n')
 bindir=root/'bin';bindir.mkdir();provider=bindir/'gramide'
 payload={'schema_version':1,'complete':True,'lang':'rust','total_lines':4,'symbols':[{'kind':'function','name':'real','start':1,'end':4}]}
 env=dict(os.environ,PATH=str(bindir),HEW_OUTLINE_BIN='')
 def install(data,code=0):
  provider.write_text('#!'+sys.executable+'\nimport sys\nprint('+repr(json.dumps(data))+')\nsys.exit('+str(code)+')\n');provider.chmod(0o755)
 def run(*args):return subprocess.check_output([str(BIN),*map(str,args)],env=env,text=True)
 install(payload);out=run('outline',p);assert '; gramide)' in out and 'L1-4' in out,out
 selected=run(p,'--symbol','real');assert 'pub fn' in selected and 'let x = 1;' in selected,selected
 for bad in [{},dict(payload,complete=False),dict(payload,total_lines=99),dict(payload,schema_version=2),dict(payload,symbols=[{'kind':'fn','name':'bad','start':0,'end':9}])]:
  install(bad);assert '; heuristic)' in run('outline',p)
 install(payload,1);assert '; heuristic)' in run('outline',p)
 # Source bytes are not reconstructed from split lines or display output.
 text='日本語\r\n'+('a'*350)+'\nlast line'
 p.write_bytes(text.encode())
 for limit in [3,1000]:
  d=json.loads(run('read-json',p,'--max-chars',limit))
  assert d['content']==text[:limit] and d['complete']==(len(text)<=limit),d
  assert d['total_chars']==len(text)
 # Discovery enables languages unknown to hew, including directory traversal.
 future=root/'sample.future';future.write_text('custom declaration\n')
 manifest={'schema_version':1,'packages':[{'extensions':['.future'],'capabilities':['symbols']}]}
 custom={'schema_version':1,'complete':True,'lang':'future','total_lines':1,'symbols':[{'kind':'function','name':'future_symbol','start':1,'end':1}]}
 def install_discovery(metadata):
  provider.write_text('#!'+sys.executable+'\nimport sys\nprint('+repr(json.dumps(metadata))+' if sys.argv[1] == "languages" else '+repr(json.dumps(custom))+')\n');provider.chmod(0o755)
 install_discovery(manifest)
 assert 'future_symbol' in run('outline',future)
 assert 'future_symbol' in run('outline',root)
 for metadata in [{},dict(manifest,schema_version=2),{'schema_version':1,'packages':[{'extensions':['.future'],'capabilities':['check']}]}]:
  install_discovery(metadata)
  assert 'future_symbol' not in run('outline',root)
 # Recovered output is accepted only from its explicit command and policy.
 q=root/'editing.py';source='def good(): pass\nx =\ndef next(): pass\n';q.write_text(source)
 start=source.index('x =')
 recovery={'schema_version':1,'complete':False,'recovery_policy':'error-free-declarations-v1','lang':'python','total_lines':3,
           'diagnostic':'invalid statement','errors':[{'start':2,'end':2,'start_byte':start,'end_byte':start+3}],
           'symbols':[{'kind':'function','name':'good','start':1,'end':1,'start_byte':0,'end_byte':source.index('\n')}]}
 def install_recovery(data):
  provider.write_text('#!'+sys.executable+'\nimport sys\nif sys.argv[1] != "symbols-recovered": sys.exit(1)\nprint('+repr(json.dumps(data))+')\n');provider.chmod(0o755)
 install_recovery(recovery)
 assert '; gramide-recovered)' in run('outline',q)
 for bad in [dict(recovery,recovery_policy='unknown'),dict(recovery,errors=[]),dict(recovery,diagnostic=''),
             dict(recovery,complete=None),dict(recovery,complete=True),dict(recovery,schema_version=2),dict(recovery,total_lines=99),
             dict(recovery,errors=[{'start':2,'end':4,'start_byte':start,'end_byte':start+3}]),
             dict(recovery,errors=recovery['errors']*2),
             dict(recovery,symbols=[dict(recovery['symbols'][0],start_byte=start,end_byte=start+1)]),
             dict(recovery,symbols=[dict(recovery['symbols'][0],start_byte=-1)])]:
  install_recovery(bad);out=run('outline',q);assert '; heuristic)' in out,(bad,out)
print('Provider, language discovery and lossless-read contracts passed')
