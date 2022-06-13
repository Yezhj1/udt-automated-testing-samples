import cv2 as cv
import numpy as np
import time
import socket
import struct
import threading
import os
import json
from uitrace.utils.env import DeviceEnv
from uitrace.device.android.dev_mgr import AndroidMgr
from uitrace.utils.log_handler import get_logger

logger = get_logger()

cur_dir = os.path.dirname(os.path.abspath(__file__))
MINICAP_PATH = os.path.join(cur_dir, "stf", "minicap")


# class Banner:
#     def __init__(self):
#         self.version = 0 # 版本信息
#         self.length = 0 # banner长度
#         self.pid = 0 # 进程ID
#         self.real_width = 0 # 设备真实宽度
#         self.real_height = 0 # 设备真实高度
#         self.virtual_width = 0 # 设备虚拟宽度
#         self.virtual_height = 0 # 设备虚拟高度
#         self.orientation = 0 # 设备方向
#         self.method = 0 # 设备信息获取策略
#
#     def get_info(self):
#         msg = {}
#         msg["version"] = self.version
#         msg["length"] = self.length
#         msg["pid"] = self.pid
#         msg["real_width"] = self.real_width
#         msg["real_height"] = self.real_height
#         msg["virtual_width"] = self.virtual_width
#         msg["virtual_height"] = self.virtual_height
#         msg["orientation"] = self.orientation
#         msg["method"] = self.method
#         return msg


