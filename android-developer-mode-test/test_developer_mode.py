import os
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import time

from uitrace.api import *
import cv2 as cv



def test_click():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE, driver_lib=DriverLib.SCRCPY)
    time.sleep(10)
    start_app('com.android.settings')
    device_type = os.system('adb shell getprop ro.product.brand')
    text1, text2 = "", ""
    if device_type == 'HONER':
        text1 = '关于本级'
        text2 = '版本号'
    elif device_type == 'HUAWEI':
        text1 = '关于手机'
        text2 = '版本号'
    elif device_type = 'OPPo':
        text1 = '关于手机'
        text2 = 'Android版本'
    if not find(text1, by=DriverType.OCR):
        slide(loc_from=[0.289, 0.836], loc_to=[0.359, 0.633], by=DriverType.POS, timeout=30)
        
        

    stop_driver()

if __name__ == '__main__':
    test_click()
    # f = os.popen("adb devices")
    # devices = f.read().strip().split('\n')
    # f.close()
    # print(devices)