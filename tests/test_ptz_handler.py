import unittest
from src.onvif.ptz_handler import _velocity_to_direction, _parse_body


class TestVelocityMapping(unittest.TestCase):
    def test_stop(self):
        self.assertEqual(_velocity_to_direction(0, 0), 'stop')
        self.assertEqual(_velocity_to_direction(0.01, -0.01), 'stop')

    def test_up(self):
        self.assertEqual(_velocity_to_direction(0, 0.5), 'up')
        self.assertEqual(_velocity_to_direction(0, 1.0), 'up')

    def test_down(self):
        self.assertEqual(_velocity_to_direction(0, -0.5), 'down')
        self.assertEqual(_velocity_to_direction(0, -1.0), 'down')

    def test_left(self):
        self.assertEqual(_velocity_to_direction(-0.5, 0), 'left')
        self.assertEqual(_velocity_to_direction(-1.0, 0), 'left')

    def test_right(self):
        self.assertEqual(_velocity_to_direction(0.5, 0), 'right')
        self.assertEqual(_velocity_to_direction(1.0, 0), 'right')

    def test_diagonal_prefers_horizontal(self):
        self.assertEqual(_velocity_to_direction(0.5, -0.3), 'right')
        self.assertEqual(_velocity_to_direction(-0.5, 0.3), 'left')


class TestPTZBodyParser(unittest.TestCase):
    def test_continuous_move(self):
        xml = b'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tt="http://www.onvif.org/ver10/schema"
               xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
  <soap:Body>
    <tptz:ContinuousMove>
      <tptz:ProfileToken>main</tptz:ProfileToken>
      <tptz:Velocity>
        <tt:PanTilt x="0.5" y="0"/>
      </tptz:Velocity>
    </tptz:ContinuousMove>
  </soap:Body>
</soap:Envelope>'''
        params = _parse_body(xml)
        self.assertEqual(params.get('ProfileToken'), 'main')
        self.assertAlmostEqual(params.get('x'), 0.5)
        self.assertAlmostEqual(params.get('y'), 0.0)

    def test_stop(self):
        xml = b'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
  <soap:Body>
    <tptz:Stop>
      <tptz:ProfileToken>main</tptz:ProfileToken>
      <tptz:PanTilt>true</tptz:PanTilt>
    </tptz:Stop>
  </soap:Body>
</soap:Envelope>'''
        params = _parse_body(xml)
        self.assertTrue(params.get('StopPanTilt'))

    def test_get_presets(self):
        xml = b'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
  <soap:Body>
    <tptz:GetPresets>
      <tptz:ProfileToken>main</tptz:ProfileToken>
    </tptz:GetPresets>
  </soap:Body>
</soap:Envelope>'''
        params = _parse_body(xml)
        self.assertEqual(params.get('ProfileToken'), 'main')

    def test_goto_preset(self):
        xml = b'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
  <soap:Body>
    <tptz:GotoPreset>
      <tptz:ProfileToken>main</tptz:ProfileToken>
      <tptz:PresetToken>1</tptz:PresetToken>
    </tptz:GotoPreset>
  </soap:Body>
</soap:Envelope>'''
        params = _parse_body(xml)
        self.assertEqual(params.get('PresetToken'), '1')


class TestTemplates(unittest.TestCase):
    def test_build_ptz_response(self):
        from src.onvif.templates import build_ptz_response, build_fault
        resp = build_ptz_response('ContinuousMove')
        self.assertIn('<tptz:ContinuousMoveResponse/>', resp)
        self.assertIn('soap:Envelope', resp)

    def test_build_fault(self):
        from src.onvif.templates import build_fault
        resp = build_fault('Action', 'Something failed')
        self.assertIn('soap:Fault', resp)
        self.assertIn('Something failed', resp)

    def test_all_actions_have_templates(self):
        from src.onvif.templates import PTZ_BODIES, build_ptz_response
        for action in ['GetServiceCapabilities', 'GetNodes', 'GetNode',
                        'GetConfigurations', 'GetConfiguration',
                        'ContinuousMove', 'Stop', 'RelativeMove',
                        'GetPresets', 'GetStatus', 'SetPreset',
                        'GotoPreset', 'RemovePreset']:
            resp = build_ptz_response(action)
            self.assertIn(f'{action}Response', resp, f'Missing template for {action}')


if __name__ == '__main__':
    unittest.main()
