import sys,unittest,tempfile,pathlib,json
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import generate_assets as g
import review_assets as r
from common import read
class AssetTests(unittest.TestCase):
 def test_download_resume_and_review(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp).resolve()
   args=g.parser().parse_args(['--asset-id','TEST','--model','console-id','--max-images','1','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid'])
   asset={'id':'TEST','category':'props','prompt':'Test','size':'2K','model':None,'reference_assets':[]}
   with patch.object(g,'ROOT',root),patch.object(r,'ROOT',root),patch.object(g,'manifest',return_value={'assets':[asset]}),patch.dict(g.os.environ,{'ARK_API_KEY':'test'}),patch.object(g,'request_json',return_value={'data':[{'url':'https://example.test/image'}]}) as post,patch.object(g,'download',side_effect=OSError):
    with self.assertRaises(SystemExit):g.run(args)
    record=next(root.rglob('record.json'));self.assertEqual(read(record)['status'],'download_failed')
    with patch.object(g,'download',return_value=b'\x89PNG\r\n\x1a\nfixture'):
     args.resume=True;g.run(args);g.run(args)
    self.assertEqual(post.call_count,1)
    r.review(record,'approved','Test approval')
    self.assertTrue((root/'assets/approved/TEST/reference.json').exists())
    ref,_=g.reference('TEST',{});self.assertEqual(ref['asset_id'],'TEST')
 def test_ambiguous_post_never_retries(self):
  with tempfile.TemporaryDirectory() as temp:
   args=g.parser().parse_args(['--asset-id','TEST','--model','console-id','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid'])
   with patch.object(g,'ROOT',pathlib.Path(temp)),patch.object(g,'manifest',return_value={'assets':[{'id':'TEST','category':'props','prompt':'test','size':'2K','reference_assets':[]}]}),patch.dict(g.os.environ,{'ARK_API_KEY':'test'}),patch.object(g,'request_json',side_effect=TimeoutError) as post:
    with self.assertRaises(SystemExit):g.run(args)
    with self.assertRaises(ValueError):g.run(args)
    self.assertEqual(post.call_count,1)
if __name__=='__main__':unittest.main()

class RecoveryTests(unittest.TestCase):
 def test_completed_cache_counts_towards_selection_limit(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp).resolve()
   assets=[{'id':aid,'category':'props','model':None,'prompt':aid,'size':'2K','reference_assets':[]} for aid in ['FIRST','SECOND']]
   args=g.parser().parse_args(['--model','test-model','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid','--max-images','1'])
   with patch.object(g,'ROOT',root),patch.object(g,'manifest',return_value={'assets':assets}),patch.dict(g.os.environ,{'ARK_API_KEY':'test'}),patch.object(g,'request_json',return_value={'data':[{'b64_json':'iVBORw0KGgo='}]}) as post:
    g.run(args);args.resume=True;g.run(args)
    self.assertEqual(post.call_count,1)
    self.assertFalse((root/'assets/generated/props/SECOND').exists())

 def test_saved_response_after_crash_never_reposts(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp).resolve()
   args=g.parser().parse_args(['--asset-id','TEST','--model','test-model','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid'])
   asset={'id':'TEST','category':'props','prompt':'Test','size':'2K','reference_assets':[]}
   with patch.object(g,'ROOT',root),patch.object(g,'manifest',return_value={'assets':[asset]}),patch.dict(g.os.environ,{'ARK_API_KEY':'test'}),patch.object(g,'request_json',return_value={'data':[{'b64_json':'iVBORw0KGgo='}]}) as post:
    g.run(args)
    record=next(root.rglob('record.json'));data=read(record);data['status']='requesting';g.write(record,data)
    g.run(args)
    self.assertEqual(post.call_count,1)
    self.assertEqual(read(record)['status'],'generated')

 def test_invalid_budget_is_rejected_before_request(self):
  for value in ['nan','inf','-1','0']:
   args=g.parser().parse_args(['--model','test-model','--unit-price-rmb',value,'--max-spend-rmb','1','--confirm-paid'])
   with patch.object(g,'request_json') as post:
    with self.assertRaises(ValueError):g.run(args)
    post.assert_not_called()
