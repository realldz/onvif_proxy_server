import http.client
import logging
import re

log = logging.getLogger(__name__)

SKIP_HEADERS = {'host', 'connection', 'transfer-encoding', 'content-length', 'accept-encoding'}

PTZ_SPACES_TPL = b'''    <%(ns)s:DefaultAbsolutePantTiltPositionSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</%(ns)s:DefaultAbsolutePantTiltPositionSpace>
    <%(ns)s:DefaultRelativePanTiltTranslationSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</%(ns)s:DefaultRelativePanTiltTranslationSpace>
    <%(ns)s:DefaultContinuousPanTiltVelocitySpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</%(ns)s:DefaultContinuousPanTiltVelocitySpace>'''

# A full PTZConfiguration block to inject when the camera profile has none.
# Frigate requires PTZConfiguration with DefaultContinuousPanTiltVelocitySpace
# to consider a profile valid for PTZ control.
PTZ_CONFIG_TPL = b'''<%(ns)s:PTZConfiguration token="default">
      <%(ns)s:Name>DefaultPTZConfiguration</%(ns)s:Name>
      <%(ns)s:UseCount>1</%(ns)s:UseCount>
      <%(ns)s:NodeToken>default</%(ns)s:NodeToken>
      <%(ns)s:DefaultAbsolutePantTiltPositionSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</%(ns)s:DefaultAbsolutePantTiltPositionSpace>
      <%(ns)s:DefaultRelativePanTiltTranslationSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</%(ns)s:DefaultRelativePanTiltTranslationSpace>
      <%(ns)s:DefaultContinuousPanTiltVelocitySpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</%(ns)s:DefaultContinuousPanTiltVelocitySpace>
      <%(ns)s:DefaultPTZSpeed>
        <%(ns)s:PanTilt x="0.5" y="0.5" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace"/>
      </%(ns)s:DefaultPTZSpeed>
      <%(ns)s:DefaultPTZTimeout>PT5S</%(ns)s:DefaultPTZTimeout>
      <%(ns)s:PanTiltLimits>
        <%(ns)s:Range>
          <%(ns)s:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</%(ns)s:URI>
          <%(ns)s:XRange><%(ns)s:Min>-1.0</%(ns)s:Min><%(ns)s:Max>1.0</%(ns)s:Max></%(ns)s:XRange>
          <%(ns)s:YRange><%(ns)s:Min>-1.0</%(ns)s:Min><%(ns)s:Max>1.0</%(ns)s:Max></%(ns)s:YRange>
        </%(ns)s:Range>
      </%(ns)s:PanTiltLimits>
    </%(ns)s:PTZConfiguration>'''


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
    new = f'http://{bridge_host}:{bridge_port}'.encode()

    # Replace exact hostname:port match
    old = f'http://{camera["onvif_host"]}:{camera["onvif_port"]}'.encode()
    body = body.replace(old, new)

    # Also replace any http URL pointing to the camera's ONVIF port, since the
    # camera might reply with its IP address even if we connected via hostname.
    # Match pattern: http://<anything>:<onvif_port>  (before the next / or end)
    cam_port = camera['onvif_port']
    body = re.sub(
        rb'http://[^/\s<"]+:' + str(cam_port).encode() + rb'(?=/|["\s<])',
        new,
        body,
    )

    body = _fix_ptz_profile(body)
    return body


def _get_ns_prefix(body, namespace_uri):
    m = re.search(rb'xmlns:(\w+)="' + re.escape(namespace_uri.encode()) + rb'"', body)
    if m:
        return m.group(1)
    return None


def _fix_ptz_profile(body):
    """Ensure GetProfilesResponse / GetProfileResponse profiles contain a valid
    PTZConfiguration block with DefaultContinuousPanTiltVelocitySpace.

    Frigate checks each profile for:
      1. VideoEncoderConfiguration  (must exist)
      2. PTZConfiguration           (must exist)
      3. PTZConfiguration.DefaultContinuousPanTiltVelocitySpace or
         DefaultContinuousZoomVelocitySpace  (at least one non-None)

    Many cheap cameras return profiles with no PTZConfiguration at all, causing
    Frigate to log "No appropriate Onvif profiles found".  This function:
      - Injects a full PTZConfiguration if the profile has none.
      - Adds DefaultContinuousPanTiltVelocitySpace (and friends) to an existing
        PTZConfiguration that is missing them.
    """
    if b'GetProfilesResponse' not in body and b'GetProfileResponse' not in body:
        return body

    ns = _get_ns_prefix(body, 'http://www.onvif.org/ver10/schema')
    if not ns:
        ns = b'tt'

    spaces = PTZ_SPACES_TPL.replace(b'%(ns)s', ns)
    ptz_config_block = PTZ_CONFIG_TPL.replace(b'%(ns)s', ns)

    # Step 1: For profiles that already have PTZConfiguration but are missing
    #         DefaultContinuousPanTiltVelocitySpace, inject the spaces.
    def _add_spaces(m):
        block = m.group(0)
        if b'DefaultContinuousPanTiltVelocitySpace' in block:
            return block
        closing = m.group(2)
        return block.replace(closing, spaces + b'\n  ' + closing)

    body = re.sub(
        rb'(<(?:[^>\s]+:)?PTZConfiguration[^>]*>.*?)(</(?:[^>\s]+:)?PTZConfiguration>)',
        _add_spaces,
        body,
        flags=re.DOTALL,
    )

    # Step 2: For profiles that have NO PTZConfiguration at all, inject one.
    #         We look for <Profiles> blocks that contain VideoEncoderConfiguration
    #         but lack PTZConfiguration, and insert one before the closing </Profiles>.
    def _add_ptz_config(m):
        block = m.group(0)
        if re.search(rb'<(?:[^>\s]+:)?PTZConfiguration[\s>]', block):
            # Already has PTZConfiguration (possibly just injected in step 1)
            return block
        closing = m.group(2)
        return block.replace(closing, b'    ' + ptz_config_block + b'\n  ' + closing)

    body = re.sub(
        rb'(<(?:[^>\s]+:)?Profiles[\s][^>]*>.*?)(</(?:[^>\s]+:)?Profiles>)',
        _add_ptz_config,
        body,
        flags=re.DOTALL,
    )

    log.debug('_fix_ptz_profile: patched response (%d bytes)', len(body))
    return body
