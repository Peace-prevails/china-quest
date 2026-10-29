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
   route=['面馆在哪里？','我听不懂','往前走','菜单',food,'我要这个。','我不要这个。',food,'我要这个。','我听不懂。','我要这个。','我听不懂。','我要辣。' if spice else '我不要辣。','我要水。' if water else '我不要水。','谢谢','这个多少钱？','好','红色文件袋','看一眼','继续吃面','我听不懂。','继续',reaction,'继续',alignment,'继续','谁死了？','看手机','结束']
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
 def test_public_package_contains_only_approved_assets(self):
  output=build();assets=read(output/'assets.json');self.assertEqual(len(assets),12)
  for path in assets.values():self.assertTrue((output/path).is_file())
  self.assertFalse((output/'.env').exists());self.assertFalse((output/'scripts').exists())
