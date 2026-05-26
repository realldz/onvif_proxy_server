import json
import logging

log = logging.getLogger(__name__)

DEFAULTS = {
    'bind_host': '0.0.0.0',
    'bind_port': 5000,
}

CAMERA_DEFAULTS = {
    'username': 'admin',
    'password': '',
    'platform': 'auto',
    'ptz_protocol': 'rtsp_cmd',
    'onvif_port': 80,
    'rtsp_host': None,
    'rtsp_port': 554,
    'rtsp_cmd_config': {},
}


def load_config(path):
    with open(path) as f:
        config = json.load(f)

    for k, v in DEFAULTS.items():
        config.setdefault(k, v)

    for i, cam in enumerate(config.get('cameras', [])):
        if 'name' not in cam:
            cam['name'] = f'camera_{i}'
        for k, v in CAMERA_DEFAULTS.items():
            cam.setdefault(k, v)
        if cam.get('rtsp_host') is None:
            cam['rtsp_host'] = cam.get('onvif_host', '')
        rc = cam.setdefault('rtsp_cmd_config', {})
        rc.setdefault('case', 'upper')
        rc.setdefault('direction_mapping', 'auto')

    log.info('Loaded %d cameras from %s', len(config['cameras']), path)
    return config
