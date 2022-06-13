import cv2 as cv
import numpy as np
import os
import re
import signal
import socket
import struct
import threading
import time
import wda
from uitrace.utils.env import DeviceEnv
from uitrace.utils.toolkit import cmd_raw
from uitrace.utils.log_handler import get_logger

logger = get_logger()

buf_size = 100000
start_bytes = b"Content-Length: ([0-9]+)\r\n\r\n"
start_len = len(start_bytes)


def resize_max(img, max_size):
    sp = img.shape
    if sp[0] > sp[1]:
        dsize = (int(sp[1] * max_size / sp[0]), max_size)
    else:
        dsize = (max_size, int(sp[0] * max_size / sp[1]))
    return cv.resize(img, dsize)


class WDAScreen:
    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = 8200
        self.max_size = 800
        self.img_cache = None
        self.t = None
        self.stream_run = True

    def start_stream(self, ip="127.0.0.1", port=8200, max_size=800):
        self.ip = ip
        self.port = port
        self.max_size = max_size
        self.stream_run = True
        self.t = threading.Thread(target=self.stream_thread)
        self.t.start()

    def stop_stream(self):
        self.stream_run = False
        self.t.join()
        self.t = None

    def stream_thread(self):
        # 断线重连
        while self.stream_run:
            frame_len = -1
            head_len = -1

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            timeval = struct.pack('ll', 10000, 0)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
            s.connect((self.ip, self.port))
            s.send(b'start send jpeg')
            raw_data = b''
            try:
                while self.stream_run:
                    data = s.recv(buf_size)
                    if not data:
                        logger.warning("wda screen svr closed")
                        break
                    raw_data += data
                    if head_len > 0:
                        raw_data = raw_data[head_len:]
                    else:
                        re_result = re.search(start_bytes, raw_data)
                        if re_result:
                            frame_len = int(re_result.group(1))
                            raw_data = raw_data[re_result.span()[1]:]

                    if len(raw_data) >= frame_len and frame_len > 0:
                        frame_data = raw_data[:frame_len]
                        raw_data = raw_data[frame_len:]

                        file_bytes = np.asarray(bytearray(frame_data), dtype=np.uint8)
                        img = cv.imdecode(file_bytes, cv.IMREAD_COLOR)
                        # sp = img.shape
                        # if sp[0] > sp[1]:
                        #     dsize = (int(sp[1] * self.max_size / sp[0]), self.max_size)
                        # else:
                        #     dsize = (self.max_size, int(sp[0] * self.max_size / sp[1]))
                        # self.img_cache = cv.resize(img, dsize)
                        self.img_cache = resize_max(img, self.max_size)

                        # self.img_cache = img.copy()
                        # self.img_cache = img
            except:
                logger.exception("WDAScreen error")
                time.sleep(1)
            s.close()

    def get_img(self):
        return self.img_cache


class WDACtrl:
    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = 8100
        self.ctrl_run = True
        self.cli = None
        self.max_size = None
        self.sess = None

    def start_ctrl(self, ip="127.0.0.1", port=8100, max_size=None):
        self.ip = ip
        self.port = port
        self.max_size = max_size

        self.ctrl_run = True
        self.cli = wda.Client("http://" + self.ip + ":" + str(self.port))

        if not self.cli.wait_ready(timeout=20):
            logger.error("wda xctest launched but check failed")

        # self.sess = self.cli.session("com.apple.Preferences")
        # self.sess = self.cli.session("com.apple.mobiletimer")
        # self.sess.home()
        # self.sess = self.cli.session()
        # self.sess.appium_settings({"mjpegScalingFactor": 60})

        # t = threading.Thread(args=self.health_check)
        # t.start()

    # def health_check(self):
    #     while self.ctrl_run:
    #         time.sleep(1)
    #         if not self.cli.is_ready():
    #             pass

    def health_check(self):
        if not self.cli.is_ready():
            self.cli = wda.Client("http://" + self.ip + ":" + str(self.port))

    def get_img(self, max_size=None):
        img = None
        try:
            img = self.cli.screenshot()
        except:
            logger.exception("get img failed")
        if img is not None and (max_size or self.max_size):
            msize = max_size if max_size else self.max_size
            img = cv.cvtColor(np.asarray(img), cv.COLOR_RGB2BGR)
            img_cache = resize_max(img, msize)
            return img_cache
        return img

    def stop_ctrl(self):
        self.ctrl_run = False
        if self.cli:
            self.cli.close()
            self.cli = None


class WDAMgr:
    def __init__(self):
        self.bundle_id = None
        self.screen = None
        self.ctrl = None

        self.wda_proc = None
        self.relay_proc = None

    def start_wda(self, bundle_id=None, ip="127.0.0.1", screen_port=8200, ctrl_port=8100, max_size=800):
        self.bundle_id = bundle_id
        self.ip = ip
        self.screen_port = screen_port
        self.ctrl_port = ctrl_port
        self.max_size = max_size

        logger.info("device wda starting")

        self.wda_proc = DeviceEnv.dev_mgr.init_wda(bundle_id=self.bundle_id, port=self.ctrl_port)
        self.relay_proc = DeviceEnv.dev_mgr.forward_port(self.screen_port, 9100)
        time.sleep(3)

        # cmd = ['wdaproxy']
        # if self.bundle_id:
        #     cmd.extend(['-B', self.bundle_id])
        # # if self.ctrl_port:
        # #     cmd.extend(['-e', 'USB_PORT:' + str(self.ctrl_port)])
        # if self.ctrl_port:
        #     cmd += ['--port', str(self.ctrl_port)]
        # self.wda_proc = DeviceEnv.dev_mgr.cmd_tid(cmd)
        # self.relay_proc = cmd_raw(["tidevice", "relay", str(self.screen_port), "9100"])
        # time.sleep(3)
        # if self.wda_proc.poll() is not None:
        #     logger.warning("device wda start failed")
        #     return False

        logger.info("device wda start done")
        return True

    def connect(self):
        logger.info("wda connecting")
        self.ctrl = WDACtrl()
        self.ctrl.start_ctrl(ip=self.ip, port=self.ctrl_port)

        self.screen = WDAScreen()
        self.screen.start_stream(ip=self.ip, port=self.screen_port, max_size=self.max_size)

        logger.info("wda connect done")
        return True

    def disconnect(self):
        if self.screen:
            self.screen.stop_stream()
            self.screen = None
        if self.ctrl:
            self.ctrl.stop_ctrl()
            self.ctrl = None
        time.sleep(1)

    def stop_wda(self):
        try:
            # os.kill(self.wda_proc.pid, signal.CTRL_C_EVENT)
            # os.kill(self.relay_proc.pid, signal.CTRL_C_EVENT)
            if self.wda_proc:
                self.wda_proc.kill()
                self.wda_proc = None
            if self.relay_proc:
                self.relay_proc.kill()
                self.relay_proc = None
        except:
            pass
        # os.popen('taskkill -f -pid %s' % self.wda_proc.pid)
        # os.popen('taskkill -f -pid %s' % self.relay_proc.pid)
        # time.sleep(1)

