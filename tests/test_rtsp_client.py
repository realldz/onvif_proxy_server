import unittest
from src.camera.rtsp_client import RtspPtzClient, FORMATS, send_rtsp


class TestDirectionMapping(unittest.TestCase):
    def setUp(self):
        self.mips_upper = RtspPtzClient('192.168.1.1', platform='mips', case='upper')
        self.arm_upper = RtspPtzClient('192.168.1.1', platform='arm', case='upper')
        self.standard = RtspPtzClient('192.168.1.1', platform='standard', case='upper')
        self.lower = RtspPtzClient('192.168.1.1', platform='mips', case='lower')

    def test_mips_upper(self):
        self.assertEqual(self.mips_upper._resolve_direction('up'), 'UP')
        self.assertEqual(self.mips_upper._resolve_direction('down'), 'DWON')
        self.assertEqual(self.mips_upper._resolve_direction('left'), 'LEFT')
        self.assertEqual(self.mips_upper._resolve_direction('right'), 'RIGHT')
        self.assertEqual(self.mips_upper._resolve_direction('stop'), 'STOP')

    def test_arm_upper(self):
        self.assertEqual(self.arm_upper._resolve_direction('up'), 'UP')
        self.assertEqual(self.arm_upper._resolve_direction('down'), 'DWON')

    def test_standard(self):
        self.assertEqual(self.standard._resolve_direction('down'), 'DOWN')

    def test_lower_case(self):
        self.assertEqual(self.lower._resolve_direction('up'), 'up')
        self.assertEqual(self.lower._resolve_direction('down'), 'dwon')
        self.assertEqual(self.lower._resolve_direction('left'), 'left')

    def test_format_list(self):
        names = [f[0] for f in FORMATS]
        self.assertIn('content_trick', names)
        self.assertIn('ptzcmd_header', names)
        self.assertIn('user_cmd_body', names)


class TestRtspFormatStrings(unittest.TestCase):
    def test_content_type_trick_format(self):
        from src.camera.rtsp_client import fmt_content_type_trick as fn
        result = fn('10.0.0.1', 554, 'UP', '/onvif1')
        self.assertIsInstance(result, bytes)

    def test_ptzcmd_header_format(self):
        from src.camera.rtsp_client import fmt_ptzcmd_header as fn
        result = fn('10.0.0.1', 554, 'DWON', '/onvif1')
        self.assertIsInstance(result, bytes)


if __name__ == '__main__':
    unittest.main()
