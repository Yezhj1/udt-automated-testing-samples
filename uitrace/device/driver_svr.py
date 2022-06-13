import socket
import struct
import json
import time
import threading
import cv2 as cv
import numpy as np
from uitrace.utils.log_handler import get_logger

logger = get_logger()


def recv_size(conn, size, buf):
    while size - len(buf) > 0:
        buf += conn.recv(10240)
    return buf[:size], buf[size:]


def send_bytes(conn, data):
    size = len(data)
    size_buf = struct.pack(">I", size)
    conn.sendall(size_buf + data)


def img2bytes(img):
    result, img_bytes = cv.imencode(".jpg", img)
    img_bytes = np.array(img_bytes).tobytes()
    return img_bytes


def bytes2img(img_bytes):
    img = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv.imdecode(img, cv.IMREAD_COLOR)
    return img


class DriverSvr:
    def __init__(self):
        self.svr = None
        self.ip = None
        self.port = None
        self.ifs = None
        self.driver = None
        self.ga_driver = None
        self.svr_run = True
        # self.cfg = proj_env.get_config()

    def set_driver(self, driver):
        self.driver = driver

    def worker(self, conn):
        buf = b''
        run_state = True
        while run_state and self.svr_run:
            try:
                # 包长
                data_buf, buf = recv_size(conn, 4, buf)
                pkg_size = struct.unpack(">I", data_buf)[0]

                # 包
                data_buf, buf = recv_size(conn, pkg_size, buf)
                pkg = json.loads(data_buf.decode("utf-8"))

                logger.info("svr recv: %s" % str(pkg))
            except Exception:
                logger.exception("recv error")
                break
            try:
                if pkg["cmd"] == "screen_stream":
                    while run_state and self.svr_run:
                        img = self.driver.get_img()
                        if img is not None:
                            img_bytes = img2bytes(img)
                            send_bytes(conn, img_bytes)
                        # frame_interval = float(self.cfg["ide"]["frame_interval"])
                        time.sleep(self.ifs)
                elif pkg["cmd"] == "screenshot":
                    # img = cv.imread("D:/Zero/Project/zios/uitrace/test/img_1.jpg")
                    for i in range(5):
                        img = self.driver.get_img()
                        if img is not None:
                            img_bytes = img2bytes(img)
                            send_bytes(conn, img_bytes)
                            break
                        time.sleep(0.2)
                elif pkg["cmd"] == "click":
                    self.driver.click_pos(pkg["pos"], duration=pkg["duration"])
                    send_bytes(conn, json.dumps({"cmd": "click"}).encode("utf-8"))
                elif pkg["cmd"] == "slide":
                    self.driver.slide_pos(pkg["pos_from"], pkg["pos_to"], duration=pkg["duration"])
                    send_bytes(conn, json.dumps({"cmd": "slide"}).encode("utf-8"))
                elif pkg["cmd"] == "home":
                    self.driver.press_home()
                    send_bytes(conn, json.dumps({"cmd": "home"}).encode("utf-8"))
                elif pkg["cmd"] == "press":
                    self.driver.press(pkg["name"])
                    send_bytes(conn, json.dumps({"cmd": "press"}).encode("utf-8"))
                elif pkg["cmd"] == "touch_down":
                    self.driver.touch_down(pkg["pos"], id=pkg["id"], pressure=pkg["pressure"])
                    send_bytes(conn, json.dumps({"cmd": "touch_down"}).encode("utf-8"))
                elif pkg["cmd"] == "touch_move":
                    self.driver.touch_move(pkg["pos"], id=pkg["id"], pressure=pkg["pressure"])
                    send_bytes(conn, json.dumps({"cmd": "touch_move"}).encode("utf-8"))
                elif pkg["cmd"] == "touch_up":
                    self.driver.touch_up(id=pkg["id"], pressure=pkg["pressure"])
                    send_bytes(conn, json.dumps({"cmd": "touch_up"}).encode("utf-8"))
                elif pkg["cmd"] == "touch_reset":
                    self.driver.touch_reset()
                    send_bytes(conn, json.dumps({"cmd": "touch_reset"}).encode("utf-8"))
                elif pkg["cmd"] == "uitree":
                    uitree_data = None
                    try:
                        uitree_data = self.driver.get_uitree()
                    except Exception:
                        logger.exception("request error")
                    res = {
                        "cmd": "uitree",
                        "uuid": pkg["uuid"] if "uuid" in pkg else "",
                        "result": uitree_data
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "input_text":
                    self.driver.input_text(None, pkg["text"])
                    res = {
                        "cmd": "input_text",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "current_app":
                    app = self.driver.current_app()
                    res = {
                        "cmd": "current_app",
                        "result": app
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "start_app":
                    bundle_id = str(pkg['bundle_id'])
                    result = self.driver.start_app(bundle_id)
                    res = {
                        "cmd": "start_app",
                        "result": result
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "refresh_screen":
                    self.driver.init_sess()
                    if hasattr(self.driver, "screen") and hasattr(self.driver.screen, "stop_stream"):
                        self.driver.screen.stop_stream()
                        self.driver.screen.start_stream()
                    res = {
                        "cmd": "refresh_screen",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "start_ga":
                    os_type = int(pkg['os_type'])
                    engine_type = int(pkg['engine_type'])
                    result = self.init_ga(os_type, engine_type)
                    res = {
                        "cmd": "start_ga",
                        "result": result
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "ga_tree":
                    result = None
                    # 获取画面可能影响其他功能，待进一步排查 zerodyli
                    # stopped = False
                    # if hasattr(self.driver, "screen") and hasattr(self.driver.screen, "stop_stream"):
                    #     self.driver.screen.stop_stream()
                    #     stopped = True
                    if self.ga_driver is not None:
                        try:
                            result = self.ga_driver.get_uitree()
                        except Exception:
                            logger.exception("request error")
                    # if stopped:
                    #     self.driver.screen.start_stream()
                    res = {
                        "cmd": "ga_tree",
                        "uuid": pkg["uuid"] if "uuid" in pkg else "",
                        "result": result
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "stop_ga":
                    if self.ga_driver is not None:
                        self.ga_driver.stop_driver()
                        self.ga_driver = None
                    res = {
                        "cmd": "stop_ga",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "close":
                    run_state = False
                    res = {
                        "cmd": "close",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "close_all":
                    self.svr_run = False
                    run_state = False
                    res = {
                        "cmd": "close_all",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
                elif pkg["cmd"] == "init_sess":
                    self.driver.init_sess()
                    res = {
                        "cmd": "init_sess",
                        "result": True
                    }
                    send_bytes(conn, json.dumps(res).encode("utf-8"))
            except Exception:
                logger.exception("command error")
        conn.close()
        logger.info("connect close")

    def init_ga(self, os_type, engine_type):
        try:
            if self.ga_driver is not None:
                self.ga_driver.stop_driver()
                self.ga_driver = None
            from uitrace.device.ga.ga_mgr import GADriver
            from uitrace.utils.toolkit import get_free_ports
            self.ga_driver = GADriver()
            port = get_free_ports(1)[0]
            self.ga_driver.start_driver(port=port, os_type=os_type, engine_type=engine_type)
            return True
        except Exception:
            logger.exception("init ga error")
            if self.ga_driver is not None:
                self.ga_driver.stop_driver()
                self.ga_driver = None
            return False

    def start_svr(self, ip="127.0.0.1", port=8400, ifs=0.05):
        self.ip = ip
        self.port = port
        self.ifs = ifs
        self.svr_run = True

        self.svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # timeval = struct.pack('ll', 5000, 0)
        # self.svr.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.svr.bind((self.ip, self.port))
        self.svr.listen(5)
        logger.info("svr start")
        while self.svr_run:
            conn, addr = self.svr.accept()
            logger.info("svr accept")
            t = threading.Thread(target=self.worker, args=(conn,))
            t.start()
        self.svr.close()
        self.driver = None


class DriverClient:
    def __init__(self, ip="127.0.0.1", port=8400):
        self.ip = ip
        self.port = port

    def connect(self):
        self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # timeval = struct.pack('ll', 5000, 0)
        # self.cli.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.cli.connect((self.ip, self.port))

    def get_img(self):
        try:
            cmd = {"cmd": "screenshot"}
            data = json.dumps(cmd).encode("utf-8")
            send_bytes(self.cli, data)

            buf = b''
            data_buf, buf = recv_size(self.cli, 4, buf)
            frame_size = struct.unpack(">I", data_buf)[0]

            frame_bytes, buf = recv_size(self.cli, frame_size, buf)
            # frame_bytes = json.loads(data_buf.decode("utf-8"))
            img = bytes2img(frame_bytes)
            return img
        except Exception:
            logger.exception("get frame failed")
            return None
        return None

    def touch_down(self, pos, id=0, pressure=50):
        cmd = {"cmd": "touch_down", "pos": pos, "id": id, "pressure": pressure}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def touch_move(self, pos, id=0, pressure=50):
        cmd = {"cmd": "touch_move", "pos": pos, "id": id, "pressure": pressure}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def touch_up(self, pos=None, id=0, pressure=50):
        cmd = {"cmd": "touch_up", "pos": pos, "id": id, "pressure": pressure}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def touch_reset(self):
        cmd = {"cmd": "touch_reset"}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def click(self, pos, duration=0.05):
        cmd = {"cmd": "click", "pos": pos, "duration": duration}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def slide(self, pos_from, pos_to, duration=0.05):
        cmd = {"cmd": "slide", "pos_from": pos_from, "pos_to": pos_to, "duration": duration}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def init_sess(self):
        cmd = {"cmd": "init_sess"}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def get_uitree(self):
        cmd = {"cmd": "uitree", "uuid": 0}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

        buf = b''
        # 包长
        data_buf, buf = recv_size(self.cli, 4, buf)
        pkg_size = struct.unpack(">I", data_buf)[0]

        # 包
        data_buf, buf = recv_size(self.cli, pkg_size, buf)
        pkg = json.loads(data_buf.decode("utf-8"))
        return pkg["result"]

    def close_all(self):
        cmd = {"cmd": "close_all"}
        data = json.dumps(cmd).encode("utf-8")
        send_bytes(self.cli, data)

    def disconnect(self):
        self.cli.close()
