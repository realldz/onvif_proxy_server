import unittest
from src.camera.registry import CameraRegistry


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.cameras = [
            {'name': 'cam1', 'onvif_host': '10.0.0.1'},
            {'name': 'cam2', 'onvif_host': '10.0.0.2'},
        ]
        self.registry = CameraRegistry(self.cameras)

        self.port_cameras = [
            {'name': 'cam_a', 'onvif_host': '10.0.0.1', 'bind_port': 5001},
            {'name': 'cam_b', 'onvif_host': '10.0.0.2', 'bind_port': 5002},
        ]
        self.port_registry = CameraRegistry(self.port_cameras)

    def test_get_by_name(self):
        cam = self.registry.get('cam1')
        self.assertIsNotNone(cam)
        self.assertEqual(cam['onvif_host'], '10.0.0.1')

    def test_get_by_path(self):
        cam = self.registry.get_by_path('/onvif/cam1/device_service')
        self.assertIsNotNone(cam)
        self.assertEqual(cam['name'], 'cam1')

        cam = self.registry.get_by_path('/onvif/cam2/ptz_service')
        self.assertIsNotNone(cam)
        self.assertEqual(cam['name'], 'cam2')

    def test_get_by_path_missing(self):
        self.assertIsNone(self.registry.get_by_path('/onvif/nonexistent/device_service'))
        self.assertIsNone(self.registry.get_by_path('/other/path'))
        self.assertIsNone(self.registry.get('nonexistent'))

    def test_list_all(self):
        all_cams = self.registry.list_all()
        self.assertEqual(len(all_cams), 2)

    def test_len(self):
        self.assertEqual(len(self.registry), 2)

    def test_empty_registry(self):
        empty = CameraRegistry([])
        self.assertEqual(len(empty), 0)
        self.assertIsNone(empty.get('anything'))

    def test_get_by_port(self):
        cam = self.port_registry.get_by_port(5001)
        self.assertIsNotNone(cam)
        self.assertEqual(cam['name'], 'cam_a')

        cam = self.port_registry.get_by_port(5002)
        self.assertIsNotNone(cam)
        self.assertEqual(cam['name'], 'cam_b')

    def test_get_by_port_missing(self):
        self.assertIsNone(self.port_registry.get_by_port(9999))

    def test_get_ports(self):
        ports = self.port_registry.get_ports()
        self.assertIn(5001, ports)
        self.assertIn(5002, ports)

    def test_get_ports_empty(self):
        ports = self.registry.get_ports()
        self.assertEqual(ports, [])


if __name__ == '__main__':
    unittest.main()
