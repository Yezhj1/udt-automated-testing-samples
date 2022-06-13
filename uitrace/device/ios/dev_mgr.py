import sys
import time
import tidevice
from uitrace.utils.toolkit import cmd_analy, cmd_raw
from uitrace.utils.env import DeviceEnv
from multiprocessing import Process
from threading import Thread
from tidevice._proto import MODELS
from tidevice._relay import relay
from tidevice._wdaproxy import WDAService
from uitrace.utils.log_handler import get_logger

logger = get_logger()


# def cmd_exec(cmd):
#     info = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
#     info_list = info[0].decode("utf-8").splitlines()
#     if info_list[-1] == '\x1b[0m':
#         info_list = info_list[:-1]
#     return info_list

class IOSMgr(object):
    def __init__(self, udid=None):
        if udid:
            self.udid = udid
        else:
            self.udid = DeviceEnv.udid

        self.dev = None
        self.usb = None
        if self.udid:
            self.usb = tidevice.Usbmux()
            self.dev = tidevice.Device(udid=self.udid, usbmux=self.usb)

    def cmd_tid(self, cmd_line, id_mark=True, wait=False):
        if isinstance(cmd_line, str):
            tid = sys.executable + " -m tidevice"
            if id_mark and self.udid:
                tid += " --udid " + self.udid
            tid += " " + cmd_line
        elif isinstance(cmd_line, list):
            tid = [sys.executable, "-m", "tidevice"]
            if id_mark and self.udid:
                tid += ["--udid", self.udid]
            tid += cmd_line
        sp = cmd_raw(tid)
        if wait:
            return sp.communicate()
        return sp

    def device_list(self):
        """获取连接设备udid"""
        # info = cmd_raw(['tidevice', 'list']).communicate()
        # info = cmd_analy(info)
        # id_list = []
        # for i in info:
        #     if i:
        #         id_list.append(i.split(' ')[0])
        # return id_list

        # [{'ConnectionType': 'USB', 'DeviceID': 1, 'LocationID': 0, 'ProductID': 4776, 'SerialNumber': '00008101-00080C213A04001E'}]
        return self.usb.device_list()

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
        if self.dev is not None:
            info = self.dev.device_info()
            market_name = MODELS.get(info["ProductType"])
            info_dict["MarketName"] = market_name if market_name else info["ProductType"]
            info_dict["ProductVersion"] = info["ProductVersion"]
            info_dict["DeviceName"] = info["DeviceName"]
            info_dict["UniqueDeviceID"] = info["UniqueDeviceID"]
        return info_dict

    # def app_list(self):
    #     """获取设备中安装的App"""
    #     args = ['applist']
    #     info = self.cmd_tid(args).communicate()
    #     info = cmd_analy(info)
    #     app_list = []
    #     for i in info:
    #         if i:
    #             app_list.append(i)
    #     return app_list

    def install_app(self, app_path):
        """安装App"""
        # logger.info("app install: %s" % ipa_path)
        # args = ['install', ipa_path]
        # info = self.cmd_tid(args).communicate()
        # info = cmd_analy(info)
        # for i in info:
        #     if i and "Complete" in i:
        #         logger.info("app install success")
        #         return True
        #
        # logger.warning("app install fail: " + str(info))
        # return False
        if self.dev:
            return self.dev.app_install(app_path)
        return False

    def uninstall_app(self, bundle_id):
        """卸载App"""
        # logger.info("app uninstall: %s" % bundle_id)
        # args = ['uninstall', bundle_id]
        # info = self.cmd_tid(args).communicate()
        # info = cmd_analy(info)
        # for i in info:
        #     if i and "Complete" in i:
        #         logger.info("app uninstall success")
        #         return True
        #
        # logger.warning("app uninstall fail: " + str(info))
        # return False
        if self.dev:
            return self.dev.app_uninstall(bundle_id)
        return False

    def start_app(self, bundle_id, kill_running=False):
        """启动App"""
        # args = ['launch', bundle_id]
        # info = self.cmd_tid(args).communicate()
        # info = cmd_analy(info)
        # for i in info:
        #     if "PID" in i:
        #         return True
        # logger.warning("app launch failed: " + str(info))
        # return False
        if self.dev:
            return self.dev.app_start(bundle_id=bundle_id, kill_running=kill_running)
        return False

    def restart_app(self, bundle_id):
        """重启App"""
        if self.dev:
            return self.start_app(bundle_id, kill_running=True)
        return False

    def stop_app(self, bundle_id):
        """关闭App"""
        # args = ['kill', bundle_id]
        # info = self.cmd_tid(args).communicate()
        # info = cmd_analy(info)
        # for i in info:
        #     if "Kill pid" in i:
        #         return True
        # logger.warning("app kill failed: " + str(info))
        # return False
        if self.dev:
            return self.dev.app_stop(bundle_id)
        return False

    def current_app(self):
        pass

    def reboot(self):
        """重启设备"""
        pass

    def screenshot(self):
        """截图"""
        pass

    def forward_worker(self, local_port, remote_port):
        dev = tidevice.Device(self.udid)
        relay(dev, local_port, remote_port)

    def forward_port(self, local_port, remote_port):
        # p = Process(target=self.forward_worker, args=(local_port, remote_port,))
        # p.start()
        # return p
        args = ["relay", str(local_port), str(remote_port)]
        return self.cmd_tid(args)

    def iproxy_port(self, local_port, remote_port):
        args = ["iproxy", str(local_port), str(remote_port)]
        return cmd_raw(args)

    def wda_worker(self, bundle_id, port):
        usb = tidevice.Usbmux()
        dev = tidevice.Device(udid=self.udid, usbmux=usb)
        serv = WDAService(dev, bundle_id)

        p = None
        if port != 8100:
            p = self.forward_port(port, 8100)
        try:
            serv.start()
            while serv._service.running:
                time.sleep(.1)
        finally:
            p and p.terminate()
            serv.stop()

    def init_wda(self, bundle_id, port=8100):
        # p = Process(target=self.wda_worker, args=(bundle_id, port,))
        # p.start()
        # return p

        args = ["wdaproxy", "-B", bundle_id, "--port", str(port)]
        return self.cmd_tid(args)

