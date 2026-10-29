"""Serve the packaged public game, never the repository or credential files."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from build_web import build
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8767);a=p.parse_args();folder=build()
 server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(SimpleHTTPRequestHandler,directory=str(folder)))
 print(f'Play China Quest: http://127.0.0.1:{a.port}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
