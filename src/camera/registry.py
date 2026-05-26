import logging

log = logging.getLogger(__name__)


class CameraRegistry:
    def __init__(self, cameras_config):
        self._by_name = {}
        for cam in cameras_config:
            name = cam['name']
            self._by_name[name] = cam
        log.info('Camera registry: %s', list(self._by_name.keys()))

    def get(self, name):
        return self._by_name.get(name)

    def get_by_path(self, path):
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'onvif':
            return self._by_name.get(parts[1])
        return None

    def list_all(self):
        return list(self._by_name.values())

    def __len__(self):
        return len(self._by_name)
