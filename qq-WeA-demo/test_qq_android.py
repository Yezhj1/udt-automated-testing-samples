from uitrace.api import *
from Xpath import *


def test_qq():
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE,
                driver_lib=DriverLib.SCRCPY)
    start_app('com.tencent.mobileqq',
              splash_activity="com.tencent.mobileqq.activity.SpalashActivity",
              clear_app=True, clear_account=False)
    click(login, by=DriverType.UI, timeout=20)
    click(account, by=DriverType.UI, timeout=20)
    input_text('qq number') # input a qq number
    click(password, by=DriverType.UI, timeout=20)
    input_text('password') # qq password
    click(confirm, by=DriverType.UI, timeout=20)

    stop_driver()


if __name__ == '__main__':
    test_qq()
