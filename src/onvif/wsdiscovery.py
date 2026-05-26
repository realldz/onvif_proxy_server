import logging
import re
import socket
import struct
import uuid

log = logging.getLogger(__name__)

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 3702

PROBE_MATCH = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://www.w3.org/2005/08/addressing"
    xmlns:wsd="http://docs.oasis-open.org/ws-dd/ns/discovery/2009/01"
    xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
  <soap:Header>
    <wsa:Action>http://docs.oasis-open.org/ws-dd/ns/discovery/2009/01/ProbeMatches</wsa:Action>
    <wsa:MessageID>uuid:{msg_id}</wsa:MessageID>
    <wsa:RelatesTo>{relates_to}</wsa:RelatesTo>
    <wsa:To>http://www.w3.org/2005/08/addressing/anonymous</wsa:To>
  </soap:Header>
  <soap:Body>
    <wsd:ProbeMatches>
      <wsd:ProbeMatch>
        <wsa:EndpointReference>
          <wsa:Address>uuid:{device_uuid}</wsa:Address>
        </wsa:EndpointReference>
        <wsd:Types>dn:NetworkVideoTransmitter</wsd:Types>
        <wsd:Scopes>onvif://www.onvif.org/type/NetworkVideoTransmitter onvif://www.onvif.org/hardware/{model} onvif://www.onvif.org/name/{name}</wsd:Scopes>
        <wsd:XAddrs>http://{bridge_host}:{bridge_port}/onvif/{name}/device_service</wsd:XAddrs>
        <wsd:MetadataVersion>1</wsd:MetadataVersion>
      </wsd:ProbeMatch>
    </wsd:ProbeMatches>
  </soap:Body>
</soap:Envelope>'''


class WsDiscoveryServer:
    def __init__(self, host, port, registry):
        self.bridge_host = host
        self.bridge_port = port
        self.registry = registry
        self._running = False
        self._sock = None

    def serve_forever(self):
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('', MCAST_PORT))

        mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._sock.settimeout(1.0)

        log.info('WS-Discovery listening on %s:%d', MCAST_GRP, MCAST_PORT)

        while self._running:
            try:
                data, addr = self._sock.recvfrom(65535)
                self._handle_probe(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                log.error('WS-Discovery error: %s', e)

        self._sock.close()

    def _get_bridge_host(self, peer_addr=None):
        """Resolve a routable bridge host, avoiding 0.0.0.0."""
        if self.bridge_host not in ('0.0.0.0', '', '::'):
            return self.bridge_host
        # Find the local IP that would route to the peer
        if peer_addr:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((peer_addr[0], 1))
                local_ip = s.getsockname()[0]
                s.close()
                return local_ip
            except Exception:
                pass
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

    def _handle_probe(self, data, addr):
        if b'Probe' not in data:
            return

        log.debug('WS-Discovery Probe from %s:%s', addr[0], addr[1])

        relates_to = ''
        m = re.search(rb'<wsa:MessageID>(.+?)</wsa:MessageID>', data)
        if m:
            relates_to = m.group(1).decode()

        bridge_host = self._get_bridge_host(addr)

        for camera in self.registry.list_all():
            response = PROBE_MATCH.format(
                msg_id=str(uuid.uuid4()),
                relates_to=relates_to,
                device_uuid=str(uuid.uuid4()),
                model=camera.get('name', 'Camera'),
                name=camera['name'],
                bridge_host=bridge_host,
                bridge_port=self.bridge_port,
            )
            self._sock.sendto(response.encode(), addr)
            log.debug('ProbeMatch sent for %s to %s:%s', camera['name'], addr[0], addr[1])

    def shutdown(self):
        self._running = False
        if self._sock:
            self._sock.close()
