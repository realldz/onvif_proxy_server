import logging
import socketserver
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from .dispatcher import resolve_action
from .ptz_handler import handle_ptz
from .proxy import proxy_request

log = logging.getLogger(__name__)


class OnvifHandler(BaseHTTPRequestHandler):
    registry = None

    def _resolve_camera(self):
        cam = self.registry.get_by_port(self.server.server_port)
        if cam:
            return cam
        cam = self.registry.get_by_path(self.path)
        if cam:
            return cam
        if len(self.registry) == 1:
            return self.registry.list_all()[0]
        return None

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b''

        camera = self._resolve_camera()
        if not camera:
            self.send_error(404, f'Camera not found (port={self.server.server_port}, path={self.path})')
            return

        action = resolve_action(body, {k: v for k, v in self.headers.items()})
        if not action:
            self.send_error(400, 'Cannot determine SOAP action')
            return

        log.debug('%s -> %s/%s (protocol=%s)', camera['name'], action['service'], action['name'], camera.get('ptz_protocol'))

        if action['service'] == 'ptz' and camera.get('ptz_protocol') == 'rtsp_cmd':
            status, resp_headers, resp_body = handle_ptz(camera, action['name'], body)
        else:
            status, resp_headers, resp_body = proxy_request(camera, 'POST', self.path, dict(self.headers), body)

        self._send_response(status, resp_headers, resp_body)

    def do_GET(self):
        camera = self._resolve_camera()
        if not camera:
            self.send_error(404, f'Camera not found (port={self.server.server_port}, path={self.path})')
            return
        status, resp_headers, resp_body = proxy_request(camera, 'GET', self.path, dict(self.headers), b'')
        self._send_response(status, resp_headers, resp_body)

    def _send_response(self, status, resp_headers, resp_body):
        self.send_response(status)
        for k, v in resp_headers.items():
            if k.lower() not in ('transfer-encoding', 'connection'):
                self.send_header(k, v)
        self.send_header('Connection', 'close')
        self.end_headers()
        if resp_body:
            self.wfile.write(resp_body)

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)


class ThreadingOnvifServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class OnvifHttpServer:
    def __init__(self, host, port, registry):
        OnvifHandler.registry = registry
        ports = registry.get_ports()
        if not ports:
            ports = [port]
        self._servers = []
        for p in ports:
            srv = ThreadingOnvifServer((host, p), OnvifHandler)
            self._servers.append(srv)
            log.info('ONVIF HTTP server listening on %s:%s', host, p)

    def serve_forever(self):
        threads = []
        for srv in self._servers:
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            threads.append((srv, t))
        for srv, t in threads:
            t.join()

    def shutdown(self):
        for srv in self._servers:
            srv.shutdown()
