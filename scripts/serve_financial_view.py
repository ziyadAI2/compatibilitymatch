from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
root = Path(__file__).resolve().parent.parent / 'instance'
handler = partial(SimpleHTTPRequestHandler, directory=str(root))
ThreadingHTTPServer(('127.0.0.1', 8765), handler).serve_forever()
