import time
from uitrace.device.android.scrcpy.scrcpy_mgr import ScrcpyMgr
from uitrace.device.android.stf.stf_mgr import STFMgr
from uitrace.utils.param import RunMode, DriverLib
from uitrace.device.driver_svr import DriverClient
from uitrace.utils.toolkit import get_free_ports
from uitrace.utils.env import DeviceEnv


class AndroidDriver():
    def __init__(self):
        self.driver = None
        self.mode = None
        self.screen_port = None
        self.ctrl_port = None

    def start_driver(self, ip="127.0.0.1", screen_port=8200, ctrl_port=8100, max_size=800, mode=RunMode.SINGLE,
                     driver_lib=DriverLib.SCRCPY):
        self.mode = mode
        if mode == RunMode.IDE:
            self.screen_port = screen_port
            self.driver = DriverClient(ip=ip, port=self.screen_port)
            self.driver.connect()
        elif mode == RunMode.SINGLE:
            if not screen_port and not ctrl_port:
                ports = get_free_ports(2)
                self.screen_port = ports[0]
                self.ctrl_port = ports[1]
            else:
                self.screen_port = screen_port if screen_port else get_free_ports(1)[0]
                self.ctrl_port = ctrl_port if ctrl_port else get_free_ports(1)[0]
            if not driver_lib:
                sdk_ver = DeviceEnv.dev_mgr.get_sdk_ver()
                if sdk_ver >= 21:
                    self.driver = ScrcpyMgr(max_size=max_size, port=self.screen_port)
                    self.driver.start()
                else:
                    self.driver = STFMgr()
                    self.driver.start(max_size=max_size, minicap_port=self.screen_port, minitouch_port=self.ctrl_port)
            elif driver_lib == DriverLib.SCRCPY:
                self.driver = ScrcpyMgr(max_size=max_size, port=self.screen_port)
                self.driver.start()
        elif mode == RunMode.MULTI:
            pass
        elif mode == RunMode.CLOUDTEST:
            pass

    def stop_driver(self):
        if self.mode == RunMode.SINGLE and self.driver:
            self.driver.disconnect()
            self.driver = None
        elif self.mode == RunMode.IDE:
            self.driver.disconnect()

    def touch_down(self, pos, id=0, pressure=50):
        self.driver.touch_down(pos=pos, id=id, pressure=pressure)

    def touch_move(self, pos, id=0, pressure=50):
        self.driver.touch_move(pos=pos, id=id, pressure=pressure)

    def touch_up(self, pos=None, id=0, pressure=50):
        self.driver.touch_up(pos=pos, id=id, pressure=pressure)

    def touch_reset(self):
        self.driver.touch_reset()

    def window_size(self):
        return [self.driver.width, self.driver.height]

    def rel2abs(self, pos):
        if isinstance(pos[0], float) and isinstance(pos[1], float):
            w, h = self.window_size()
            return [int(pos[0] * w), int(pos[1] * h)]
        return pos

    def abs2rel(self, pos):
        if isinstance(pos[0], int) and isinstance(pos[1], int):
            w, h = self.window_size()
            return [pos[0] / w, pos[1] / h]
        return pos

    def click_pos(self, pos, duration=0.05):
        pos = self.rel2abs(pos)
        self.touch_down(pos)
        time.sleep(duration)
        self.touch_up(pos)

    def slide_pos(self, pos_from, pos_to=None, pos_shift=None, duration=0):
        step = 15
        pos_from = self.rel2abs(pos_from)
        if pos_to:
            pos_to = self.rel2abs(pos_to)
            vector = [pos_to[0] - pos_from[0], pos_to[1] - pos_from[1]]
        elif pos_shift:
            vector = self.rel2abs(pos_shift)
            pos_to = [pos_from[0] + vector[0], pos_from[1] + vector[1]]

        step_x = int(vector[0] / step)
        step_y = int(vector[1] / step)

        for i in range(step):
            pos = (pos_from[0] + (i + 1) * step_x, pos_from[1] + (i + 1) * step_y)
            self.self.touch_move(pos)
            time.sleep(0.03)

        self._track(pos_to)
        self.touch_up(pos_to)

    def get_img(self):
        return self.driver.get_img()
