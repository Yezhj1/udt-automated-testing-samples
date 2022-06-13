import socket
import time
import os
from uitrace.utils.env import DeviceEnv
from uitrace.device.android.dev_mgr import AndroidMgr
from uitrace.utils.log_handler import get_logger


logger = get_logger()


cur_dir = os.path.dirname(os.path.abspath(__file__))
MINITOUCH_PATH = os.path.join(cur_dir, "stf", "minitouch")


class Minitouch:
    def __init__(self):
        self.port = None
        self.cli = None
        self.svr_proc = None
        self.info = None

        # DeviceEnv.dev_mgr = AndroidMgr()
        self.dev_mgr = DeviceEnv.dev_mgr

        info = self.dev_mgr.cmd_adb("shell ls /data/local/tmp/minitouch").communicate()
        for i in info:
            if "No such file" in str(i):
                self.setup()

    def setup(self):
        self.dev_mgr.cmd_adb("shell mkdir /data/local/tmp/").wait()
        cpu_info = self.dev_mgr.cmd_adb("shell getprop ro.product.cpu.abi").communicate()[0].strip()
        cpu_info = str(cpu_info,encoding='utf8')
        push_cmd = "push " + os.path.join(MINITOUCH_PATH, cpu_info, "minitouch") + " /data/local/tmp"
        self.dev_mgr.cmd_adb(push_cmd).wait()
        self.dev_mgr.cmd_adb("shell chmod 777 /data/local/tmp/minitouch").wait()

    def start(self, ip="127.0.0.1", port = 1112):
        self.ip = ip
        self.port = port
        self.stop()

        self.svr_proc = self.dev_mgr.cmd_adb("shell /data/local/tmp/minitouch")
        time.sleep(1)
        self.dev_mgr.cmd_adb("forward tcp:" + str(self.port) + " localabstract:minitouch").wait()

        self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cli.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.cli.connect((self.ip, self.port))

    def set_info(self, info):
        self.info = info

    def pos_map(self, pos):
        rotation = self.info["rotation"]
        width = self.info["real_width"]
        height = self.info["real_height"]
        if rotation == 0:
            return pos
        elif rotation == 1:
            return [width - pos[1], pos[0]]
        elif rotation == 2:
            return [width - pos[0], height - pos[1]]
        elif rotation == 3:
            return [pos[1], height - pos[0]]

    def touch_down(self, pos, id=0, pressure=50):
        pos = self.pos_map(pos)
        cmd = "d %s %s %s %s\nc\n" % (id, pos[0], pos[1], pressure)
        self.cli.send(cmd.encode())

    def touch_move(self, pos, id=0, pressure=50):
        pos = self.pos_map(pos)
        cmd = "m %d %d %d %d\nc\n" % (id, pos[0], pos[1], pressure)
        self.cli.send(cmd.encode())

    def touch_up(self, id=0):
        cmd = "u %d\nc\n" % (id)
        self.cli.send(cmd.encode())

    def stop(self):
        if self.cli is not None:
            self.cli.close()
            self.cli = None

        if self.svr_proc is not None:
            self.svr_proc.kill()
            self.svr_proc = None

        self.dev_mgr.cmd_adb("shell killall -9 minitouch").wait()

        # minitouch_info = self.dev_mgr.cmd_adb(self.adb + " shell ps -ef /data/local/tmp/minitouch", stdout=subprocess.PIPE).communicate()[0]
        # minitouch_info = str(minitouch_info, encoding='utf8')
        # minitouch_info = minitouch_info.strip().split("\n")
        # if len(minitouch_info) > 1:
        #     idx = minitouch_info[0].split().index("PID")
        #     pid = minitouch_info[1].split()[idx]
        #     self.dev_mgr.cmd_adb(self.adb + " shell kill -9 " + pid).wait()

    # def click(self, pos):
    #     cmd = ""
    #     for i in pos:
    #         cmd += "d 0 %d %d 50\nc\n" % (int(i[0] * self.x_ratio), int(i[1] * self.y_ratio))
    #     cmd += "u 0\nc\n"
    #     self.cli.send(cmd.encode())
    #
    # def swipe(self, x1, y1, x2, y2, steps=20):
    #     x1, y1, x2, y2 = map(int, (x1*self.x_ratio, y1*self.y_ratio, x2*self.x_ratio, y2*self.y_ratio))
    #     dx = (x2-x1)/steps
    #     dy = (y2-y1)/steps
    #     self.cli.send(("d 0 %d %d 30\nc\n" % (x1, y1)).encode())
    #     for i in range(steps-1):
    #         x, y = x1+(i+1)*dx, y1+(i+1)*dy
    #         self.cli.send(("m 0 %d %d 30\nc\n" % (x, y)).encode())
    #     self.cli.send(("u 0 %d %d 30\nc\nu 0\nc\n" % (x2, y2)).encode())

# m = Minitouch()
# m.start()
# m.touch_down([100, 100])
# time.sleep(0.5)
# m.touch_up()