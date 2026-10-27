"""Offline HTTP integration: no Ark request, no paid generation, temporary fixtures."""
import base64
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import generate_assets as generation
import review_assets as review
from common import read

# A real tiny PNG is used strictly as a transport fixture, never as production art.
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6F8AAAAASUVORK5CYII=')


class HTTPIntegrationTests(unittest.TestCase):
    def test_request_download_review_and_reference(self):
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                received.append({'path':self.path,'auth':self.headers.get('Authorization'),'payload':payload})
                body=json.dumps({'data':[{'b64_json':base64.b64encode(PNG).decode()}]}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                root=pathlib.Path(temp).resolve()
                assets=[{'id':'BG','category':'backgrounds','model':None,'prompt':'Fixture background','size':'2K','reference_assets':[]}, {'id':'DERIVED','category':'backgrounds','model':None,'prompt':'Fixture derived image','size':'2K','reference_assets':['BG']}]
                argv=['--model','fixture-endpoint','--unit-price-rmb','1','--max-spend-rmb','1','--confirm-paid','--max-images','1']
                # Localhost only. Real request_json and base64 download path are exercised.
                with patch.object(generation,'ROOT',root),patch.object(review,'ROOT',root),patch.object(generation,'API',f'http://127.0.0.1:{server.server_port}/images/generations'),patch.object(generation,'manifest',return_value={'assets':assets}),patch.dict(generation.os.environ,{'ARK_API_KEY':'offline-fixture-key'}),redirect_stdout(io.StringIO()):
                    generation.run(generation.parser().parse_args(argv+['--asset-id','BG']))
                    record=next((root/'assets/generated/backgrounds/BG').rglob('record.json'))
                    self.assertEqual((root/read(record)['path']).read_bytes(),PNG)
                    review.review(record,'approved','Transport fixture only')
                    generation.run(generation.parser().parse_args(argv+['--asset-id','DERIVED']))
                    review.gallery()
                    self.assertTrue((root/'local/review/index.html').exists())
                    records=list(root.rglob('record.json'))
                    self.assertEqual(len(records),2)
                    derived=next(r for r in records if read(r)['asset_id']=='DERIVED')
                    self.assertEqual(read(derived)['references'][0]['asset_id'],'BG')
                self.assertEqual(len(received),2)
                self.assertEqual(received[0]['auth'],'Bearer offline-fixture-key')
                self.assertEqual(received[0]['path'],'/images/generations')
                self.assertEqual(received[1]['payload']['image'],['data:image/png;base64,'+base64.b64encode(PNG).decode()])
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)
