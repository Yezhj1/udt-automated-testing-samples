from init import args
from device import Xiaomi, HUAWEI
from uitrace.api import *


def set_ime(device_type='HUAWEI'):
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE,
                driver_lib=DriverLib.SCRCPY)
    start_app('com.android.settings')
    if device_type == 'HUAWEI':
        if not find('系统', by=DriverType.OCR):
            slide(loc_from=[0.289, 0.836], loc_to=[0.359, 0.633], by=DriverType.POS, timeout=30)
        click(loc="系统", by=DriverType.OCR, timeout=30, duration=0.05, times=1)
        click(loc='语言与输入法', by=DriverType.OCR, timeout=30, duration=0.05, times=1)
        click(loc='输入法名', by=DriverType.OCR, timeout=30, duration=0.05, times=1)

    elif device_type == 'Xiaomi':
        if not find('更多设置', by=DriverType.OCR):
            slide(loc_from=[0.289, 0.836], loc_to=[0.359, 0.633], by=DriverType.POS, timeout=30)
        click(loc="更多设置", by=DriverType.OCR, timeout=30, duration=0.05, times=1)
        click(loc='语言与输入法', by=DriverType.OCR, timeout=30, duration=0.05, times=1)
        click(loc='输入法名', by=DriverType.OCR, timeout=30, duration=0.05, times=1)

    press(DeviceButton.HOME)

    stop_driver()


if __name__ == '__main__':
    info = args()
    # phone_address = info.phone_address
    # input_address = info.app_address
    app_name = info.app_name
    device_type = info.device_type

    set_ime(device_type)
    