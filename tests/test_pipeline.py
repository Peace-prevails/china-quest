import sys,unittest,tempfile,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from story import Story
from validate_story import validate
from generate_assets import parser,run,image_type
class StoryTests(unittest.TestCase):
 def test_graph(self):validate()
 def choose(self,s,text):return s.choose(next(c['id'] for c in s.view()['choices'] if c['zh']==text))
 def test_all_order_and_plot_branches(self):
  for food,price in [('牛肉面',28),('炸酱面',24)]:
   for spice in [True,False]:
    for water in [True,False]:
     for reaction in ['我要。','我不要。','这是什么？','这是谁的？']:
      for alignment in ['你是谁？','我不认识他。','我也不认识你。','文件给我。']:
       s=Story()
       for c in ['看招牌','坐下','菜单',food,'我要这个。','我不要这个。',food,'我要这个。','我听不懂。','我要这个。','我听不懂。','我要辣。' if spice else '我不要辣。','我要水。' if water else '我不要水。','谢谢','这个多少钱？']:self.choose(s,c)
       self.assertEqual(s.values()['total'],price+3*water)
       self.choose(s,'好');self.choose(s,'红色文件袋');self.choose(s,'看一眼');self.choose(s,'继续吃面');self.choose(s,'看着他');self.choose(s,'我听不懂。');self.choose(s,'继续');self.choose(s,reaction);self.choose(s,'继续');self.choose(s,'看向门口');self.choose(s,alignment);self.choose(s,'继续');self.choose(s,'看她的反应');self.choose(s,'谁死了？');self.choose(s,'看手机');self.choose(s,'结束')
       self.assertEqual(s.current,'end');self.assertTrue(s.state['saw_red_envelope']);self.assertIs(s.state['spicy'],spice)
 def test_paid_guard(self):
  with self.assertRaises(ValueError):run(parser().parse_args([]))
 def test_invalid_image(self):
  with self.assertRaises(ValueError):image_type(b'<html>oops</html>')
if __name__=='__main__':unittest.main()
