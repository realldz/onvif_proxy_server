import unittest
from src.onvif.proxy import _fix_ptz_profile, _rewrite_response, _get_ns_prefix


class TestNsPrefix(unittest.TestCase):
    def test_extract_tt(self):
        body = b'<Envelope xmlns:tt="http://www.onvif.org/ver10/schema"><Body/></Envelope>'
        self.assertEqual(_get_ns_prefix(body, 'http://www.onvif.org/ver10/schema'), b'tt')

    def test_extract_ns2(self):
        body = b'<Envelope xmlns:ns2="http://www.onvif.org/ver10/schema"><Body/></Envelope>'
        self.assertEqual(_get_ns_prefix(body, 'http://www.onvif.org/ver10/schema'), b'ns2')

    def test_extract_none(self):
        body = b'<Envelope><Body/></Envelope>'
        self.assertIsNone(_get_ns_prefix(body, 'http://www.onvif.org/ver10/schema'))


class TestXAddrRewrite(unittest.TestCase):
    def test_xaddr_replacement(self):
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'''<ns2:XAddr>http://10.0.0.1:80/onvif/device_service</ns2:XAddr>'''
        result = _rewrite_response(body, camera, '192.168.1.200', 5001)
        self.assertIn(b'192.168.1.200:5001', result)
        self.assertNotIn(b'10.0.0.1:80', result)

    def test_multiple_xaddrs(self):
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'''<XAddr>http://10.0.0.1:80/service1</XAddr>
<XAddr>http://10.0.0.1:80/service2</XAddr>'''
        result = _rewrite_response(body, camera, 'bridge', 5000)
        self.assertEqual(result.count(b'bridge:5000'), 2)


class TestPtzSpaceInjection(unittest.TestCase):
    def test_inject_missing_spaces(self):
        body = b'''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:ns2="http://www.onvif.org/ver10/schema"
               xmlns:ns1="http://www.onvif.org/ver10/media/wsdl">
  <soap:Body>
    <ns1:GetProfilesResponse>
      <ns1:Profiles token="test">
        <ns2:Name>Main</ns2:Name>
        <ns2:PTZConfiguration token="ptz1">
          <ns2:Name>PTZ</ns2:Name>
          <ns2:NodeToken>node1</ns2:NodeToken>
        </ns2:PTZConfiguration>
      </ns1:Profiles>
    </ns1:GetProfilesResponse>
  </soap:Body>
</soap:Envelope>'''
        result = _fix_ptz_profile(body)
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)
        self.assertIn(b'DefaultAbsolutePantTiltPositionSpace', result)
        self.assertIn(b'DefaultRelativePanTiltTranslationSpace', result)

    def test_skip_if_already_has_velocity(self):
        body = b'''<GetProfilesResponse>
  <Profiles token="test">
    <PTZConfiguration token="ptz1">
      <DefaultContinuousPanTiltVelocitySpace/>
    </PTZConfiguration>
  </Profiles>
</GetProfilesResponse>'''
        result = _fix_ptz_profile(body)
        self.assertEqual(result, body)

    def test_no_modification_non_profiles(self):
        body = b'<GetDeviceInformationResponse><Manufacturer>Test</Manufacturer></GetDeviceInformationResponse>'
        result = _fix_ptz_profile(body)
        self.assertEqual(result, body)

    def test_multiple_profiles(self):
        body = b'''<GetProfilesResponse>
  <trt:Profiles token="main" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">Main</tt:Name>
    <tt:PTZConfiguration token="ptz1">
      <tt:Name>PTZ</tt:Name>
      <tt:NodeToken>node1</tt:NodeToken>
    </tt:PTZConfiguration>
  </trt:Profiles>
  <trt:Profiles token="sub" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">Sub</tt:Name>
    <tt:PTZConfiguration token="ptz2">
      <tt:Name>PTZ</tt:Name>
      <tt:NodeToken>node2</tt:NodeToken>
    </tt:PTZConfiguration>
  </trt:Profiles>
</GetProfilesResponse>'''
        result = _fix_ptz_profile(body)
        open_tags = result.count(b'<tt:DefaultContinuousPanTiltVelocitySpace')
        self.assertEqual(open_tags, 2)

    def test_preserve_existing_ptzconfig(self):
        body = b'''<GetProfilesResponse xmlns:ns2="http://www.onvif.org/ver10/schema">
  <Profiles token="test">
    <ns2:PTZConfiguration token="ptz1">
      <ns2:Name>PTZ</ns2:Name>
      <ns2:NodeToken>node1</ns2:NodeToken>
    </ns2:PTZConfiguration>
  </Profiles>
</GetProfilesResponse>'''
        result = _fix_ptz_profile(body)
        # Should keep original PTZConfiguration and add spaces
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)
        self.assertIn(b'NodeToken>node1', result)

    def test_content_length_updated(self):
        from src.onvif.proxy import _rewrite_response
        camera = {'onvif_host': '10.0.0.1', 'onvif_port': 80}
        body = b'''<GetProfilesResponse>
  <Profiles token="test">
    <PTZConfiguration token="ptz1">
      <Name>PTZ</Name>
      <NodeToken>node1</NodeToken>
    </PTZConfiguration>
  </Profiles>
</GetProfilesResponse>'''
        result = _rewrite_response(body, camera, 'bridge', 5000)
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)
        self.assertGreater(len(result), len(body))

    def test_inject_ptz_config_when_missing(self):
        """Camera profiles with NO PTZConfiguration should get one injected.
        This is the root cause of Frigate's 'No appropriate Onvif profiles found'."""
        body = b'''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tt="http://www.onvif.org/ver10/schema"
               xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <soap:Body>
    <trt:GetProfilesResponse>
      <trt:Profiles token="profile_1">
        <tt:Name>Main</tt:Name>
        <tt:VideoSourceConfiguration token="vs1">
          <tt:Name>VideoSource</tt:Name>
        </tt:VideoSourceConfiguration>
        <tt:VideoEncoderConfiguration token="ve1">
          <tt:Name>H264</tt:Name>
          <tt:Encoding>H264</tt:Encoding>
        </tt:VideoEncoderConfiguration>
      </trt:Profiles>
    </trt:GetProfilesResponse>
  </soap:Body>
</soap:Envelope>'''
        result = _fix_ptz_profile(body)
        self.assertIn(b'PTZConfiguration', result)
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)

    def test_inject_ptz_config_single_profile(self):
        """GetProfileResponse (singular) should also be patched."""
        body = b'''<?xml version="1.0"?>
<GetProfileResponse>
  <Profiles token="profile_1">
    <Name>Main</Name>
    <VideoEncoderConfiguration token="ve1">
      <Name>H264</Name>
    </VideoEncoderConfiguration>
  </Profiles>
</GetProfileResponse>'''
        result = _fix_ptz_profile(body)
        self.assertIn(b'PTZConfiguration', result)
        self.assertIn(b'DefaultContinuousPanTiltVelocitySpace', result)


class TestXAddrRewriteRobust(unittest.TestCase):
    def test_rewrite_ip_mismatch(self):
        """Camera responds with IP even though we connected via hostname."""
        camera = {'onvif_host': 'GWIPC-12345.home', 'onvif_port': 5000}
        body = b'<XAddr>http://192.168.100.105:5000/onvif/device_service</XAddr>'
        result = _rewrite_response(body, camera, '192.168.1.200', 5001)
        self.assertIn(b'192.168.1.200:5001', result)
        self.assertNotIn(b'192.168.100.105:5000', result)


if __name__ == '__main__':
    unittest.main()

