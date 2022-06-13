import threading
import time
import os
from uitrace.utils.env import DeviceEnv
from uitrace.device.android.dev_mgr import AndroidMgr

cur_dir = os.path.dirname(os.path.abspath(__file__))
ROTATION_PATH = os.path.join(cur_dir, "stf", "rotationwatcher", "RotationWatcher.jar")


class Rotation:
    def __init__(self):
        self.rotation = 0
        self.rotation_thread = None
        self.run_state = True

        # DeviceEnv.dev_mgr = AndroidMgr()
        self.dev_mgr = DeviceEnv.dev_mgr

        info = self.dev_mgr.cmd_adb("shell ls /data/local/tmp/RotationWatcher.jar").communicate()
        for i in info:
            if "No such file" in str(i):
                self.setup()

    def setup(self):
        push_jar = "push " + ROTATION_PATH + " /data/local/tmp"
        self.dev_mgr.cmd_adb(push_jar).wait()
        self.dev_mgr.cmd_adb("shell chmod 777 /data/local/tmp/RotationWatcher.jar").wait()

    def run_rotation(self):
        rotation_cmd = "shell app_process -Djava.class.path=/data/local/tmp/RotationWatcher.jar /data/local/tmp com.example.rotationwatcher.Main"
        rotation = self.dev_mgr.cmd_adb(rotation_cmd)

        while self.run_state:
            self.rotation = int(rotation.stdout.readline().strip())
            # print(self.rotation)

    def start(self):
        self.run_state = True
        self.rotation_thread = threading.Thread(target=self.run_rotation)
        self.rotation_thread.setDaemon(True)
        self.rotation_thread.start()

    def get_rotation(self):
        return self.rotation

    def stop(self):
        self.run_state = False

# r = Rotation()
# r.start()
# while True:
#     print(r.get_rotation())
#     time.sleep(0.5)
