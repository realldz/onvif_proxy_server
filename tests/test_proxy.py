import unittest
from src.onvif.proxy import _inject_ptz_config, PTZ_CONFIG_INJECT


class TestXAddrRewrite(unittest.TestCase):
    def test_xaddr_replacement(self):
        from src.onvif.proxy import _rewrite_response
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'''<tt:XAddr>http://10.0.0.1:80/onvif/device_service</tt:XAddr>'''
        result = _rewrite_response(body, camera, '192.168.1.200', 5001)
        self.assertIn(b'192.168.1.200:5001', result)
        self.assertNotIn(b'10.0.0.1:80', result)

    def test_no_xaddr_no_change(self):
        from src.onvif.proxy import _rewrite_response
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'<dummy>hello world</dummy>'
        result = _rewrite_response(body, camera, '192.168.1.200', 5001)
        self.assertEqual(result, body)

    def test_multiple_xaddrs(self):
        from src.onvif.proxy import _rewrite_response
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'''<XAddr>http://10.0.0.1:80/service1</XAddr>
<XAddr>http://10.0.0.1:80/service2</XAddr>'''
        result = _rewrite_response(body, camera, 'bridge', 5000)
        self.assertEqual(result.count(b'bridge:5000'), 2)
        self.assertNotIn(b'10.0.0.1:80', result)


class TestPtzProfileInjection(unittest.TestCase):
    def test_inject_into_empty_profiles(self):
        body = b'''<?xml version="1.0"?>
<soap:Envelope>
  <soap:Body>
    <trt:GetProfilesResponse>
      <trt:Profiles token="main">
        <tt:Name>Main</tt:Name>
        <tt:VideoEncoderConfiguration token="v1">
          <tt:Encoding>H264</tt:Encoding>
        </tt:VideoEncoderConfiguration>
      </trt:Profiles>
    </trt:GetProfilesResponse>
  </soap:Body>
</soap:Envelope>'''
        result = _inject_ptz_config(body)
        self.assertIn(b'PTZConfiguration', result)
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)

    def test_skip_if_already_has_ptz(self):
        body = b'''<trt:GetProfilesResponse>
  <trt:Profiles token="main">
    <tt:Name>Main</tt:Name>
    <tt:PTZConfiguration token="default"/>
  </trt:Profiles>
</trt:GetProfilesResponse>'''
        result = _inject_ptz_config(body)
        self.assertEqual(result, body)

    def test_no_modification_non_profiles(self):
        body = b'<GetDeviceInformationResponse><Manufacturer>Test</Manufacturer></GetDeviceInformationResponse>'
        result = _inject_ptz_config(body)
        self.assertEqual(result, body)

    def test_multiple_profiles(self):
        body = b'''<trt:GetProfilesResponse>
  <trt:Profiles token="main">
    <tt:Name>Main</tt:Name>
  </trt:Profiles>
  <trt:Profiles token="sub">
    <tt:Name>Sub</tt:Name>
  </trt:Profiles>
</trt:GetProfilesResponse>'''
        result = _inject_ptz_config(body)
        open_tags = result.count(b'<tt:PTZConfiguration ')
        self.assertEqual(open_tags, 2)

    def test_content_length_update(self):
        from src.onvif.proxy import _rewrite_response
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'<trt:GetProfilesResponse><trt:Profiles token="main"><tt:Name>Cam</tt:Name></trt:Profiles></trt:GetProfilesResponse>'
        result = _rewrite_response(body, camera, 'bridge', 5000)
        self.assertIn(b'PTZConfiguration', result)
        self.assertGreater(len(result), len(body))


if __name__ == '__main__':
    unittest.main()
