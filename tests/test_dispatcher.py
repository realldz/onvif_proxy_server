import unittest
from src.onvif.dispatcher import resolve_action


class TestDispatcher(unittest.TestCase):
    def test_soap12_content_type(self):
        body = b'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body><tptz:ContinuousMove xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"/></soap:Body></soap:Envelope>'
        headers = {'Content-Type': 'application/soap+xml; action="http://www.onvif.org/ver20/ptz/wsdl/ContinuousMove"'}
        result = resolve_action(body, headers)
        self.assertIsNotNone(result)
        self.assertEqual(result['service'], 'ptz')
        self.assertEqual(result['name'], 'ContinuousMove')

    def test_soap11_header(self):
        body = b''
        headers = {'SOAPAction': '"http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"'}
        result = resolve_action(body, headers)
        self.assertIsNotNone(result)
        self.assertEqual(result['service'], 'device')
        self.assertEqual(result['name'], 'GetDeviceInformation')

    def test_xml_body_parse(self):
        body = b'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body><trt:GetProfiles xmlns:trt="http://www.onvif.org/ver10/media/wsdl"/></soap:Body></soap:Envelope>'
        headers = {'Content-Type': 'application/soap+xml'}
        result = resolve_action(body, headers)
        self.assertIsNotNone(result)
        self.assertEqual(result['service'], 'media')
        self.assertEqual(result['name'], 'GetProfiles')

    def test_unknown_action(self):
        body = b'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body><foo:Bar xmlns:foo="http://example.com"/></soap:Body></soap:Envelope>'
        headers = {}
        result = resolve_action(body, headers)
        self.assertIsNone(result)

    def test_ptz_actions(self):
        ptz_actions = ['ContinuousMove', 'Stop', 'GetPresets', 'GetStatus', 'GetNodes']
        for action in ptz_actions:
            body = f'''<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body><tptz:{action} xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"/></soap:Body></soap:Envelope>'''
            result = resolve_action(body.encode(), {})
            self.assertIsNotNone(result, f'Failed to parse {action}')
            self.assertEqual(result['service'], 'ptz')
            self.assertEqual(result['name'], action)


if __name__ == '__main__':
    unittest.main()
