#!/usr/bin/env python3
"""ONVIF Proxy Server - bridge between Frigate and non-ONVIF cameras.

Translates ONVIF PTZ commands to camera-specific RTSP SET_PARAMETER/USER_CMD_SET
with ptzCmd header, while proxying Device/Media/Imaging requests to the camera's
native ONVIF endpoint.

Usage:
    python -m src.server -c config.json
    python -m src.server -c config.json -p 5000 -v
"""

import argparse
import logging
import os
import sys
import threading

from src.camera.config import load_config
from src.camera.registry import CameraRegistry
from src.onvif.http_server import OnvifHttpServer
from src.onvif.wsdiscovery import WsDiscoveryServer


def main():
    parser = argparse.ArgumentParser(description='ONVIF Proxy Server')
    parser.add_argument('-c', '--config', default='config.json',
                        help='Configuration file path (default: config.json)')
    parser.add_argument('-b', '--bind', default=None,
                        help='Bind address (default: from config or 0.0.0.0)')
    parser.add_argument('-p', '--port', type=int, default=None,
                        help='HTTP port (default: from config or 5000)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable debug logging')
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    log = logging.getLogger('server')

    if not os.path.exists(args.config):
        log.error('Config file not found: %s', args.config)
        sys.exit(1)

    config = load_config(args.config)
    registry = CameraRegistry(config['cameras'])

    if len(registry) == 0:
        log.warning('No cameras configured!')

    bind_host = args.bind or config.get('bind_host', '0.0.0.0')
    bind_port = args.port or config.get('bind_port', 5000)

    http_server = OnvifHttpServer(bind_host, bind_port, registry)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    ws_discovery = WsDiscoveryServer(bind_host, bind_port, registry)
    ws_thread = threading.Thread(target=ws_discovery.serve_forever, daemon=True)
    ws_thread.start()

    log.info('ONVIF Proxy Server running on %s:%d (%d camera(s))',
             bind_host, bind_port, len(registry))

    try:
        while http_thread.is_alive():
            http_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        log.info('Shutting down...')
        http_server.shutdown()
        ws_discovery.shutdown()


if __name__ == '__main__':
    main()