class Minicap:
    def __init__(self):
        self.ip = None
        self.port = None
        self.max_size = 800
        self.banner = {}

        self.frame_img = None
        self.device_info = None
        self.svr_proc = None

        self.stream_thread = None # 获取画面线程
        self.conn = None # 获取画面的连接
        self.run_state = True # 获取画面线程运行状态

        # DeviceEnv.dev_mgr = AndroidMgr()
        self.dev_mgr = DeviceEnv.dev_mgr

        info = self.dev_mgr.cmd_adb("shell ls /data/local/tmp/minicap").communicate()
        for i in info:
            if "No such file" in str(i):
                self.setup()

    def setup(self):
        self.dev_mgr.cmd_adb("shell mkdir /data/local/tmp/").wait()
        cpu_info = self.dev_mgr.cmd_adb("shell getprop ro.product.cpu.abi").communicate()[0].strip()
        cpu_info = str(cpu_info, encoding='utf8')
        sdk_info = self.dev_mgr.cmd_adb("shell getprop ro.build.version.sdk").communicate()[0].strip()
        sdk_info = str(sdk_info, encoding='utf8')
        push_minicap = "push " + os.path.join(MINICAP_PATH, "bin", cpu_info, "minicap") + " /data/local/tmp"
        self.dev_mgr.cmd_adb(push_minicap).wait()
        push_so = "push " + os.path.join(MINICAP_PATH, "shared", "android-" + sdk_info, cpu_info, "minicap.so") + " /data/local/tmp"
        self.dev_mgr.cmd_adb(push_so).wait()
        self.dev_mgr.cmd_adb("shell chmod 777 /data/local/tmp/minicap").wait()
        self.dev_mgr.cmd_adb("shell chmod 777 /data/local/tmp/minicap.so").wait()

    def start(self, ip="127.0.0.1", port=1111, max_size=800):
        self.stop()

        self.ip = ip
        self.port = port
        self.max_size = max_size

        raw_info = self.dev_mgr.cmd_adb(
            "shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i").communicate()
        raw_info = str(raw_info[0], encoding='utf8')
        self.device_info = json.loads(raw_info)

        width = int(self.device_info["width"])
        height = int(self.device_info["height"])
        if height > width:
            ratio = self.max_size / height
            virtual_width = int(width * ratio)
            virtual_height = self.max_size
        else:
            ratio = self.max_size / width
            virtual_height = int(height * ratio)
            virtual_width = self.max_size
        rotation = self.device_info["rotation"]
        params = width, height, virtual_width, virtual_height, rotation
        minicap_param = "%dx%d@%dx%d/%d" % params
        start_minicap = "shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P " + minicap_param + " -S"
        self.svr_proc = self.dev_mgr.cmd_adb(start_minicap)
        time.sleep(0.5)

        self.dev_mgr.cmd_adb("forward tcp:" + str(self.port) + " localabstract:minicap").wait()

        # while self.stream_thread is not None and self.stream_thread.isAlive():
        #     time.sleep(0.01)
        self.run_state = True
        self.stream_thread = threading.Thread(target=self.minicap_stream)
        self.stream_thread.setDaemon(True)
        self.stream_thread.start()

        time.sleep(0.5)

    def recv_size(self, size, buf):
        while size - len(buf) > 0:
            buf += self.conn.recv(10240)
        return buf[:size], buf[size:]

    def minicap_stream(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.ip, self.port))

            buf = b''
            data_buf, buf = self.recv_size(24, buf)
            banner = struct.unpack("<2B5I2B", data_buf)
            self.banner = {}
            self.banner["version"] = banner[0]
            self.banner["length"] = banner[1]
            self.banner["pid"] = banner[2]
            self.banner["real_width"] = banner[3]
            self.banner["real_height"] = banner[4]
            self.banner["virtual_width"] = banner[5]
            self.banner["virtual_height"] = banner[6]
            self.banner["rotation"] = banner[7]
            self.banner["method"] = banner[8]

            while self.run_state:
                # 包长
                data_buf, buf = self.recv_size(4, buf)
                frame_size = struct.unpack("<I", data_buf)[0]

                # 包
                frame_data, buf = self.recv_size(frame_size, buf)
                self.frame_img = frame_data
        except:
            logger.exception("minicap stream error")
        finally:
            self.conn.close()

    def get_img(self):
        raw_data = self.frame_img
        if raw_data is None:
            return None
        np_data = np.frombuffer(raw_data, np.uint8)
        img = cv.imdecode(np_data, cv.IMREAD_COLOR)
        return img

    def get_info(self):
        return self.banner

    def stop(self):
        self.run_state = False

        # if self.banner.pid:
        #     self.dev_mgr.cmd_adb("shell kill -9 %s" % self.banner.pid).wait()

        if self.svr_proc is not None:
            self.svr_proc.kill()
            self.svr_proc = None

        self.dev_mgr.cmd_adb("shell killall -9 minicap").wait()

        # minicap_info = self.dev_mgr.cmd_adb("shell ps -ef /data/local/tmp/minicap").communicate()[0]
        # minicap_info = str(minicap_info, encoding='utf8')
        # minicap_info = minicap_info.strip().split("\n")
        # if len(minicap_info) > 1:
        #     idx = minicap_info[0].split().index("PID")
        #     pid = minicap_info[1].split()[idx]
        #     self.dev_mgr.cmd_adb("shell kill -9 " + pid).wait()

    # def minicap_stream(self):
    #     self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         self.conn.connect((self.ip, self.port))
    #         banner_len = 2
    #         banner_read = 0
    #         frame_read = 0
    #         frame_len = 0
    #         frame_data = b''
    #         while self.run_state:
    #             recv_data = self.conn.recv(4096)
    #             if not recv_data:
    #                 continue
    #             recv_len = len(recv_data)
    #             cursor = 0
    #             while cursor < recv_len:
    #                 if banner_read < banner_len:
    #                     if banner_read == 0:
    #                         self.banner.version = recv_data[cursor]
    #                     elif banner_read == 1:
    #                         banner_len = recv_data[cursor]
    #                         self.banner.length = banner_len
    #                     elif banner_read >= 2 and banner_read <= 5:
    #                         self.banner.pid += (recv_data[cursor] << ((banner_read - 2) * 8)) >> 0;
    #                     elif banner_read >= 6 and banner_read <= 9:
    #                         self.banner.real_width += (recv_data[cursor] << ((banner_read - 6) * 8)) >> 0;
    #                     elif banner_read >= 10 and banner_read <= 13:
    #                         self.banner.real_height += (recv_data[cursor] << ((banner_read - 10) * 8)) >> 0;
    #                     elif banner_read >= 14 and banner_read <= 17:
    #                         self.banner.virtual_width += (recv_data[cursor] << ((banner_read - 14) * 8)) >> 0;
    #                     elif banner_read >= 18 and banner_read <= 21:
    #                         self.banner.virtual_height += (recv_data[cursor] << ((banner_read - 18) * 8)) >> 0;
    #                     elif banner_read == 22:
    #                         self.banner.orientation = recv_data[cursor] * 90
    #                     elif banner_read == 23:
    #                         self.banner.method = recv_data[cursor]
    #                     cursor += 1
    #                     banner_read += 1
    #                     if banner_read == banner_len:
    #                         logger.info(self.banner.get_info())
    #                 elif frame_read < 4:
    #                     frame_len = frame_len + ((recv_data[cursor] << (frame_read * 8)) >> 0)
    #                     cursor += 1
    #                     frame_read += 1
    #                 else:
    #                     if recv_len - cursor >= frame_len:
    #                         frame_data = frame_data + recv_data[cursor:(cursor + frame_len)]
    #                         # self.frame_queue.put(frame_data)
    #                         self.frame_img = frame_data
    #                         cursor += frame_len
    #                         frame_len = 0
    #                         frame_read = 0
    #                         frame_data = b''
    #                     else:
    #                         frame_data = frame_data + recv_data[cursor:(cursor + frame_len)]
    #                         frame_len -= recv_len - cursor
    #                         frame_read += recv_len - cursor
    #                         cursor = recv_len
    #     except:
    #         logger.exception("minicap stream error")
    #     finally:
    #         self.conn.close()


# m = Minicap()
# m.start()
# for i in range(100000):
#     img = m.get_img()
#     if img is not None:
#         cv.imshow("test", img)
#     cv.waitKey(50)
#
# m.stop()
