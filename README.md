# ONVIF Proxy Server

[![Tests](https://github.com/realldz/onvif_proxy_server/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/realldz/onvif_proxy_server/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

A lightweight, zero-dependency proxy server that bridges standard ONVIF clients (such as **Frigate NVR**) with IP cameras that have incomplete, broken, or non-standard ONVIF implementations (e.g., Yoosee MIPS/ARM cameras).

The server intercepts ONVIF PTZ SOAP commands and translates them into camera-specific RTSP commands (e.g., `SET_PARAMETER` / `USER_CMD_SET` with `ptzCmd`), while proxying all standard non-PTZ requests (Device, Media, Imaging, etc.) directly to the camera's native ONVIF endpoints.

---

## 🗺️ Architecture & Flow

```mermaid
graph TD
    subgraph Client
        Frigate[Frigate NVR / ONVIF Client]
    end

    subgraph Proxy ["ONVIF Proxy Server (Port 5000 / 5001 / 5002)"]
        WS[WS-Discovery Server]
        HTTP[HTTP ONVIF Router]
        PTZ[PTZ Handler]
        RTSP[RTSP PTZ Client]
    end

    subgraph Cameras
        CamA[Camera A: MIPS Yoosee]
        CamB[Camera B: ARM Yoosee]
    end

    Frigate -->|WS-Discovery Probe| WS
    Frigate -->|ONVIF SOAP Device/Media| HTTP
    HTTP -->|Proxy Direct| CamA
    HTTP -->|Proxy Direct| CamB
    
    Frigate -->|ONVIF SOAP PTZ| HTTP
    HTTP -->|Intercept PTZ| PTZ
    PTZ -->|Translate PTZ| RTSP
    RTSP -->|RTSP ptzCmd SET_PARAMETER| CamA
    RTSP -->|RTSP ptzCmd USER_CMD_SET| CamB
```

* **Non-PTZ requests** (e.g., retrieving stream profiles, device information, etc.) are dynamically proxied to the camera's native ONVIF service.
* **PTZ requests** (if configured with `ptz_protocol=rtsp_cmd`) are intercepted, converted into raw RTSP PTZ requests, and sent directly to the camera's RTSP endpoint.

---

## ⚡ Features

* **Zero-Dependency Runtime**: Built entirely using Python's standard library (`socket`, `http.server`, `xml.etree`, etc.). No external pip packages are required to run the server.
* **Smart Camera Routing**: Supports three methods for identifying cameras:
  1. **Port-based routing** (Recommended): Assigns a dedicated port on the proxy to each camera.
  2. **Path-based routing**: Access cameras via unique URLs (e.g., `/onvif/{camera_name}/device_service`).
  3. **Fallback routing**: Automatically routes to the single configured camera if only one exists.
* **WS-Discovery Server**: Built-in discovery daemon responder (UDP port `3702`) that replies with camera-specific HTTP endpoints.
* **Auto-Detect RTSP Methods**: Automatically probes and detects the camera's working RTSP connection methods and stream paths.
* **MIPS/ARM Direction Correction**: Handles vendor-specific direction spelling differences (such as `DWON` for down on MIPS platforms).
* **Lightweight Container**: Ready-to-go minimal Docker footprint based on Python Alpine.

---

## 🚀 Quick Start

### Method 1: Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/realldz/onvif_proxy_server.git
   cd onvif_proxy_server
   ```

2. **Configure the cameras:**
   Copy the example config and adjust it with your camera details:
   ```bash
   cp config.example.json config.json
   ```
   *Edit `config.json` using your preferred text editor (see [Configuration](#-configuration) below).*

3. **Run the server:**
   ```bash
   python -m src.server -c config.json -v
   ```
   *The `-v` (verbose) flag enables debug logs, which are extremely helpful for testing RTSP connections.*

---

### Method 2: Docker Setup

1. **Build the Docker Image:**
   ```bash
   docker build -t onvif-proxy-server .
   ```

2. **Run the Container:**
   ```bash
   docker run -d \
     --name onvif-proxy \
     --network host \
     -v $(pwd)/config.json:/app/config.json \
     onvif-proxy-server
   ```
   > [!NOTE]
   > Running with `--network host` is highly recommended to allow the WS-Discovery daemon to receive multicast UDP packets on port `3702`. If not using host networking, make sure to map the HTTP port range (e.g., `5000-5005`) and `3702/udp`.

---

## ⚙️ Configuration

An example configuration file is provided in `config.example.json`.

```json
{
  "bind_host": "0.0.0.0",
  "bind_port": 5000,
  "cameras": [
    {
      "name": "yoosee_mips",
      "bind_port": 5001,
      "onvif_host": "192.168.1.102",
      "onvif_port": 5000,
      "rtsp_host": "192.168.1.102",
      "rtsp_port": 554,
      "username": "admin",
      "password": "",
      "platform": "mips",
      "ptz_protocol": "rtsp_cmd",
      "rtsp_cmd_config": {
        "case": "upper",
        "direction_mapping": "mips"
      }
    },
    {
      "name": "yoosee_arm",
      "bind_port": 5002,
      "onvif_host": "192.168.1.101",
      "onvif_port": 80,
      "rtsp_host": "192.168.1.101",
      "rtsp_port": 554,
      "username": "admin",
      "password": "",
      "platform": "arm",
      "ptz_protocol": "onvif_native"
    }
  ]
}
```

### Parameter Reference

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `bind_host` | string | `0.0.0.0` | IP address for the proxy server to bind to. |
| `bind_port` | integer | `5000` | Base HTTP port for the proxy. |
| `cameras` | array | `[]` | List of camera configuration objects. |

#### Camera Parameters

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | string | **Required** | A unique, URL-safe name for the camera. |
| `bind_port` | integer | Optional | Dedicated proxy port for this camera (highly recommended). |
| `onvif_host` | string | **Required** | The camera's physical IP address. |
| `onvif_port` | integer | `80` | The camera's native ONVIF SOAP port. |
| `rtsp_host` | string | Matches `onvif_host` | The camera's physical RTSP host. |
| `rtsp_port` | integer | `554` | The camera's RTSP port. |
| `username` | string | `"admin"` | Username for camera authentication. |
| `password` | string | `""` | Password for camera authentication. |
| `platform` | string | `"arm"` | Camera hardware chipset (`"mips"` or `"arm"`). |
| `ptz_protocol` | string | `"rtsp_cmd"` | PTZ intercept behavior (`"rtsp_cmd"` to translate to RTSP, or `"onvif_native"` to pass SOAP directly). |
| `rtsp_cmd_config` | object | Optional | Adjust commands: `case` (`"upper"`/`"lower"`) and `direction_mapping` (`"mips"` maps Down to `DWON`). |

---

## 🦌 Frigate NVR Integration

To integrate with Frigate, use the proxy server's dedicated `bind_port` for each camera in your `frigate.yml`:

```yaml
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://admin:password@192.168.1.102:554/onvif1
          roles:
            - detect
            - record
    onvif:
      host: 192.168.1.200    # The IP address of the ONVIF Proxy Server
      port: 5001             # The bind_port assigned to front_door
      user: admin
      password: "your_password"

  backyard:
    ffmpeg:
      inputs:
        - path: rtsp://admin:password@192.168.1.101:554/onvif1
          roles:
            - detect
            - record
    onvif:
      host: 192.168.1.200    # The IP address of the ONVIF Proxy Server
      port: 5002             # The bind_port assigned to backyard
      user: admin
      password: "your_password"
```

---

## 🧪 Testing

The proxy server has a comprehensive suite of unit tests covering configuration parsing, request routing/dispatching, SOAP proxying, and PTZ conversion logic.

To run the unit tests, run:
```bash
python -m unittest discover -s tests
```

---

## 📁 Repository Structure

```
onvif_proxy_server/
├── config.example.json    # Example configuration template
├── Dockerfile             # Alpine-based runtime container definition
├── README.md              # Project documentation
├── docs/
│   └── architecture.md    # Detailed internal design and protocols
├── src/
│   ├── server.py          # Server daemon entry point
│   ├── camera/
│   │   ├── config.py      # Config loading and default mapping
│   │   ├── registry.py    # Memory store for active cameras
│   │   └── rtsp_client.py # Low-level RTSP socket client for PTZ commands
│   └── onvif/
│       ├── dispatcher.py  # SOAP router and action identifier
│       ├── http_server.py # Base HTTPServer implementation
│       ├── proxy.py       # SOAP relay middleware
│       ├── ptz_handler.py # PTZ SOAP interpreter & parser
│       ├── templates.py   # XML response templates
│       └── wsdiscovery.py # UDP WS-Discovery responder daemon
└── tests/                 # Unit test coverage
```

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
