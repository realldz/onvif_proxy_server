import logging
import socket

log = logging.getLogger(__name__)

STREAMS = ['/onvif1', '/onvif2', '/h264', '/h264ES', '/']
TIMEOUT = 5

DIR_MAPPING = {
    'mips': {
        'up': 'UP', 'down': 'DWON', 'left': 'LEFT', 'right': 'RIGHT',
        'stop': 'STOP', 'auto': 'AUTO',
        'zoom_tele': 'ZOOM_TELE', 'zoom_wide': 'ZOOM_WIDE',
    },
    'arm': {
        'up': 'UP', 'down': 'DWON', 'left': 'LEFT', 'right': 'RIGHT',
        'stop': 'STOP', 'auto': 'AUTO',
        'zoom_tele': 'ZOOM_TELE', 'zoom_wide': 'ZOOM_WIDE',
    },
    'standard': {
        'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',
        'stop': 'STOP', 'auto': 'AUTO',
        'zoom_tele': 'ZOOM_TELE', 'zoom_wide': 'ZOOM_WIDE',
    },
}


def send_rtsp(host, port, raw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        s.connect((host, port))
        s.sendall(raw.encode())
        resp = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
            if b'\r\n\r\n' in resp:
                hdr, _, body = resp.partition(b'\r\n\r\n')
                cl = 0
                for line in hdr.split(b'\r\n'):
                    if line.lower().startswith(b'content-length:'):
                        cl = int(line.split(b':')[1].strip())
                        break
                if len(body) >= cl:
                    break
        return resp
    except socket.timeout:
        return b''
    except ConnectionRefusedError:
        return b''
    except Exception as e:
        log.debug('RTSP error: %s', e)
        return b''
    finally:
        s.close()


def fmt_content_type_trick(host, port, direction, stream):
    raw = (
        f'SET_PARAMETER rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'Content-type: ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


def fmt_ptzcmd_header(host, port, direction, stream):
    raw = (
        f'SET_PARAMETER rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


def fmt_user_cmd_body(host, port, direction, stream):
    body = f'ptzCmd: {direction}'
    raw = (
        f'USER_CMD_SET rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'Content-Type: text/parameters\r\n'
        f'Content-Length: {len(body)}\r\n'
        f'\r\n'
        f'{body}'
    )
    return send_rtsp(host, port, raw)


def fmt_user_cmd_header(host, port, direction, stream):
    raw = (
        f'USER_CMD_SET rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


def fmt_setparam_body(host, port, direction, stream):
    body = f'ptzCmd: {direction}'
    raw = (
        f'SET_PARAMETER rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'Content-Type: text/parameters\r\n'
        f'Content-Length: {len(body)}\r\n'
        f'\r\n'
        f'{body}'
    )
    return send_rtsp(host, port, raw)


def fmt_options_header(host, port, direction, stream):
    raw = (
        f'OPTIONS rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


def fmt_describe_header(host, port, direction, stream):
    raw = (
        f'DESCRIBE rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


def fmt_play_user_cmd(host, port, direction, stream):
    raw = (
        f'PLAY rtsp://{host}:{port}{stream} RTSP/1.0\r\n'
        f'CSeq: 1\r\n'
        f'USER_CMD_SET: ptzCmd: {direction}\r\n'
        f'\r\n'
    )
    return send_rtsp(host, port, raw)


FORMATS = [
    ('content_trick', fmt_content_type_trick),
    ('ptzcmd_header', fmt_ptzcmd_header),
    ('user_cmd_body', fmt_user_cmd_body),
    ('user_cmd_header', fmt_user_cmd_header),
    ('setparam_body', fmt_setparam_body),
    ('options_header', fmt_options_header),
    ('describe_header', fmt_describe_header),
    ('play_user_cmd', fmt_play_user_cmd),
]


class RtspPtzClient:
    def __init__(self, host, port=554, platform='mips', case='upper'):
        self.host = host
        self.port = port
        self.platform = platform
        self.case = case
        self._working = None

    def _resolve_direction(self, direction):
        dir_map = DIR_MAPPING.get(self.platform, DIR_MAPPING['standard'])
        val = dir_map.get(direction.lower(), direction.upper())
        if self.case == 'lower':
            val = val.lower()
        return val

    def auto_detect(self):
        for name, fmt_func in FORMATS:
            for stream in STREAMS:
                try:
                    resp = fmt_func(self.host, self.port, 'STOP', stream)
                    if b'200 OK' in resp:
                        self._working = (name, fmt_func, stream)
                        log.info('RTSP format found: %s [%s] for %s:%s', name, stream, self.host, self.port)
                        return True
                except Exception:
                    continue
        log.warning('No working RTSP format for %s:%s', self.host, self.port)
        return False

    def send_command(self, direction):
        dir_val = self._resolve_direction(direction)

        if self._working:
            _, fmt_func, stream = self._working
            resp = fmt_func(self.host, self.port, dir_val, stream)
            if b'200 OK' in resp:
                return True
            self._working = None

        if not self._working:
            self.auto_detect()

        if self._working:
            _, fmt_func, stream = self._working
            resp = fmt_func(self.host, self.port, dir_val, stream)
            return b'200 OK' in resp

        return False
