import os
import time
import json
import subprocess
import platform
import socket
import argparse
import numpy as np
from contextlib import closing
from functools import wraps
from uitrace.cvlib.cv_utils import imread, imwrite
from uitrace.utils.env import proj_env, DeviceEnv
from uitrace.utils.log_handler import get_logger
from uitrace.utils.param import RunMode, OSType, DriverLib

__cur_dir = os.path.dirname(os.path.abspath(__file__))
__root_dir = os.path.abspath(os.path.join(__cur_dir, "..", ".."))


def cmd_raw(cmd_line):
    # if isinstance(cmd_line, str):
    #     cmd_line = cmd_line.split()
    if isinstance(cmd_line, list):
        cmd_line = " ".join(cmd_line)
    return subprocess.Popen(cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def cmd_analy(info):
    info_list = info[0].strip().decode("utf-8").splitlines()
    if info_list and info_list[-1] == '\x1b[0m':
        info_list = info_list[:-1]
    return info_list


def get_free_port():
    """获取空闲端口"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def get_free_ports(num=1):
    ports = []
    while len(ports) < num:
        port = get_free_port()
        if not port in ports:
            ports.append(port)
    return ports


def set_env(key, value):
    """设置环境变量"""
    real_key = key.upper()
    os.putenv(real_key, value)


def get_env(key, default=None):
    """获取环境变量"""
    real_key = key.upper()
    return os.getenv(real_key, default=default)


def img_parse(img):
    """读取图像"""
    if isinstance(img, str):
        if os.path.exists(img):
            return imread(img)
        if proj_env.workspace:
            img_path = os.path.join(proj_env.workspace, "data", "img", img)
            if os.path.exists(img_path):
                return imread(img_path)
            img_path = os.path.join(proj_env.workspace, "data", "img", img + ".jpg")
            if os.path.exists(img_path):
                return imread(img_path)
    elif isinstance(img, np.ndarray):
        return img
    return None


def retry(tries=4, timeval=5, health_reset=None, logger=None, **kwargs):
    def retry_deco(func):
        def wrapper(*args, **kwargs):
            for i in range(tries):
                try:
                    f = func(*args, **kwargs)
                    return f
                except:
                    if logger:
                        logger.exception("retry %s" % i)
                    if health_reset:
                        health_reset()
                    time.sleep(timeval)
            return None
        return wrapper
    return retry_deco


# def record(func, args, kwargs):
#     img_path = ""
#     if DeviceEnv.driver is not None:
#         path = DeviceEnv.driver.screenshot(label=func.__name__)
#         if path:
#             img_path = path
#
#     info = {
#         "time": time.time(),
#         "func": func.__name__,
#         "args": str(args),
#         "kwargs": str(kwargs),
#         "img": img_path
#     }
#     report_logger = get_logger(log_name="report")
#     report_logger.info(json.dumps(info))
#
# def report_deco(func):
#     """report装饰器"""
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if proj_env.report_dir:
#             record(func, args, kwargs)
#         return func(*args, **kwargs)
#     return wrapper

def parse_args():
    # do not change default
    parser = argparse.ArgumentParser(description='ide runner')
    parser.add_argument('--os_type', default=OSType.IOS, type=int, help='operation system')
    parser.add_argument('--udid', default=None, help='unique device identifier')
    parser.add_argument('--bundle_id', default="com.watest.WebDriverAgentRunner.xctrunner", help='bundle id')
    parser.add_argument('--ip', default='127.0.0.1', help='ip')
    parser.add_argument('--max_size', default=800, type=int, help='screen max size')
    parser.add_argument('--driver_lib', default=DriverLib.SCRCPY, type=int, help='driver lib type')
    parser.add_argument('--mode', default=None, type=int, help='script run mode')
    parser.add_argument('--svr_port', default=8400, type=int, help='middleware svr port')
    parser.add_argument('--ga_port', default=None, type=int, help='ga driver port')
    parser.add_argument('--screen_port', default=None, type=int, help='wda screen stream or android scrcpy port')
    parser.add_argument('--ctrl_port', default=None, type=int, help='wda ctrl svr port')
    parser.add_argument('--ifs', default=0.05, type=float, help='middleware svr screen stream frame interval')
    parser.add_argument('--script', default="", type=str, help='user script py')
    parser.add_argument('--cmd', default="", type=str, help='ide cmd')
    args = parser.parse_known_args()
    return args[0]


def is_contain_chinese(check_str):
    """
    判断字符串中是否包含中文
    :param check_str: {str} 需要检测的字符串
    :return: {bool} 包含返回True， 不包含返回False
    """
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


def get_default_appdata():
    appName = "WeAutomatorIOS-dev"
    if os.path.exists(os.path.join(__root_dir, "WeTestUITracePython")) or \
            os.path.exists(os.path.join(__root_dir, "WeTestUITracePython.exe")):
        appName = "WeAutomatorIOS"
    if platform.system().upper().startswith("DARWIN"):
        workspace = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', appName)
    elif platform.system().upper().startswith("WINDOW"):
        workspace = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', appName)
    else:
        workspace = os.path.join(os.path.expanduser('~'), appName)
    os.makedirs(workspace, exist_ok=True)
    return workspace
