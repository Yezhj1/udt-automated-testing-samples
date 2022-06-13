import threading
import time
import cv2

from uitrace.device.android.stf.Minicap import Minicap
from uitrace.device.android.stf.Minitouch import Minitouch
from uitrace.device.android.stf.Rotation import Rotation

from uitrace.utils.env import DeviceEnv
from uitrace.device.android.dev_mgr import AndroidMgr


class STFMgr:
    def __init__(self):
        self.max_size = None
        self.port = None
        self.minicap = None
        self.minitouch = None
        self.rotation_watcher = None
        self.rotation = None
        self.info = None
        self.run_state = True

        # DeviceEnv.dev_mgr = AndroidMgr()

    def start(self, max_size=800, minicap_port=1111, minitouch_port=1112):
        self.max_size = max_size
        self.minicap_port = minicap_port
        self.minicap = Minicap()
        self.minicap.start(port=self.minicap_port, max_size=self.max_size)
        self.info = self.minicap.get_info()

        self.minitouch_port = minitouch_port
        self.minitouch = Minitouch()
        self.minitouch.start(port=self.minitouch_port)
        self.minitouch.set_info(self.info)

        self.rotation_watcher = Rotation()
        self.rotation_watcher.start()

        self.rotation_thread = threading.Thread(target=self.rotation_check)
        self.rotation_thread.start()

    def rotation_check(self):
        rotation_tmp = self.rotation_watcher.get_rotation()
        while self.run_state:
            self.rotation = self.rotation_watcher.get_rotation()
            if rotation_tmp != self.rotation:
                rotation_tmp = self.rotation
                self.minicap.start(port=self.minicap_port, max_size=self.max_size)
                self.info = self.minicap.get_info()
                self.minitouch.set_info(self.info)
            time.sleep(0.1)

    def stop(self):
        self.run_state = False

        if self.minicap is not None:
            self.minicap.stop()
            self.minicap = None

        if self.minitouch is not None:
            self.minitouch.stop()
            self.minitouch = None

        if self.rotation_watcher is not None:
            self.rotation_watcher.stop()
            self.rotation_watcher = None

    def get_img(self):
        return self.minicap.get_img()

    def touch_down(self, pos, id=0, pressure=50):
        self.minitouch.touch_down(pos=pos, id=id, pressure=pressure)

    def touch_move(self, pos, id=0, pressure=50):
        self.minitouch.touch_move(pos=pos, id=id, pressure=pressure)

    def touch_up(self, id=0, **kwargs):
        self.minitouch.touch_up(id=id)

    def touch_reset(self):
        pass

    def device_info(self):
        return self.info

    def get_rotation(self):
        return self.rotation

# stf = STFMgr()
# stf.start()
# stf.touch_down([100, 100])
# time.sleep(0.5)
# # stf.touch_up()
#
# while True:
#     img = stf.get_img()
#     cv2.imshow("test", img)
#     cv2.waitKey(50)