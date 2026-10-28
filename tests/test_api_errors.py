import io
from contextlib import redirect_stdout
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import generate_assets as g
from common import read


class APIErrorTests(unittest.TestCase):
    def error(self,status,code,message='Model unavailable'):
        return HTTPError(g.API,status,'test',{'x-request-id':'fixture-request'},io.BytesIO(json.dumps({'error':{'code':code,'message':message}}).encode()))

    def test_provider_error_preserved_and_key_redacted(self):
        details=g.http_error_details(self.error(401,'AuthenticationError','Invalid secret-test-key'), 'secret-test-key')
        self.assertEqual(details['status'],401)
        self.assertEqual(details['code'],'AuthenticationError')
        self.assertNotIn('secret-test-key',json.dumps(details))
        self.assertEqual(details['request_id'],'fixture-request')

    def test_non_json_error_is_bounded(self):
        error=HTTPError(g.API,502,'test',{},io.BytesIO(b'upstream failure'*1000))
        details=g.http_error_details(error)
        self.assertLessEqual(len(details['body_excerpt']),1000)

    def test_model_not_open_is_a_recorded_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp).resolve()
            asset={'id':'TEST','category':'props','prompt':'fixture','size':'2K','model':None,'reference_assets':[]}
            args=g.parser().parse_args(['--model','fixture-model','--unit-price-rmb','0.12','--max-spend-rmb','40','--confirm-paid'])
            with patch.object(g,'ROOT',root),patch.object(g,'manifest',return_value={'assets':[asset]}),patch.dict(os.environ,{'ARK_API_KEY':'fixture-key'}),patch.object(g,'request_json',side_effect=self.error(404,'ModelNotOpen')) as post,redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):g.run(args)
                record=read(next(root.rglob('record.json')))
                self.assertEqual(record['status'],'request_rejected')
                self.assertEqual(record['http_error']['code'],'ModelNotOpen')
                with self.assertRaisesRegex(ValueError,'fix the recorded cause'):g.run(args)
                self.assertEqual(post.call_count,1)

    def test_server_failure_keeps_uncertain_status(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp).resolve()
            asset={'id':'TEST','category':'props','prompt':'fixture','size':'2K','model':None,'reference_assets':[]}
            args=g.parser().parse_args(['--model','fixture-model','--unit-price-rmb','0.12','--max-spend-rmb','40','--confirm-paid'])
            with patch.object(g,'ROOT',root),patch.object(g,'manifest',return_value={'assets':[asset]}),patch.dict(os.environ,{'ARK_API_KEY':'fixture-key'}),patch.object(g,'request_json',side_effect=self.error(503,'ServiceUnavailable')),redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):g.run(args)
                self.assertEqual(read(next(root.rglob('record.json')))['status'],'uncertain')
