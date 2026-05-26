# ONVIF Proxy Server - Architecture

## Overview

ONVIF Proxy Server bridges Frigate NVR with cameras that have broken or
incomplete ONVIF implementations. It presents a standard ONVIF interface to
Frigate while translating PTZ commands to camera-specific RTSP messages.

## Architecture

```
Frigate --ONVIF SOAP--> onvif-bridge:5001 --> RTSP ptzCmd --> Camera A:554
                         onvif-bridge:5002 --> RTSP ptzCmd --> Camera B:554
                              |
                              |--HTTP proxy--> Camera A/B ONVIF (Device/Media)
```

- **Non-PTZ** requests → proxied to camera's native ONVIF endpoint
- **PTZ** requests (if `ptz_protocol=rtsp_cmd`) → intercepted, translated to RTSP

## Camera Identification

The bridge supports 3 methods to identify which camera a request belongs to,
checked in this order:

### 1. Port-based (recommended for Frigate)

Each camera gets a unique `bind_port` on the bridge. Frigate configures
each camera with a different `port` pointing to the bridge.

```json
// bridge config.json
{
  "cameras": [
    {"name": "cam1", "bind_port": 5001, "onvif_host": "10.0.0.1", ...},
    {"name": "cam2", "bind_port": 5002, "onvif_host": "10.0.0.2", ...}
  ]
}
```

```yaml
# Frigate config
cameras:
  cam1:
    onvif: { host: "bridge_ip", port: 5001, user: "admin", password: "" }
  cam2:
    onvif: { host: "bridge_ip", port: 5002, user: "admin", password: "" }
```

### 2. Path-based (for WS-Discovery)

`http://bridge:port/onvif/{camera_name}/device_service`

Used automatically when WS-Discovery announces each camera with its
unique URL.

### 3. Single camera fallback

If only one camera is configured and no port/path match, the bridge
routes to it by default.

## Protocol Selection

Per-camera `ptz_protocol` field:

| Value | Behavior |
|-------|----------|
| `rtsp_cmd` | Intercept PTZ, send RTSP SET_PARAMETER/USER_CMD_SET |
| `onvif_native` | Forward PTZ to camera's ONVIF (passthrough) |

## Direction Mapping

| Direction | Standard | MIPS/ARM |
|-----------|----------|----------|
| Up | UP | UP |
| Down | DOWN | DWON |
| Left | LEFT | LEFT |
| Right | RIGHT | RIGHT |
| Stop | STOP | STOP |

## RTSP Formats

8 methods from `ptz_rtsp_cmd.py`. Auto-detection finds the first working
format + stream path on first use.

## Services

| Service | Namespace | Handling |
|---------|-----------|----------|
| Device | `ver10/device/wsdl` | Proxy to camera |
| Media | `ver10/media/wsdl` | Proxy to camera |
| PTZ | `ver20/ptz/wsdl` | Intercept (`rtsp_cmd`) or proxy (`onvif_native`) |
| Imaging | `ver20/imaging/wsdl` | Proxy to camera |
| Events | `ver10/events/wsdl` | Proxy to camera |
| DeviceIO | `ver10/deviceio/wsdl` | Proxy to camera |

## URL Structure

```
Port-based:   http://bridge:{port}/onvif/device_service
Path-based:   http://bridge:5000/onvif/{name}/device_service
WS-Discovery: UDP 239.255.255.250:3702 → ProbeMatch with per-camera XAddrs
```

## Project Structure

```
onvif_proxy_server/
├── config.example.json
├── Dockerfile
├── src/
│   ├── server.py
│   ├── camera/
│   │   ├── config.py
│   │   ├── registry.py
│   │   └── rtsp_client.py
│   └── onvif/
│       ├── templates.py
│       ├── ptz_handler.py
│       ├── proxy.py
│       ├── dispatcher.py
│       ├── http_server.py
│       └── wsdiscovery.py
├── tests/
└── docs/
```

## Usage

```bash
cp config.example.json config.json
# Edit config.json with your camera details

python -m src.server -c config.json -v

# Docker
docker build -t onvif-proxy-server .
docker run -d -p 5001:5001 -p 5002:5002 -p 3702:3702/udp \
  -v $(pwd)/config.json:/app/config.json onvif-proxy-server
```

## Frigate Configuration Example

```yaml
# frigate.yml
cameras:
  garage:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.1.100:554/onvif1
          roles: [record, detect]
    onvif:
      host: 192.168.1.200   # bridge IP
      port: 5001             # unique port per camera
      user: admin
      password: ""

  backyard:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.1.101:554/onvif1
          roles: [record, detect]
    onvif:
      host: 192.168.1.200
      port: 5002
      user: admin
      password: ""
```
