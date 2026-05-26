import http.client
import logging
import re

log = logging.getLogger(__name__)

SKIP_HEADERS = {'host', 'connection', 'transfer-encoding', 'content-length', 'accept-encoding'}

PTZ_CONFIG_INJECT = b'''<tt:PTZConfiguration token="default">
      <tt:Name>Default PTZ</tt:Name>
      <tt:NodeToken>default</tt:NodeToken>
      <tt:DefaultContinuousPanTiltVelocitySpace>
        <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
      </tt:DefaultContinuousPanTiltVelocitySpace>
    </tt:PTZConfiguration>'''


def proxy_request(camera, method, path, headers, body, bridge_host=None, bridge_port=None):
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
        resp_headers = dict(resp.getheaders())

        if bridge_host and bridge_port:
            resp_body = _rewrite_response(resp_body, camera, bridge_host, bridge_port)
            resp_headers['Content-Length'] = str(len(resp_body))

        log.debug('Proxy %s %s:%s%s -> %d (%d bytes)',
                  method, camera['onvif_host'], camera['onvif_port'], path,
                  resp.status, len(resp_body))
        return resp.status, resp_headers, resp_body
    except Exception as e:
        log.error('Proxy to %s:%s failed: %s', camera['onvif_host'], camera['onvif_port'], e)
        return 502, {'Content-Type': 'text/plain'}, b'Camera unreachable'
    finally:
        conn.close()


def _rewrite_response(body, camera, bridge_host, bridge_port):
    old = f'http://{camera["onvif_host"]}:{camera["onvif_port"]}'
    new = f'http://{bridge_host}:{bridge_port}'
    body = body.replace(old.encode(), new.encode())
    body = _inject_ptz_config(body)
    return body


def _inject_ptz_config(body):
    if b'GetProfilesResponse' not in body:
        return body

    def _replacer(m):
        block = m.group(0)
        if b'<tt:PTZConfiguration' in block:
            return block
        closing = m.group(2)
        indent = b'    '
        return block.replace(closing, indent + PTZ_CONFIG_INJECT + b'\n' + closing)

    result = re.sub(
        rb'(<\w+:Profiles[^>]*>.*?)(</\w+:Profiles>)',
        _replacer,
        body,
        flags=re.DOTALL,
    )
    return result
