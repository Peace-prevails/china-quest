import itertools,json,pathlib,subprocess,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,read
from story import Story
from build_web import build
class WebTests(unittest.TestCase):
 def test_browser_matches_python_story(self):
  cases=[]
  for food,spice,water,reaction,alignment in itertools.product(['牛肉面','炸酱面'],[True,False],[True,False],['我要。','我不要。','这是什么？','这是谁的？'],['你是谁？','我不认识他。','我也不认识你。','文件给我。']):
   s=Story();ids=[]
   route=['面馆在哪里？','我听不懂','往前走','坐下','菜单',food,'我要这个。','我不要这个。',food,'我要这个。','我听不懂。','我要这个。','我听不懂。','我要辣。' if spice else '我不要辣。','我要水。' if water else '我不要水。','谢谢','这个多少钱？','好','门外的动静','看一眼','继续吃面','看着他','我听不懂。','继续',reaction,'继续','看向门口',alignment,'继续','看她的反应','谁死了？','看手机','结束']
   for label in route:
    choice=next(c for c in s.view()['choices'] if c['zh']==label);ids.append(choice['id']);s.choose(choice['id'])
   cases.append({'choices':ids,'expected':{'version':1,'episode_id':s.data['id'],'current':s.current,'story':s.state,'learning':s.learning}})
  result=subprocess.run(['node','tests/web_engine.mjs'],cwd=ROOT,input=json.dumps({'data':Story().data,'cases':cases}),text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_choice_and_dynamic_dialogue_pinyin_coverage(self):
  p=read(ROOT/'web/pinyin.json');s=Story()
  for node in s.data['nodes']:
   for choice in node['choices']:self.assertTrue(p.get(choice['zh']),choice['zh'])
  for food,water in itertools.product(['beef','zhajiang'],[True,False]):
   s.state.update(item_selected=food,wants_water=water)
   for node in s.data['nodes']:
    s.current=node['id'];self.assertTrue(p.get(s.view()['zh']),s.view()['zh'])
 def test_public_package_contains_verified_assets(self):
  output=build();assets=read(output/'assets.json');self.assertTrue({a['id'] for a in read(ROOT/'episodes/ep01/approved_asset_manifest.json')['assets']}<=set(assets))
  for path in assets.values():self.assertTrue((output/path).is_file())
  self.assertFalse((output/'.env').exists());self.assertFalse((output/'scripts').exists())
 def test_speaker_and_expression_shots(self):
  result=subprocess.run(['node','tests/web_visuals.mjs'],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_visual_preview_covers_every_shot(self):
  revision=read(ROOT/'episodes/ep01/visual_revision.json')
  available=set(revision['assets'])|{a['id'] for a in read(ROOT/'episodes/ep01/approved_asset_manifest.json')['assets']}
  for node,shot in read(ROOT/'web/scene_visuals.json').items():self.assertIn(shot['asset'],available,node)

 def test_learning_review_and_old_save_migration(self):
  result=subprocess.run(["node","tests/learning_review.mjs"],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
