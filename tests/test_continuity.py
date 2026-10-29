import json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ContinuityTests(unittest.TestCase):
 def test_arrivals_and_document_read_precede_reveals(self):
  nodes=json.loads((ROOT/'episodes/ep01/episode_01.json').read_text())['nodes']
  for target,prior in [('gu','gu_arrival'),('rival','rival_arrival'),('name','open_file')]:
   incoming={n['id'] for n in nodes for c in n['choices'] if c['next']==target}
   self.assertEqual(incoming,{prior})
 def test_setup_remains_available_without_language_hints(self):
  nodes={n['id']:n for n in json.loads((ROOT/'episodes/ep01/episode_01.json').read_text())['nodes']}
  for key in ['start','enter_shop','served','explore','gu','billion','rival_arrival','open_file','name','sms']:
   self.assertTrue(nodes[key]['context']['zh']);self.assertTrue(nodes[key]['context']['en'])
