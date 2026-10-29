import pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import generate_assets as generation
import review_assets as review
from common import digest,write,read
from production_budget import reserve,synchronize
class ScopeAndBudgetTests(unittest.TestCase):
 def test_identity_only_is_saved_and_loaded(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp).resolve();data=b'\x89PNG\r\n\x1a\nfixture';image=root/'assets/generated/characters/OWNER/test/image.png';image.parent.mkdir(parents=True);image.write_bytes(data)
   record=image.with_name('record.json');write(record,{'status':'generated','category':'characters','asset_id':'OWNER','path':str(image.relative_to(root)),'sha256':digest(data)})
   with patch.object(review,'ROOT',root),patch.object(generation,'ROOT',root):
    review.review(record,'approved','User approves person only','identity_only')
    ref,_=generation.reference('OWNER',{})
    self.assertEqual(ref['scope'],'identity_only')
    self.assertTrue(read(root/'assets/approved/OWNER/reference.json')['ignore_background'])
 def test_cumulative_reserve_survives_missing_images_and_rejects_overspend(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);write(root/'data/production_budget.json',{'approved_total_rmb':0.24,'entries':{}})
   reserve(root,'a','A','fixture-model',0.12);reserve(root,'b','B','fixture-model',0.12)
   with self.assertRaises(ValueError):reserve(root,'c','C','fixture-model',0.12)
   with self.assertRaises(ValueError):reserve(root,'a','A','fixture-model',0.12)
   self.assertEqual(synchronize(root)['remaining_estimate_rmb'],0)
 def test_identity_instruction_reaches_provider_payload(self):
  asset={'id':'CG','category':'cg','model':None,'prompt':'Target scene','size':'2K','reference_assets':['OWNER']}
  args=generation.parser().parse_args(['--model','fixture','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid'])
  with tempfile.TemporaryDirectory() as temp, patch.object(generation,'ROOT',pathlib.Path(temp)),patch.object(generation,'manifest',return_value={'assets':[asset]}),patch.object(generation,'reference',return_value=({'asset_id':'OWNER','scope':'identity_only','sha256':'fixture','path':'fixture.png'},'data:image/png;base64,fixture')),patch.dict(generation.os.environ,{'ARK_API_KEY':'fixture'}),patch.object(generation,'request_json',return_value={'data':[{'b64_json':'iVBORw0KGgo='}]}) as post:
   generation.run(args)
   self.assertIn('完全忽略该图背景',post.call_args.args[0]['prompt'])
 def test_identity_cannot_define_background(self):
  asset={'id':'BG','category':'backgrounds','model':None,'prompt':'Target scene','size':'2K','reference_assets':['OWNER']}
  args=generation.parser().parse_args(['--model','fixture','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid'])
  with tempfile.TemporaryDirectory() as temp,patch.object(generation,'ROOT',pathlib.Path(temp)),patch.object(generation,'manifest',return_value={'assets':[asset]}),patch.object(generation,'reference',return_value=({'asset_id':'OWNER','scope':'identity_only'},'fixture')),patch.dict(generation.os.environ,{'ARK_API_KEY':'fixture'}),patch.object(generation,'request_json') as post:
   with self.assertRaisesRegex(ValueError,'cannot define a background'):generation.run(args)
   post.assert_not_called()
 def test_edit_uses_archived_target_and_rejects_modified_image(self):
  asset={'id':'CG','category':'cg','model':'fixture','prompt':'Original generation','size':'2K','reference_assets':[]}
  args=generation.parser().parse_args(['--dry-run','--edit-target','assets/candidates/CG/v1.png','--edit-prompt-file','edit.txt'])
  import io,json
  with tempfile.TemporaryDirectory() as temp,patch.object(generation,'ROOT',pathlib.Path(temp)),patch.object(generation,'manifest',return_value={'assets':[asset]}):
   root=pathlib.Path(temp);target=root/args.edit_target;target.parent.mkdir(parents=True);target.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
   write(target.with_suffix('.json'),{'asset_id':'CG','sha256':digest(target.read_bytes())});(root/'edit.txt').write_text('Change expression only')
   output=io.StringIO()
   with patch('sys.stdout',output):generation.run(args)
   result=json.loads(output.getvalue());self.assertEqual(result['prompt'],'Change expression only');self.assertEqual(result['references'][0]['scope'],'edit_target')
   target.write_bytes(b'\x89PNG\r\n\x1a\ntampered')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):generation.run(args)
