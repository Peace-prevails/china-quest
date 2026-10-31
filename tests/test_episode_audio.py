import pathlib,sys,unittest,subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from episode_audio import inventory,key,LESSONS
class AudioTests(unittest.TestCase):
 def test_order_variants_and_spoken_roles(self):
  rows=inventory();lookup={(r['role'],r['text']):r for r in rows}
  for price in [24,27,28,31]:self.assertIn(('owner',f'一共{price}元。'),lookup)
  for food in ['牛肉面','炸酱面']:self.assertIn(('owner',f'你要{food}？'),lookup)
  for text in LESSONS:self.assertIn(('narrator',text),lookup)
  rival=next(r for r in rows if 'node:rival' in r['sources']);self.assertEqual(rival['spoken_text'],'等等！不能给你！他认错人了！')
  owner=next(r for r in rows if 'node:gu_eat' in r['sources']);self.assertEqual(owner['role'],'owner');self.assertNotIn('老板娘：',owner['spoken_text'])
  self.assertEqual(len(rows),len({r['id'] for r in rows}))
 def test_player(self):
  p=subprocess.run(['node','tests/audio_player.mjs'],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_parallel_requests_keep_all_budget_entries(self):
  import tempfile,json,base64,os,time
  from concurrent.futures import ThreadPoolExecutor
  from unittest.mock import patch
  from types import SimpleNamespace
  from contextlib import redirect_stdout
  import io,generate_voice_samples as voice
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'data/production_budget.json').write_text(json.dumps({'approved_total_rmb':40,'entries':{}}))
   def response(args,**kwargs):
    time.sleep(.02)
    pathlib.Path(args[args.index('--output')+1]).write_text(json.dumps({'audio':base64.b64encode(b'x'*1500).decode(),'original_duration':6,'duration':6}))
    return SimpleNamespace(stdout='200',returncode=0)
   with patch.object(voice,'ROOT',root),patch.object(voice,'dotenv'),patch.dict(os.environ,{'VOLC_VOICE_API_KEY':'offline-fixture'}),patch.object(voice.subprocess,'run',side_effect=response),redirect_stdout(io.StringIO()):
    with ThreadPoolExecutor(max_workers=4) as pool:
     futures=[pool.submit(voice.run,'gu',True,custom=('fixture','fixture',str(i)),output_folder=root/'clips'/str(i),short_line=True) for i in range(4)]
     for future in futures:future.result()
   budget=json.loads((root/'data/production_budget.json').read_text());self.assertEqual(len(budget['entries']),4);self.assertAlmostEqual(budget['reserved_and_estimated_rmb'],.4)
   self.assertTrue(all(r['status']=='generated' for r in budget['entries'].values()))
