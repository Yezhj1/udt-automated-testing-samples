# import sys
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from uitrace.api import *
import cv2 as cv


def test_click():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__),
                mode=RunMode.SINGLE, dirver_lib=DriverLib.SCRCPY)

    click([200, 200])
    tic = time.time()
    toc = tic
    while toc - tic < 20:
        img = get_img()
        if img is not None:
            cv.imshow("test_android", img)
            cv.waitKey(1)
            toc = time.time()

    stop_driver()


if __name__ == '__main__':
    test_click()
