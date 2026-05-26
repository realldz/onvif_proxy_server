import logging
import xml.etree.ElementTree as ET

from . import templates
from ..camera.rtsp_client import RtspPtzClient

log = logging.getLogger(__name__)

_clients = {}

NS_SOAP12 = 'http://www.w3.org/2003/05/soap-envelope'
NS_SOAP11 = 'http://schemas.xmlsoap.org/soap/envelope/'
NS_PTZ = 'http://www.onvif.org/ver20/ptz/wsdl'
NS_TT = 'http://www.onvif.org/ver10/schema'


def _get_client(camera):
    name = camera['name']
    if name not in _clients:
        rc = camera.get('rtsp_cmd_config', {})
        _clients[name] = RtspPtzClient(
            host=camera['rtsp_host'],
            port=camera.get('rtsp_port', 554),
            platform=rc.get('direction_mapping', 'auto'),
            case=rc.get('case', 'upper'),
        )
    return _clients[name]


def _velocity_to_direction(x, y, threshold=0.05):
    if abs(x) < threshold and abs(y) < threshold:
        return 'stop'
    if abs(x) >= abs(y):
        if x < -threshold:
            return 'left'
        if x > threshold:
            return 'right'
        return 'stop'
    if y < -threshold:
        return 'up'
    if y > threshold:
        return 'down'
    return 'stop'


def _parse_body(body_xml):
    params = {}
    try:
        root = ET.fromstring(body_xml)
        body_elem = root.find(f'{{{NS_SOAP12}}}Body')
        if body_elem is None:
            body_elem = root.find(f'{{{NS_SOAP11}}}Body')
        if body_elem is None or len(body_elem) == 0:
            return params

        action = body_elem[0]

        for tag, key in [
            (f'{{{NS_PTZ}}}ProfileToken', 'ProfileToken'),
            (f'{{{NS_PTZ}}}PresetToken', 'PresetToken'),
            (f'{{{NS_PTZ}}}PresetName', 'PresetName'),
        ]:
            el = action.find(tag)
            if el is not None and el.text:
                params[key] = el.text

        for parent_tag, parent_key in [
            (f'{{{NS_PTZ}}}Velocity', 'velocity'),
            (f'{{{NS_PTZ}}}Translation', 'translation'),
            (f'{{{NS_PTZ}}}Position', 'position'),
        ]:
            parent = action.find(parent_tag)
            if parent is not None:
                pt = parent.find(f'{{{NS_TT}}}PanTilt')
                if pt is not None:
                    try:
                        params['x'] = float(pt.get('x', '0'))
                        params['y'] = float(pt.get('y', '0'))
                    except (ValueError, TypeError):
                        params['x'] = 0.0
                        params['y'] = 0.0

        pantilt_stop = action.find(f'{{{NS_PTZ}}}PanTilt')
        if pantilt_stop is not None:
            params['StopPanTilt'] = pantilt_stop.text == 'true'

    except ET.ParseError as e:
        log.warning('XML parse error in PTZ body: %s', e)

    return params


def handle_ptz(camera, action_name, body_xml):
    params = _parse_body(body_xml)
    log.info('PTZ %s: %s', action_name, params)

    if camera.get('ptz_protocol') == 'rtsp_cmd':
        if action_name in ('ContinuousMove', 'RelativeMove', 'AbsoluteMove'):
            x = params.get('x', 0)
            y = params.get('y', 0)
            direction = _velocity_to_direction(x, y)
            client = _get_client(camera)
            if not client.send_command(direction):
                log.error('PTZ failed: %s %s', camera['name'], direction)
                return 500, {'Content-Type': 'application/soap+xml'}, templates.build_fault('Action', f'PTZ command failed: {direction}').encode()

        elif action_name == 'Stop':
            stop_pt = params.get('StopPanTilt', True)
            if stop_pt:
                client = _get_client(camera)
                client.send_command('stop')

        elif action_name == 'GotoPreset':
            log.info('GotoPreset %s (not fully mapped)', params.get('PresetToken'))

    response = templates.build_ptz_response(action_name)
    return 200, {'Content-Type': 'application/soap+xml; charset=utf-8'}, response.encode()
