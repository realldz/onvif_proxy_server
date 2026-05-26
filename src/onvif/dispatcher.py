import logging
import re
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)

NS_SOAP12 = 'http://www.w3.org/2003/05/soap-envelope'
NS_SOAP11 = 'http://schemas.xmlsoap.org/soap/envelope/'

SERVICE_MAP = {
    'http://www.onvif.org/ver10/device/wsdl': 'device',
    'http://www.onvif.org/ver10/media/wsdl': 'media',
    'http://www.onvif.org/ver20/ptz/wsdl': 'ptz',
    'http://www.onvif.org/ver10/imaging/wsdl': 'imaging',
    'http://www.onvif.org/ver10/events/wsdl': 'events',
    'http://www.onvif.org/ver10/deviceio/wsdl': 'deviceio',
}


def resolve_action(body, headers):
    content_type = headers.get('Content-Type', '')

    m = re.search(r'action=(["\']?)([^"\';]+)\1', content_type)
    if m:
        result = _parse_action_uri(m.group(2))
        if result:
            return result

    soap_action = headers.get('SOAPAction', '').strip('"').strip()
    if soap_action:
        result = _parse_action_uri(soap_action)
        if result:
            return result

    if body:
        return _parse_action_xml(body)

    return None


def _parse_action_uri(uri):
    parts = uri.rsplit('/', 1)
    if len(parts) == 2:
        service = SERVICE_MAP.get(parts[0])
        if service:
            return {'service': service, 'name': parts[1], 'ns': parts[0]}
    return None


def _parse_action_xml(body):
    try:
        root = ET.fromstring(body)
        body_elem = root.find(f'{{{NS_SOAP12}}}Body')
        if body_elem is None:
            body_elem = root.find(f'{{{NS_SOAP11}}}Body')
        if body_elem is not None and len(body_elem) > 0:
            action = body_elem[0]
            tag = action.tag
            ns = tag.split('}')[0][1:] if '}' in tag else ''
            name = tag.split('}')[1] if '}' in tag else tag
            service = SERVICE_MAP.get(ns)
            if service:
                return {'service': service, 'name': name, 'ns': ns}
    except ET.ParseError as e:
        log.warning('XML parse error: %s', e)
    return None
