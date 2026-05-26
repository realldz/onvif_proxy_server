import http.client
import logging
import re

log = logging.getLogger(__name__)

SKIP_HEADERS = {'host', 'connection', 'transfer-encoding', 'content-length', 'accept-encoding'}

PTZ_SPACES_TPL = b'''    <%(ns)s:DefaultAbsolutePanTiltPositionSpace>
      <%(ns)s:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</%(ns)s:URI>
    </%(ns)s:DefaultAbsolutePanTiltPositionSpace>
    <%(ns)s:DefaultRelativePanTiltTranslationSpace>
      <%(ns)s:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</%(ns)s:URI>
    </%(ns)s:DefaultRelativePanTiltTranslationSpace>
    <%(ns)s:DefaultContinuousPanTiltVelocitySpace>
      <%(ns)s:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</%(ns)s:URI>
    </%(ns)s:DefaultContinuousPanTiltVelocitySpace>'''


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
    body = _fix_ptz_profile(body)
    return body


def _get_ns_prefix(body, namespace_uri):
    m = re.search(rb'xmlns:(\w+)="' + re.escape(namespace_uri.encode()) + rb'"', body)
    if m:
        return m.group(1)
    return None


def _fix_ptz_profile(body):
    if b'GetProfilesResponse' not in body:
        return body

    ns = _get_ns_prefix(body, 'http://www.onvif.org/ver10/schema')
    if not ns:
        ns = b'tt'

    spaces = PTZ_SPACES_TPL.replace(b'%(ns)s', ns)

    def _replacer(m):
        block = m.group(0)
        if b'DefaultContinuousPanTiltVelocitySpace' in block:
            return block
        closing = m.group(2)
        return block.replace(closing, spaces + b'\n  ' + closing)

    result = re.sub(
        rb'(<(?:[^>\s]+:)?PTZConfiguration[^>]*>.*?)(</(?:[^>\s]+:)?PTZConfiguration>)',
        _replacer,
        body,
        flags=re.DOTALL,
    )
    return result
