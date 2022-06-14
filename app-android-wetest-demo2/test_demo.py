import sys
import os
sys.path.append(os.path.join(__file__, '..'))

from uitrace.api import *
import cv2 as cv


def start_calculate():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__),
                mode=RunMode.SINGLE, dirver_lib=DriverLib.SCRCPY)
    time.sleep(2)
    start_app('package name')  # app name, 如 'com.tencent.mobileqq'
    time.sleep(2)
    img = get_img()
    cv.imshow('test_app', img)
    time.sleep(10)

    stop_driver()


if __name__ == '__main__':
    start_calculate()
