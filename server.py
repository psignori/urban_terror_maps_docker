#!/usr/bin/env python3
"""
Servidor de votação Urban Terror Maps
Uso: python3 server.py [porta]       (padrão: 8080)

Acesse pelo IP da sua máquina: http://192.168.x.x:8080
Os votos são gravados em votes.json no mesmo diretório.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

VOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'votes.json')
SERVE_DIR  = os.path.dirname(os.path.abspath(__file__))


def load_votes() -> dict:
    if os.path.exists(VOTES_FILE):
        with open(VOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_votes(votes: dict) -> None:
    with open(VOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(votes, f, indent=2, ensure_ascii=False)


class VoteHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    # ── GET /votes  → retorna todos os votos ──
    # ── GET /       → redireciona para o HTML ──
    # ── GET /*      → serve arquivos estáticos ──
    def do_GET(self):
        if self.path == '/votes':
            self._json_response(200, load_votes())
        elif self.path in ('/', ''):
            self.send_response(302)
            self.send_header('Location', '/urban-terror-maps.html')
            self.end_headers()
        else:
            super().do_GET()

    # ── POST /vote  → registra um voto ──
    def do_POST(self):
        if self.path == '/reset':
            save_votes({})
            self._json_response(200, {'ok': True})
            return

        if self.path != '/vote':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        try:
            data     = json.loads(self.rfile.read(length))
            map_name = str(data.get('map',  '')).strip()
            mode     = str(data.get('mode', '')).strip()
        except (json.JSONDecodeError, ValueError):
            self.send_response(400)
            self.end_headers()
            return

        if not map_name or not mode:
            self.send_response(400)
            self.end_headers()
            return

        votes = load_votes()
        votes.setdefault(map_name, {})
        votes[map_name][mode] = votes[map_name].get(mode, 0) + 1
        save_votes(votes)

        self._json_response(200, {
            'ok':    True,
            'map':   map_name,
            'mode':  mode,
            'count': votes[map_name][mode],
        })

    def _json_response(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',  'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()}  {fmt % args}")


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    # Descobre o IP local para exibir no terminal
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = 'localhost'

    httpd = HTTPServer(('0.0.0.0', port), VoteHandler)
    print(f"\n  Servidor rodando!")
    print(f"  Local:        http://localhost:{port}/urban-terror-maps.html")
    print(f"  Rede local:   http://{local_ip}:{port}/urban-terror-maps.html")
    print(f"  Votos em:     {VOTES_FILE}")
    print(f"\n  Ctrl+C para parar\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")

