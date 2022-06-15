# import sys
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from uitrace.api import *
import time
from init import *


def test_camera():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE, driver_lib=DriverLib.SCRCPY)

    time.sleep(2)

    start_app(Android_camera,
              splash_activity="com.tencent.mobileqq.activity.SpalashActivity",
              clear_app=True, clear_account=False)

    click(Android_shoot,
          by=DriverType.UI, timeout=20)

    click(loc="人像", by=DriverType.OCR, timeout=30, duration=0.05, times=1)
    click(Android_shoot,
          by=DriverType.UI, timeout=20)

    click(Android_switch_camera,
          by=DriverType.UI, timeout=20)
    click(Android_shoot,
          by=DriverType.UI, timeout=20)

    stop_driver()


if __name__ == '__main__':
    test_camera()

