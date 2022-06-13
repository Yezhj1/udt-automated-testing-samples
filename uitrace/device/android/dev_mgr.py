import os
from uitrace.utils.env import proj_env, DeviceEnv
from uitrace.utils.param import OSType
from uitrace.utils.toolkit import cmd_raw, cmd_analy
from uitrace.utils.log_handler import get_logger

logger = get_logger()


class AndroidMgr(object):
    def __init__(self, udid=None):
        self.adb = self.get_adb()

        if udid:
            self.udid = udid
        else:
            self.udid = DeviceEnv.udid

    def get_adb(self):
        if proj_env.platform == OSType.WINDOWS:
            adb_file = os.path.join(os.path.dirname(__file__), "static", "adb", "win", "adb.exe")
        elif proj_env.platform == OSType.MAC:
            adb_file = os.path.join(os.path.dirname(__file__), "static", "adb", "mac", "adb")
        elif proj_env.platform == OSType.LINUX:
            adb_file = os.path.join(os.path.dirname(__file__), "static", "adb", "linux", "adb")
        if os.path.exists(adb_file):
            return adb_file
        return "adb"

    def cmd_adb(self, cmd_line, id_mark=True, timeout=-1):
        if isinstance(cmd_line, str):
            adb = self.adb
            if id_mark and self.udid:
                adb += " -s " + self.udid
            adb += " " + cmd_line
        elif isinstance(cmd_line, list):
            adb = [self.adb]
            if id_mark and self.udid:
                adb += ["-s", self.udid]
            adb += cmd_line
        sp = cmd_raw(adb)
        if timeout > 0:
            return sp.wait(timeout=timeout)
        return sp

    def device_list(self):
        """获取连接设备udid"""
        cmd = "devices"
        info = self.cmd_adb(cmd, id_mark=False).communicate()
        info = cmd_analy(info)
        devices = []
        for i in info:
            if i and "\t" in i:
                item = i.split("\t")
                devices.append([item[0], item[1].strip()])
        return devices

    def app_list(self):
        """获取设备中安装的App"""
        cmd = "shell pm list packages"
        info = self.cmd_adb(cmd).communicate()
        info = cmd_analy(info)
        apps = []
        for i in info:
            apps.append(i[8:]) # delete 'package:'
        return apps

    def install_app(self, app_path):
        """安装App"""
        cmd = "install " + app_path
        info = self.cmd_adb(cmd).communicate()
        for i in info:
            if "Success" in str(i):
                return True
        return False

    def uninstall_app(self, bundle_id):
        """卸载App"""
        cmd = "uninstall " + bundle_id
        info = self.cmd_adb(cmd).communicate()
        for i in info:
            if "Success" in str(i):
                return True
        return False

    def start_app(self, pkg):
        """启动App"""
        cmd = "shell monkey -p " + pkg + " -c android.intent.category.LAUNCHER 1"
        self.cmd_adb(cmd, timeout=30)
        app = self.current_app()
        if app and app == pkg:
            return True
        return False

    def stop_app(self, pkg):
        """关闭App"""
        cmd = "shell am force-stop " + pkg
        self.cmd_adb(cmd).communicate()

    def reboot(self):
        """重启设备"""
        pass

    def screenshot(self):
        """截图"""
        pass

    def current_app(self):
        """返回当前app"""
        pass

    def app_reset(self, pkg):
        '''清空应用数据'''
        cmd = "shell pm clear " + pkg
        info = self.cmd_adb(cmd).communicate()
        for i in info:
            if "Success" in str(i):
                return True
        return False

    def press(self, btn, timeout=10):
        cmd = "shell input keyevent " + str(btn)
        self.cmd_adb(cmd, timeout=timeout)

    def input_text(self, text, timeout=10, ime=True):
        if ime:
            cmd = "shell am broadcast -a ADB_INPUT_TEXT --es msg '%s'" % text
        else:
            cmd = "shell input text '%s'" % text
        self.cmd_adb(cmd, timeout=timeout)

    def device_info(self):
        """获取设备信息"""
        # args = ['info']
        # info = self.cmd_tid(args).communicate()
        # info = cmd_analy(info)
        # devices = {}
        # for i in info:
        #     if i:
        #         item = i.split(":")
        #         devices[item[0]] = item[1].strip()
        # return devices
        info_dict = {}
        return info_dict

    def get_sdk_ver(self):
        """获取系统版本"""
        try:
            cmd = "shell getprop ro.build.version.sdk"
            info = self.cmd_adb(cmd).communicate()
            sdk_ver = int(cmd_analy(info)[0])
            return sdk_ver
        except:
            logger.exception("get android sdk error")
        return -1
