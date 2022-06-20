# import os
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from uitrace.api import *


def test_click():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE, driver_lib=DriverLib.SCRCPY)
    start_app("com.android.browser")
    time.sleep(5)
    click(loc="视频", by=DriverType.OCR, timeout=30, duration=0.05, times=1)
    stop_driver()


if __name__ == '__main__':
    test_click()

