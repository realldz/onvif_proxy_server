import logging

log = logging.getLogger(__name__)


class CameraRegistry:
    def __init__(self, cameras_config, default_bind_port=5000):
        self._by_name = {}
        self._by_port = {}
        for cam in cameras_config:
            name = cam['name']
            self._by_name[name] = cam
            port = cam.get('bind_port')
            if port is not None:
                self._by_port[port] = cam
        log.info('Camera registry: %s', list(self._by_name.keys()))
        if self._by_port:
            log.info('Port mapping: %s', {p: c['name'] for p, c in self._by_port.items()})

    def get(self, name):
        return self._by_name.get(name)

    def get_by_port(self, port):
        return self._by_port.get(port)

    def get_by_path(self, path):
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'onvif':
            return self._by_name.get(parts[1])
        return None

    def get_ports(self):
        return list(self._by_port.keys())

    def list_all(self):
        return list(self._by_name.values())

    def __len__(self):
        return len(self._by_name)
