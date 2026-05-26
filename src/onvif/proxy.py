import http.client
import logging

log = logging.getLogger(__name__)

SKIP_HEADERS = {'host', 'connection', 'transfer-encoding', 'content-length', 'accept-encoding'}


def proxy_request(camera, method, path, headers, body):
    conn = http.client.HTTPConnection(
        camera['onvif_host'],
        camera['onvif_port'],
        timeout=10,
    )

    fwd_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in SKIP_HEADERS
    }

    try:
        conn.request(method, path, body=body, headers=fwd_headers)
        resp = conn.getresponse()
        resp_body = resp.read()
        log.debug('Proxy %s %s:%s%s -> %d', method, camera['onvif_host'], camera['onvif_port'], path, resp.status)
        return resp.status, dict(resp.getheaders()), resp_body
    except Exception as e:
        log.error('Proxy to %s:%s failed: %s', camera['onvif_host'], camera['onvif_port'], e)
        return 502, {'Content-Type': 'text/xml'}, b'<error>Camera unreachable</error>'
    finally:
        conn.close()
