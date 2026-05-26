# ONVIF Proxy Server - Architecture

## Overview

ONVIF Proxy Server bridges Frigate NVR with cameras that have broken or
incomplete ONVIF implementations. It presents a standard ONVIF interface to
Frigate while translating PTZ commands to camera-specific RTSP messages.

## Architecture

```
Frigate --ONVIF SOAP--> onvif-bridge:5000 --RTSP ptzCmd--> Camera:554
                             |
                             |--HTTP proxy--> Camera:80/5000 (Device, Media, Imaging)
```

- **Non-PTZ** requests (DeviceInfo, MediaProfiles, StreamUri, Imaging, Events)
  are proxied to the camera's native ONVIF endpoint
- **PTZ** requests (ContinuousMove, Stop, GetPresets, GetStatus, etc.) are
  intercepted and handled via RTSP `SET_PARAMETER`/`USER_CMD_SET` with `ptzCmd` header

## Protocol Selection

Per-camera config supports two PTZ protocols:

| Protocol | Description |
|----------|-------------|
| `onvif_native` | Forward PTZ to camera's ONVIF (passthrough) |
| `rtsp_cmd` | Translate PTZ to RTSP custom commands |

## Direction Mapping

Cameras use non-standard spelling for directions:

| Direction | Standard | MIPS/ARM |
|-----------|----------|----------|
| Up | UP | UP |
| Down | DOWN | DWON (typo in firmware) |
| Left | LEFT | LEFT |
| Right | RIGHT | RIGHT |
| Stop | STOP | STOP |

## RTSP Formats

The server tries multiple RTSP methods (ported from `ptz_rtsp_cmd.py`):

1. `SET_PARAMETER` + `Content-type: ptzCmd: <dir>` (PHP-style trick)
2. `SET_PARAMETER` + header `ptzCmd: <dir>`
3. `USER_CMD_SET` + body `ptzCmd: <dir>`
4. `USER_CMD_SET` + header `ptzCmd: <dir>`
5. `SET_PARAMETER` + body `ptzCmd: <dir>`
6. `OPTIONS` + `ptzCmd` header
7. `DESCRIBE` + `ptzCmd` header
8. `PLAY` + `USER_CMD_SET` header

Auto-detection finds the first working format + stream path.

## Services

| Service | Namespace | Handling |
|---------|-----------|----------|
| Device | `ver10/device/wsdl` | Proxy to camera |
| Media | `ver10/media/wsdl` | Proxy to camera |
| PTZ | `ver20/ptz/wsdl` | Intercept (rtsp_cmd) or Proxy (onvif_native) |
| Imaging | `ver20/imaging/wsdl` | Proxy to camera |
| Events | `ver10/events/wsdl` | Proxy to camera |
| DeviceIO | `ver10/deviceio/wsdl` | Proxy to camera |

## API

### URL Structure

```
http://{bridge}:{port}/onvif/{camera_name}/device_service
http://{bridge}:{port}/onvif/{camera_name}/media_service
http://{bridge}:{port}/onvif/{camera_name}/ptz_service
```

### WS-Discovery

UDP multicast `239.255.255.250:3702`. Responds to Probe with a ProbeMatch
for each configured camera.

## Project Structure

```
onvif_proxy_server/
├── config.example.json   # Example configuration
├── Dockerfile            # Container build
├── src/
│   ├── server.py         # Entry point
│   ├── camera/
│   │   ├── config.py     # JSON config loader
│   │   ├── registry.py   # Camera lookup
│   │   └── rtsp_client.py # RTSP PTZ client
│   └── onvif/
│       ├── templates.py  # SOAP XML templates
│       ├── ptz_handler.py # PTZ action handler
│       ├── proxy.py       # HTTP proxy to camera
│       ├── dispatcher.py  # SOAP action resolver
│       ├── http_server.py # HTTP server + handler
│       └── wsdiscovery.py # WS-Discovery responder
├── tests/
│   ├── test_rtsp_client.py
│   ├── test_ptz_handler.py
│   ├── test_dispatcher.py
│   ├── test_config.py
│   └── test_registry.py
└── docs/
    └── architecture.md
```

## Usage

```bash
# Create config from example
cp config.example.json config.json
# Edit config.json with your camera details

# Run
python -m src.server -c config.json -v

# Docker
docker build -t onvif-proxy-server .
docker run -d -p 5000:5000 -p 3702:3702/udp -v $(pwd)/config.json:/app/config.json onvif-proxy-server
```

## Frigate Configuration

```yaml
cameras:
  my_camera:
    ffmpeg:
      inputs:
        - path: rtsp://192.168.1.100:554/onvif1
          roles:
            - record
            - detect
    onvif:
      host: 192.168.1.200  # Bridge server IP
      port: 5000
      user: admin
      password: ""
    # Custom ONVIF path (if not using WS-Discovery)
    # onvif_url: http://192.168.1.200:5000/onvif/camera_name/device_service
```
