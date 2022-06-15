import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from uitrace.api import *
from Xpath import *
import argparse


def arg():
    parse = argparse.ArgumentParser()
    parse.add_argument('--qq', typr=str, default='')
    parse.add_argument('-password', type=str, default='')
    return parse.parse_args()


def test_qq(arg):
    init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), mode=RunMode.SINGLE,
                driver_lib=DriverLib.SCRCPY)
    start_app('com.tencent.mobileqq',
              splash_activity="com.tencent.mobileqq.activity.SpalashActivity",
              clear_app=True, clear_account=False)
    click(login, by=DriverType.UI, timeout=20)
    click(account, by=DriverType.UI, timeout=20)
    input_text(arg.qq) # input a qq number
    click(password, by=DriverType.UI, timeout=20)
    input_text(arg.password) # qq password
    click(confirm, by=DriverType.UI, timeout=20)

    stop_driver()


if __name__ == '__main__':
    info = arg()
    test_qq(info)
