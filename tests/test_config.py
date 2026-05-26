import json
import os
import tempfile
import unittest
from src.camera.config import load_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config_data = {
            'bind_host': '0.0.0.0',
            'bind_port': 5000,
            'cameras': [
                {
                    'name': 'test_cam',
                    'onvif_host': '192.168.1.100',
                    'onvif_port': 80,
                    'rtsp_host': '192.168.1.100',
                }
            ]
        }

    def _write_config(self, data):
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, tmp)
        tmp.close()
        return tmp.name

    def test_load_basic(self):
        path = self._write_config(self.config_data)
        try:
            config = load_config(path)
            self.assertEqual(len(config['cameras']), 1)
            self.assertEqual(config['cameras'][0]['name'], 'test_cam')
            self.assertEqual(config['cameras'][0]['ptz_protocol'], 'rtsp_cmd')
        finally:
            os.unlink(path)

    def test_defaults_applied(self):
        data = {'cameras': [{'name': 'cam1', 'onvif_host': '10.0.0.1'}]}
        path = self._write_config(data)
        try:
            config = load_config(path)
            cam = config['cameras'][0]
            self.assertEqual(cam['username'], 'admin')
            self.assertEqual(cam['password'], '')
            self.assertEqual(cam['onvif_port'], 80)
            self.assertEqual(cam['rtsp_port'], 554)
            self.assertEqual(cam['rtsp_host'], '10.0.0.1')
            self.assertEqual(cam['rtsp_cmd_config']['case'], 'upper')
        finally:
            os.unlink(path)

    def test_multiple_cameras(self):
        data = {
            'bind_port': 5000,
            'cameras': [
                {'name': 'cam1', 'onvif_host': '10.0.0.1'},
                {'name': 'cam2', 'onvif_host': '10.0.0.2'},
                {'name': 'cam3', 'onvif_host': '10.0.0.3'},
            ]
        }
        path = self._write_config(data)
        try:
            config = load_config(path)
            self.assertEqual(len(config['cameras']), 3)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
