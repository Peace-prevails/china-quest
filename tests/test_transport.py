import json,pathlib,sys,types,unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import generate_assets as g
class CurlTransportTests(unittest.TestCase):
 def transport(self,status,body,returncode):
  def run(command,**kwargs):
   self.assertNotIn('secret-fixture-key',' '.join(command))
   pathlib.Path(command[command.index('--output')+1]).write_bytes(body)
   pathlib.Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 '+str(status)+' Status\nX-Request-Id: fixture-request\n\n')
   return types.SimpleNamespace(stdout=str(status),stderr='',returncode=returncode)
  return run
 def test_success_and_no_secret_in_argv(self):
  with patch.object(g.subprocess,'run',side_effect=self.transport(200,b'{"data":[]}',0)):
   self.assertEqual(g.curl_request_json({'model':'fixture'},'secret-fixture-key'),{'data':[]})
 def test_provider_error_preserved(self):
  with patch.object(g.subprocess,'run',side_effect=self.transport(404,b'{"error":{"code":"ModelNotOpen"}}',22)):
   with self.assertRaises(HTTPError) as raised:g.curl_request_json({},'secret-fixture-key')
   details=g.http_error_details(raised.exception,'secret-fixture-key')
   self.assertEqual(details['code'],'ModelNotOpen');self.assertEqual(details['request_id'],'fixture-request')
 def test_network_error_does_not_retry(self):
  with patch.object(g.subprocess,'run',side_effect=self.transport(0,b'',35)) as call:
   with self.assertRaises(URLError):g.curl_request_json({},'secret-fixture-key')
   self.assertEqual(call.call_count,1)
