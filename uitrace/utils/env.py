import os
import sys
import time
import platform
from uitrace.utils.param import OSType
from configparser import ConfigParser


class ProjEnv:
    def __init__(self):
        self.lib_dir = None # 库的根目录
        self.workspace = "" # 存储根目录
        self.output_dir = "" # 输出目录
        self.log_dir = "" # 日志目录
        self.report_dir = "" # 报告目录
        self.screenshot_dir = ""  # 截图目录
        self.script_path = "" # 用户脚本路径

        pf = platform.system()
        if pf == "Windows":
            self.platform = OSType.WINDOWS
        elif pf == "Linux":
            self.platform = OSType.LINUX
        elif pf == "Darwin":
            self.platform = OSType.MAC
        else:
            self.platform = OSType.OTHER
        # self.config_dict = {}

        # self.init_env()

    def init_env(self):
        self.lib_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

        if self.workspace is None:
            return
        if not self.workspace:
            self.workspace = sys.path[0]
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if self.output_dir is None:
            return
        if not self.output_dir:
            time_label = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            pid_label = str(os.getpid())
            self.output_dir = os.path.join(self.workspace, "log", time_label + "_" + pid_label)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if self.log_dir is not None:
            if not self.log_dir:
                self.log_dir = self.output_dir
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)

        if self.report_dir is not None:
            if not self.report_dir:
                self.report_dir = self.output_dir
            if not os.path.exists(self.report_dir):
                os.makedirs(self.report_dir)

        if self.screenshot_dir is not None:
            if not self.screenshot_dir:
                self.screenshot_dir = os.path.join(self.report_dir, "screenshot")
            if not os.path.exists(self.screenshot_dir):
                os.makedirs(self.screenshot_dir)

        # cfg = self.get_config("base")
        #
        # if cfg["core"]["workspace"]:
        #     self.workspace = cfg["core"]["workspace"]
        # else:
        #     self.workspace = sys.path[0]
        # if not os.path.exists(self.workspace):
        #     os.makedirs(self.workspace)
        #
        # time_label = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        # pid_label = str(os.getpid())
        # self.output_dir = os.path.join(self.workspace, "output", time_label + "_" + pid_label)
        # if not os.path.exists(self.output_dir):
        #     os.makedirs(self.output_dir)
        #
        # if cfg["core"]["log_dir"]:
        #     self.log_dir = cfg["core"]["log_dir"]
        # else:
        #     self.log_dir = self.output_dir
        # if not os.path.exists(self.log_dir):
        #     os.makedirs(self.log_dir)
        #
        # if cfg["core"]["report_dir"]:
        #     self.report_dir = cfg["core"]["report_dir"]
        # else:
        #     self.report_dir = self.output_dir
        # if not os.path.exists(self.report_dir):
        #     os.makedirs(self.report_dir)
        #
        # self.screenshot_dir = os.path.join(self.report_dir, "screenshot")
        # if not os.path.exists(self.screenshot_dir):
        #     os.makedirs(self.screenshot_dir)


    def get_config(self, table="base"):
        """获取配置"""
        # 2021/03/25 zerodyli 去除库内读取配置文件功能，该函数废弃
        if table in self.config_dict:
            return self.config_dict[table]
        cfg = ConfigParser()
        file_path = os.path.abspath(os.path.join(self.lib_dir, "config", table + '.ini'))
        cfg.read(file_path, encoding="utf-8")
        self.config_dict[table] = cfg
        return cfg


proj_env = ProjEnv()

class DeviceEnv(object):
    os_type = None
    udid = None
    real_size = None
    run_mode = None
    driver = None  # 基础驱动driver
    ui_driver = None # 原生控件驱动driver
    # ga_driver = None
    dev_mgr = None