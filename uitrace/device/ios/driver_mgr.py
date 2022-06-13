import time
from uitrace.device.ios.wda.wda_mgr import WDAMgr, WDACtrl
from uitrace.device.driver_svr import DriverClient
from uitrace.utils.log_handler import get_logger
from uitrace.utils.param import RunMode, DeviceButton
from uitrace.utils.toolkit import get_free_ports, retry

logger = get_logger()


# def set_workspace(dir):
#     # set_env("project_dir", os.path.abspath(dir))
#     proj_env.workspace = os.path.abspath(dir)


class IOSDriver():
    def __init__(self):
        self.driver = None
        self.ctrl = None
        self.screen = None
        self.sess = None
        self.mode = None
        self.screen_port = None
        self.ctrl_port = None
        self.ctrl_driver = None
        self.bundle_id = None

    def start_driver(self, bundle_id=None, ip="127.0.0.1", screen_port=8200, ctrl_port=8100, max_size=800,
                     mode=RunMode.SINGLE):
        ports = get_free_ports(2)
        self.screen_port = screen_port if screen_port else ports[0]
        self.ctrl_port = ctrl_port if ctrl_port else ports[1]

        self.mode = mode
        if mode == RunMode.IDE:
            self.screen = DriverClient(ip=ip, port=self.screen_port)
            self.screen.connect()
            self.ctrl_driver = WDACtrl()
            self.ctrl_driver.start_ctrl(ip=ip, port=self.ctrl_port)
            self.ctrl = self.ctrl_driver.cli
            # self.sess = self.ctrl_driver.sess
        elif mode == RunMode.SINGLE:
            self.bundle_id = bundle_id
            self.driver = WDAMgr()
            self.driver.start_wda(bundle_id=bundle_id, ip=ip, screen_port=self.screen_port, ctrl_port=self.ctrl_port,
                                  max_size=max_size)
            self.driver.connect()
            self.ctrl = self.driver.ctrl.cli
            self.screen = self.driver.screen
            # self.sess = self.driver.ctrl.sess
        elif mode == RunMode.CLOUDTEST:
            self.ctrl_driver = WDACtrl()
            self.ctrl_driver.start_ctrl(ip=ip, port=self.ctrl_port, max_size=max_size)
            self.ctrl = self.ctrl_driver.cli
            # self.sess = self.ctrl_driver.sess
            self.screen = self.ctrl_driver

        self.init_sess()
        self.sess.appium_settings({"mjpegScalingFactor": 60})

    def stop_driver(self):
        if self.mode == RunMode.SINGLE and self.driver:
            self.driver.disconnect()
            self.driver.stop_wda()
            self.driver = None
        elif self.mode == RunMode.IDE:
            self.screen.disconnect()
            self.ctrl_driver.stop_ctrl()
        elif self.mode == RunMode.CLOUDTEST:
            self.ctrl_driver.stop_ctrl()

    def init_sess(self):
        self.sess = self.ctrl.session()

    def window_size(self):
        self.sess.appium_settings({"snapshotMaxDepth": 0})
        ws = self.ctrl.window_size()
        self.sess.appium_settings({"snapshotMaxDepth": 50})
        return ws

    def rel2abs(self, pos):
        self.sess.appium_settings({"snapshotMaxDepth": 0})
        pos = self.ctrl._percent2pos(pos[0], pos[1])
        self.sess.appium_settings({"snapshotMaxDepth": 50})
        return pos

    def abs2rel(self, pos):
        if isinstance(pos[0], int) and isinstance(pos[1], int):
            w, h = self.window_size()
            return [pos[0] / w, pos[1] / h]
        return pos

    def get_img(self):
        return self.screen.get_img()

    def get_uitree(self):
        return self.ctrl.source(format='json')

    def start_app(self, bundle_id):
        result = self.ctrl.app_launch(bundle_id)
        if "status" in result.keys() and result["status"] == 0:
            return result["sessionId"]
        logger.warning("app launch failed: %s" % str(result))
        return False

    def stop_app(self, bundle_id):
        return self.ctrl.app_stop(bundle_id)

    def restart_app(self, bundle_id):
        self.stop_app(bundle_id)
        time.sleep(1)
        self.start_app(bundle_id)

    def press_home(self):
        self.ctrl.home()

    def press(self, btn):
        self.sess.appium_settings({"snapshotMaxDepth": 0})
        if btn == DeviceButton.HOME:
            self.ctrl.press("home")
        elif btn == DeviceButton.VOLUME_UP:
            self.ctrl.press("volumeUp")
        elif btn == DeviceButton.VOLUME_DOWN:
            self.ctrl.press("volumeDown")
        elif btn == DeviceButton.LOCK:
            self.lock()
        elif btn == DeviceButton.UNLOCK:
            self.unlock()
        self.sess.appium_settings({"snapshotMaxDepth": 50})

    def lock(self):
        self.ctrl.lock()

    def unlock(self):
        self.ctrl.unlock()

    def current_app(self):
        # {'processArguments': {'env': {}, 'args': []}, 'name': '', 'pid': 60, 'bundleId': 'com.apple.springboard'}
        try:
            info = self.ctrl.app_current()
            if "bundleId" in info.keys():
                return info["bundleId"]
            logger.warning("get app current failed: %s" % str(info))
        except:
            logger.exception("get app current failed")
        return ""

    def get_element(self, xpath, timeout=30):
        # elem = self.sess(**kwargs).get(timeout=timeout, raise_error=False)
        return self.ctrl.xpath(xpath).get(timeout=timeout, raise_error=False)

    def get_elements(self, xpath):
        return self.ctrl.xpath(xpath).find_elements()

    def get_pos(self, xpath, timeout=30, **kwargs):
        elem = self.get_element(xpath=xpath, timeout=timeout)
        if elem:
            return elem.bounds.center
        return None

    @retry(logger=logger)
    def click_pos(self, pos, duration=None):
        pos = self.rel2abs(pos)
        self.sess.appium_settings({"snapshotMaxDepth": 0})
        self.ctrl.click(pos[0], pos[1], duration)
        self.sess.appium_settings({"snapshotMaxDepth": 50})

    def slide_pos(self, pos_from, pos_to=None, pos_shift=None, duration=0):
        pos_from = self.rel2abs(pos_from)
        if pos_to:
            pos_to = self.rel2abs(pos_to)
        elif pos_shift:
            vector = self.rel2abs(pos_shift)
            pos_to = [pos_from[0] + vector[0], pos_from[1] + vector[1]]
        du = duration if duration else 0
        self.sess.appium_settings({"snapshotMaxDepth": 0})
        self.ctrl.swipe(pos_from[0], pos_from[1], pos_to[0], pos_to[1], du)
        self.sess.appium_settings({"snapshotMaxDepth": 50})

    def input_text(self, text, xpath=None, timeout=30, depth=10):
        self.sess.appium_settings({"snapshotMaxDepth": depth})
        self.ctrl.xpath(xpath).get(timeout=timeout, raise_error=False).set_text(text)
        self.sess.appium_settings({"snapshotMaxDepth": 50})
