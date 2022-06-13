import codecs
import os
import re
import json
import sys
import time
import shutil
import threading
import cv2 as cv
from functools import wraps
from uitrace.utils.param import OSType, DriverType, RunMode, DriverLib, DeviceButton
from uitrace.utils.env import proj_env, DeviceEnv
from uitrace.utils.toolkit import img_parse, parse_args, get_free_ports
from uitrace.cvlib.tpl_match import tpl_match
from uitrace.cvlib.ocr_match import ocr_driver
from uitrace.cvlib.cv_utils import imwrite, imread
from uitrace.device.android.dev_mgr import AndroidMgr
from uitrace.device.ios.dev_mgr import IOSMgr
from uitrace.device.ios.driver_mgr import IOSDriver
from uitrace.device.android.driver_mgr import AndroidDriver
from uitrace.device.ga.ga_mgr import GADriver, ga_driver
from uitrace.utils.log_handler import get_logger, file_handler, report_handler

logger = get_logger()
__root_dir = os.path.abspath(os.path.join(__file__, "..", ".."))

"""General API"""


def record_report(func, args=None, kwargs=None):
    """记录报告.

    Args:
        func (func or str): 操作函数名或操作名
        args: 操作相关函数
        kwargs: 操作相关函数

    """
    func_name = func.__name__ if hasattr(func, "__name__") else func
    img_path = ""
    if DeviceEnv.driver is not None:
        pos = None
        if isinstance(args, tuple) and len(args) > 0 and (isinstance(args[0], list) or isinstance(args[0], tuple)):
            pos = args[0]
        path = screenshot(label=func_name, pos=pos)
        if path:
            img_path = path
    info = {
        "time": time.time(),
        "func": func_name,
        "args": str(args),
        "kwargs": str(kwargs),
        "img": img_path
    }
    if proj_env.report_dir:
        report_file = os.path.join(proj_env.report_dir, "report_record")
        with open(report_file, "a", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False)
            f.write("\n")
    # report_logger = get_logger(log_name="report")
    # report_logger.info(json.dumps(info))


def set_script_path(script_path):
    proj_env.script_path = os.path.abspath(os.path.normcase(script_path))


def _get_script_line():
    lineno = None
    if proj_env.script_path:
        f = sys._getframe()
        f = f.f_back

        while hasattr(f, "f_code"):
            co = f.f_code
            if os.path.abspath(os.path.normcase(co.co_filename)) == proj_env.script_path:
                lineno = f.f_lineno
            f = f.f_back
    return lineno


def log_deco(report=True):
    """日志装饰器.

    Args:
        report (bool): 为True时自动截图记录在报告中，为False则只打印

    """

    def log_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if proj_env.script_path:
                lineno = _get_script_line()
                if lineno:
                    logger.log(91, "[line-%s]" % str(lineno))
            logger.info("%s args:%s kwargs:%s" % (func.__name__, args, kwargs))
            if report and proj_env.report_dir:
                record_report(func, args, kwargs)
            return func(*args, **kwargs)

        return wrapper

    return log_decorator


def highlight_line():
    """高亮装饰器.

    """

    def highlight_line_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if proj_env.script_path:
                lineno = _get_script_line()
                if lineno:
                    logger.log(91, "[line-%s]" % str(lineno))
            return func(*args, **kwargs)

        return wrapper

    return highlight_line_decorator


def generate_report(report_dir=None):
    """生成报告.

    生成报告，stop_driver会默认调用，如可能异常导致无法正常结束，可主动调用该函数

    Args:
        report_dir (str): 报告生成路径

    """
    if not report_dir:
        return False

    src_dir = os.path.join(os.path.dirname(__file__), "static", "report")
    shutil.copytree(src_dir, report_dir, dirs_exist_ok=True)

    js_dir = os.path.join(report_dir, "static")
    log_file = os.path.join(report_dir, "log")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            data = []
            for i in lines:
                item = re.findall(r"\[(.+?)\]", i)
                # if item[1].startswith("Level "):
                #     continue
                if item and len(item) >= 3:
                    item_dict = {
                        "time": item[0],
                        "level": item[1],
                        "path": item[2],
                        "msg": i.split(item[2] + "]")[1].strip()
                    }
                else:
                    item_dict = {
                        "time": "",
                        "level": "",
                        "path": "",
                        "msg": i.strip()
                    }
                data.append(item_dict)
            log_js_str = "const logger=%s" % json.dumps(data, ensure_ascii=False)
        log_js = os.path.join(js_dir, "log.js")
        with open(log_js, "w+", encoding="utf-8") as f:
            f.write(log_js_str)

    device_file = os.path.join(report_dir, "device_info")
    if os.path.exists(device_file):
        with open(device_file, "r", encoding="utf-8") as f:
            data = "const device_info=" + f.readline()
        device_js = os.path.join(js_dir, "device_info.js")
        with open(device_js, "w+", encoding="utf-8") as f:
            f.write(data)

    report_file = os.path.join(report_dir, "report_record")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            data = "const report_record=[%s]" % ",".join(lines)
        report_js = os.path.join(js_dir, "report_record.js")
        with open(report_js, "w+", encoding="utf-8") as f:
            f.write(data)


def cloud_test_report(report_dir, result=False, msg="", onlyJson=False, onlyLogs=False):
    if not report_dir:
        return
    workspace = report_dir
    if not onlyLogs:
        case_result = {}
        if not result:
            case_result["adaptresult"] = {
                "level": 1,
                "description": "OK" if result else msg,
                "errorstack": msg,
                "time": int(time.time())
            }
        if "CASE_NAME" in os.environ:
            case_result["caseresult"] = [{
                "casename": os.environ["CASE_NAME"],
                "errorno": 0 if result else -1,
                "errordesc": "OK" if result else msg,
                "time": int(time.time())
            }]
        if len(case_result):
            with codecs.open(os.path.join(workspace, "caseresult.json"), 'w+', encoding='utf8') as fd:
                fd.write(json.dumps(case_result, ensure_ascii=False))
    if "USER_DOCKER_DIR" in os.environ:
        # 私有化平台复制日志到指定目录
        _copy_log_dir(workspace, os.path.join(os.environ["USER_DOCKER_DIR"], "upload.dir"),
                      onlyJson=onlyJson, onlyLogs=onlyLogs)
    if "CASE_LOG_DIR" in os.environ:
        # 新版云测功能测试复制日志到指定目录
        _copy_log_dir(workspace, os.environ["CASE_LOG_DIR"],
                      onlyJson=onlyJson, onlyLogs=onlyLogs)
    elif "UPLOADDIR" in os.environ:
        # 新版云测兼容测试复制日志到指定目录
        relative_wsp = os.path.join(__root_dir, os.environ['UPLOADDIR'])
        if "PWD" in os.environ:
            relative_wsp = os.path.abspath(os.path.join(os.environ["PWD"], os.environ['UPLOADDIR']))
        _copy_log_dir(workspace, relative_wsp, onlyJson=onlyJson, onlyLogs=onlyLogs)


def _copy_log_dir(src, target, onlyJson=False, onlyLogs=False):
    if not os.path.exists(src):
        logger.info('src %s not exist' % str(src))
        return False
    if not os.path.exists(target):
        return False
    if not os.path.exists(os.path.dirname(target)):
        return False
    if not onlyJson:
        try:
            shutil.copytree(src, os.path.join(target, "report"))
        except Exception as e:
            if not os.path.exists(os.path.join(target, "report")):
                logger.info('failed to copytree %s' % str(e))
    if not onlyLogs and os.path.exists(os.path.join(src, "caseresult.json")):
        shutil.copyfile(os.path.join(src, "caseresult.json"), os.path.join(target, "caseresult.json"))
    return True


def check_env():
    pass


@log_deco(report=False)
def init_driver(os_type=OSType.IOS, udid=None, max_size=800, bundle_id="com.test.WebDriverAgentRunner.xctrunner",
                screen_port=None, ctrl_port=None, mode=RunMode.SINGLE, driver_lib=None, **kwargs):
    """初始化设备驱动及环境.

    Args:
        os_type (OSType): 设备系统，安卓为OSType.ANDROID，iOS为OSType.IOS
        udid (str): 设备ID
        max_size (int): 传输画面的最大边长
        bundle_id (str): 设备为iOS时，WDA的bundle id
        screen_port (int): 获取画面服务的端口，不指定则使用闲置端口
        ctrl_port (int): 操作服务的端口，不指定则使用闲置端口
        mode (RunMode): 运行模式，一般使用默认即可
        driver_lib (DriverLib): 底层驱动使用的框架
        **kwargs: 脚本执行产出路径的修改等

    """
    args = parse_args()
    # 工程环境初始化
    proj_env.workspace = kwargs["workspace"] if "workspace" in kwargs else os.path.dirname(__file__)
    proj_env.output = kwargs["output"] if "output" in kwargs else ""
    proj_env.log_dir = kwargs["log_dir"] if "log_dir" in kwargs else ""
    proj_env.report_dir = kwargs["report_dir"] if "report_dir" in kwargs else ""
    proj_env.screenshot_dir = kwargs["screenshot_dir"] if "screenshot_dir" in kwargs else ""
    proj_env.init_env()

    if proj_env.log_dir:
        fh = file_handler()
        logger.addHandler(fh)

    # if proj_env.report_dir:
    #     rh = report_handler("report")
    #     get_logger("report").addHandler(rh)

    # 设备信息初始化
    DeviceEnv.os_type = os_type
    DeviceEnv.udid = args.udid if args.udid else udid
    DeviceEnv.run_mode = args.mode if args.mode else mode

    max_s = args.max_size if args.max_size else max_size
    screen_p = screen_port if screen_port else args.screen_port
    ctrl_p = ctrl_port if ctrl_port else args.ctrl_port

    if DeviceEnv.os_type == OSType.ANDROID:
        driver_l = args.driver_lib if args.driver_lib else driver_lib

        DeviceEnv.dev_mgr = AndroidMgr(udid=DeviceEnv.udid)
        driver = AndroidDriver()
        driver.start_driver(screen_port=screen_p, ctrl_port=ctrl_p, max_size=max_s, mode=DeviceEnv.run_mode,
                            driver_lib=driver_l)
        DeviceEnv.driver = driver
    elif DeviceEnv.os_type == OSType.IOS:
        DeviceEnv.dev_mgr = IOSMgr(udid=DeviceEnv.udid)
        driver = IOSDriver()
        driver.start_driver(bundle_id=bundle_id, screen_port=screen_p, ctrl_port=ctrl_p, max_size=max_s,
                            mode=DeviceEnv.run_mode, ip=args.ip)
        DeviceEnv.driver = driver
        DeviceEnv.ui_driver = driver.ctrl

    if proj_env.report_dir:
        info = DeviceEnv.dev_mgr.device_info()
        with open(os.path.join(proj_env.report_dir, "device_info"), 'w', encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False)

        params = locals()
        if "kwargs" in params.keys():
            del params["kwargs"]
        record_report(init_driver, params, kwargs)
        logger.log(90, "report dir: %s" % proj_env.report_dir)
    if DeviceEnv.run_mode == RunMode.CLOUDTEST:
        cloud_test_report(proj_env.report_dir, False, "执行中断", True)


@log_deco(report=True)
def install_app(app_path):
    """安装应用.

    Args:
        app_path (str): 安装包路径

    Returns:
        bool: 安装是否成功

    """
    return DeviceEnv.dev_mgr.install_app(app_path)


@log_deco(report=True)
def uninstall_app(pkg):
    """卸载应用.

    Args:
        pkg (str): iOS系统为被卸载应用的bundle id

    Returns:
        bool: 卸载是否成功

    """
    return DeviceEnv.dev_mgr.uninstall_app(pkg)


@log_deco(report=True)
def start_app(pkg):
    """启动应用.

    Args:
        pkg (str): iOS系统为被启动应用的bundle id

    Returns:
        bool: 启动是否成功

    """
    if DeviceEnv.os_type == OSType.IOS:
        return DeviceEnv.driver.start_app(pkg)
    elif DeviceEnv.os_type == OSType.ANDROID:
        return DeviceEnv.dev_mgr.start_app(pkg)


@log_deco(report=True)
def restart_app(pkg):
    """重启应用.

    Args:
        pkg (str): iOS系统为被重启应用的bundle id

    Returns:
        bool: 重启是否成功

    """
    if DeviceEnv.os_type == OSType.IOS:
        return DeviceEnv.driver.restart_app(pkg)
    elif DeviceEnv.os_type == OSType.ANDROID:
        return DeviceEnv.dev_mgr.restart_app(pkg)


@log_deco(report=True)
def stop_app(pkg):
    """结束应用.

    Args:
        pkg (str): iOS系统为被结束应用的bundle id

    Returns:
        bool: 结束是否成功

    """
    if DeviceEnv.os_type == OSType.IOS:
        return DeviceEnv.driver.stop_app(pkg)
    elif DeviceEnv.os_type == OSType.ANDROID:
        return DeviceEnv.dev_mgr.stop_app(pkg)



@log_deco(report=True)
def current_app():
    """获取当前应用.

    Returns:
        str: 应用bundle id

    """
    if DeviceEnv.os_type == OSType.ANDROID:
        return DeviceEnv.dev_mgr.current_app()
    elif DeviceEnv.os_type == OSType.IOS:
        return DeviceEnv.driver.current_app()


@log_deco(report=True)
def click_pos(pos, duration=0.05, times=1):
    """坐标点击.

    Args:
        pos (tuple or list): 坐标
        duration (int or float): 点击持续时间
        times (int): 点击次数，以实现双击等效果

    """
    for i in range(times):
        DeviceEnv.driver.click_pos(pos, duration=duration)


@log_deco(report=True)
def slide_pos(pos_from, pos_to=None, pos_shift=None, duration=0):
    """坐标滑动.

    Args:
        pos_from (tuple or list): 滑动起始坐标
        pos_to (tuple or list): 滑动结束坐标，为None时则根据pos_shift滑动
        pos_shift (tuple or list): 滑动偏移距离
        duration (int or float): 起始位置按下时长，以实现拖拽功能

    """
    DeviceEnv.driver.slide_pos(pos_from, pos_to=pos_to, pos_shift=pos_shift, duration=duration)


def get_img():
    """获取设备当前画面.

    Returns:
        ndarray: 画面图像

    """
    return DeviceEnv.driver.get_img()


def rel2abs(pos):
    """相对坐标转换为绝对坐标.

    Args:
        pos (tuple or list): 相对坐标

    Returns:
        tuple: 绝对坐标

    """
    return DeviceEnv.driver.rel2abs(pos)


def abs2rel(pos):
    """绝对坐标转换为相对坐标.

    Args:
        pos (tuple or list): 绝对坐标

    Returns:
        tuple: 相对坐标

    """
    return DeviceEnv.driver.abs2rel(pos)


def find_cv(tpl, img=None, timeout=30, threshold=0.8, pos=None, pos_weight=0.05, ratio_lv=21, is_translucent=False,
            tpl_l=None, offset=None):
    """基于多尺寸模板匹配的图像查找.

    Args:
        tpl (ndarray or str): 待匹配查找的目标图像
        img (ndarray or str): 在该图上进行查找，为None时则获取当前设备画面
        timeout (int): 查找超时时间
        threshold (float): 匹配阈值
        pos (tuple or list): 目标图像的坐标，以辅助定位图像位置
        pos_weight (float): 坐标辅助定位的权重
        tpl_l (ndarray or str): 备选的尺寸更大的目标图像，以辅助定位
        offset (tuple or list): 偏移，图像匹配位置加上该偏移作为结果返回
        ratio_lv (int): 缩放范围，数值越大则进行更大尺寸范围的匹配查找
        is_translucent (bool): 目标图像是否为半透明，为True则会进行图像预处理

    Returns:
        list: 查找到的坐标，未找到则返回None
    """
    tpl = img_parse(tpl)
    tpl_l = img_parse(tpl_l)

    if tpl is None:
        return None

    if img is not None:
        img = img_parse(img)
        if img is not None:
            val, center, ratio, scale_object, vertex = tpl_match(tpl, img, tpl_pos=pos, pos_weight=pos_weight,
                                                                 ratio_lv=ratio_lv, is_translucent=is_translucent,
                                                                 tpl_l=tpl_l, offset=offset)
            if val > threshold:
                return [center[0] / img.shape[1], center[1] / img.shape[0]]
        return None

    tic = time.time()
    toc = tic
    while toc - tic <= timeout:
        img = get_img()
        if img is not None:
            val, center, ratio, scale_object, vertex = tpl_match(tpl, img, tpl_pos=pos, pos_weight=pos_weight,
                                                                 ratio_lv=ratio_lv, is_translucent=is_translucent,
                                                                 tpl_l=tpl_l, offset=offset)
            if val > threshold:
                return [center[0] / img.shape[1], center[1] / img.shape[0]]
        time.sleep(0.5)
        toc = time.time()
    return None


def find_ocr(word, timeout=30, is_regular=True):
    """基于OCR文字识别的查找.

    Args:
        word (str): 待查找文字，支持正则
        timeout (int): 查找超时时间
        is_regular (bool): 为True时进行正则查找

    Returns:
        list: 查找到的中心点坐标

    """
    tic = time.time()
    toc = tic
    while toc - tic <= timeout:
        img = get_img()
        if img is not None:
            word_list = ocr_driver.search_from_img(img, word, is_regular=is_regular)
            if word_list:
                return word_list[0][1]
                # rect = word_list[0][1]
                # x = int((rect[0] + rect[2]) / 2)
                # y = int((rect[1] + rect[3]) / 2)
                # return [x, y]
        toc = time.time()
    return None


def find_ui(xpath, timeout=30, **kwargs):
    """基于控件查找.

    Args:
        xpath (str): 控件xpath
        timeout (int): 查找超时时间
        **kwargs

    Returns:

    """
    return DeviceEnv.driver.get_pos(xpath, timeout=timeout, **kwargs)


@log_deco(report=False)
def find(loc, by=DriverType.CV, timeout=30, **kwarg):
    """查找.

    Args:
        loc: 待查找的元素，具体形式需符合基于的查找类型
        by (DriverType): 查找类型，原生控件DriverType.UI，图像匹配DriverType.CV，文字识别DriverType.OCR，坐标DriverType.POS，
        GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        timeout (int): 查找超时时间
        **kwarg: 基于不同的查找类型，其他需要的参数，具体参见各find函数

    Returns:
        list: 查找到的坐标，未找到则返回None

    """
    if by == DriverType.UI:
        return find_ui(loc, timeout=timeout, **kwarg)
    elif by == DriverType.CV:
        return find_cv(loc, timeout=timeout, **kwarg)
    elif by == DriverType.OCR:
        return find_ocr(loc, timeout=timeout, **kwarg)
    elif by == DriverType.POS:
        return loc
    elif by == DriverType.GA_UNITY or by == DriverType.GA_UE:
        return find_ga(xpath=loc, by=by, timeout=timeout)
    return None


@log_deco(report=False)
def multi_find(ctrl="", img="", pos=None, by=DriverType.UI, ctrl_timeout=30, img_timeout=10, **kwargs):
    """综合查找.

    优先基于控件定位，未查找到则基于图片匹配+坐标定位，仍未找到则返回传入坐标

    Args:
        ctrl (str): 待查找的控件
        img (ndarray or str): 待匹配查找的图像
        pos (list or tuple): 目标图像的坐标，以辅助定位图像位置
        by (DriverType): ctrl的控件类型，原生控件DriverType.UI，GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        ctrl_timeout (int): 基于控件查找的超时时间
        img_timeout (int): 基于图像匹配查找的超时时间
        **kwargs: 不同查找类型需要设置的参数，具体参见各find函数

    Returns:
        list, DriverType: 查找到的中心点坐标及查找结果基于的查找类型

    """
    if ctrl:
        loc_pos = find.__wrapped__(loc=ctrl, by=by, timeout=ctrl_timeout, **kwargs)
        if loc_pos:
            return loc_pos, DriverType.UI
    if img is not None:
        loc_pos = find.__wrapped__(loc=img, by=DriverType.CV, timeout=img_timeout, pos=pos, **kwargs)
        if loc_pos:
            return loc_pos, DriverType.CV
    if pos:
        return pos, DriverType.POS
    return None, -1


@log_deco(report=False)
def click(loc=None, by=DriverType.POS, offset=None, timeout=30, duration=0.05, times=1, **kwargs):
    """点击.

    Args:
        loc: 待点击的元素，具体形式需符合基于的点击类型
        by (DriverType): 查找类型，原生控件DriverType.UI，图像匹配DriverType.CV，文字识别DriverType.OCR，坐标DriverType.POS，
        GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (float): 点击的按压时长，以实现长按
        times (int): 点击次数，以实现双击等效果
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数

    Returns:
        bool: 操作是否成功

    """
    pos = find.__wrapped__(loc=loc, by=by, timeout=timeout, **kwargs)
    if pos:
        if offset:
            pos = rel2abs(pos)
            offset = rel2abs(offset)
            pos = [pos[0] + offset[0], pos[1] + offset[1]]
        # click_pos.__wrapped__(pos, duration=duration, times=times)
        click_pos(pos, duration=duration, times=times)
        return True
    logger.warning("click cannot find target")
    return False


@log_deco(report=False)
def double_click(loc=None, by=DriverType.POS, offset=None, timeout=30, duration=0.05, **kwargs):
    """双击.

    Args:
        loc: 待操作的元素，具体形式需符合基于的操作类型
        by (DriverType): 查找类型，原生控件DriverType.UI，图像匹配DriverType.CV，文字识别DriverType.OCR，坐标DriverType.POS，
        GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (float): 点击的按压时长，以实现长按
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数

    Returns:
        bool: 操作是否成功

    """
    return click(loc=loc, by=by, offset=offset, timeout=timeout, duration=duration, times=2, **kwargs)


@log_deco(report=False)
def long_click(loc=None, by=DriverType.POS, offset=None, timeout=30, duration=1, **kwargs):
    """长按.

    Args:
        loc: 待操作的元素，具体形式需符合基于的操作类型
        by (DriverType): 查找类型，原生控件DriverType.UI，图像匹配DriverType.CV，文字识别DriverType.OCR，坐标DriverType.POS，
        GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (float): 点击的按压时长
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数

    Returns:
        bool: 操作是否成功

    """
    return click(loc=loc, by=by, offset=offset, timeout=timeout, duration=duration, times=1, **kwargs)


@log_deco(report=False)
def slide(loc_from=None, loc_to=None, loc_shift=None, by=DriverType.POS, timeout=30, duration=None, **kwargs):
    """滑动.

    Args:
        loc_from: 滑动起始元素位置
        loc_to: 滑动结束元素位置，为None时则根据loc_shift滑动
        loc_shift (tuple or list): 滑动偏移距离
        by (DriverType): 查找类型，原生控件DriverType.UI，图像匹配DriverType.CV，文字识别DriverType.OCR，坐标DriverType.POS，
        GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        timeout (int): 定位元素的超时时间
        duration (int or float): 起始位置按下时长，以实现拖拽功能
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数

    Returns:
        bool: 操作是否成功

    """
    pos_from = find.__wrapped__(loc=loc_from, by=by, timeout=timeout, **kwargs)
    if not pos_from:
        logger.warning("slide cannot find loc_from target")
        return False

    if loc_to:
        pos_to = find.__wrapped__(loc=loc_to, by=by, timeout=timeout, **kwargs)
        if pos_to:
            slide_pos(pos_from, pos_to, duration=duration)
            return True
        logger.warning("slide cannot find loc_to target")
        return False
    elif loc_shift:
        slide_pos(pos_from=pos_from, pos_shift=loc_shift, duration=duration)
        return True


@log_deco(report=False)
def get_uitree(by=DriverType.UI):
    """获取控件树.

    Args:
        by (DriverType): 获取控件树的类型，系统原生DriverType.UI，GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE

    Returns:
        dict: 控件树

    """
    if by == DriverType.UI:
        return DeviceEnv.ui_driver.get_uitree()
    elif by == DriverType.GA_UNITY:
        return ga_driver.unity.get_uitree()
    elif by == DriverType.GA_UE:
        return ga_driver.ue.get_uitree()


@log_deco(report=False)
def get_elements(xpath, by=DriverType.UI):
    """根据xpath获取元素列表.

    Args:
        xpath (str): 获取元素的xpath
        by (DriverType): 获取元素的类型，系统原生DriverType.UI，GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE

    Returns:
        list: 元素对象的list

    """
    if by == DriverType.UI:
        return DeviceEnv.ui_driver.get_elements(xpath)
    elif by == DriverType.GA_UNITY:
        return ga_driver.unity.get_elements(xpath)
    elif by == DriverType.GA_UE:
        return ga_driver.ue.get_elements(xpath)
    return None


@log_deco(report=True)
def input_text(text, xpath=None, timeout=30, depth=10):
    """文本输入.

    Args:
        text (str): 待输入的文本
        xpath (xpath): iOS需要基于控件输入，xpath形式定位
        timeout (int): 超时时间
        depth (int): source tree的最大深度值，部分应用数值设置过大会导致操作不稳定，过小则可能导致输入失败

    """
    if DeviceEnv.os_type == OSType.IOS:
        DeviceEnv.driver.input_text(xpath=xpath, text=text, timeout=timeout, depth=depth)
    elif DeviceEnv.os_type == OSType.ANDROID:
        DeviceEnv.dev_mgr.input_text(text, timeout=timeout)


@log_deco(report=True)
def press(name):
    """设备功能键操作.

    Args:
        name (DeviceButton): 详见DeviceButton

    """
    if DeviceEnv.os_type == OSType.IOS:
        DeviceEnv.driver.press(name)
    elif DeviceEnv.os_type == OSType.ANDROID:
        DeviceEnv.dev_mgr.press(name)


def screenshot(label="screenshot", img_path=None, pos=None):
    """截图.

    Args:
        label (str): 图像存储的文件名
        img_path (str): 存储图像的路径，为None时则存到默认目录
        pos (tuple or list): 将坐标绘制在图像上

    Returns:
        str: 图像存储路径

    """
    img = None
    for i in range(5):
        img = get_img()
        if img is not None:
            break
        time.sleep(0.2)
    if pos and img is not None:
        sp = img.shape
        if isinstance(pos[0], float) and isinstance(pos[1], float):
            pos_draw = (int(pos[0] * sp[1]), int(pos[1] * sp[0]))
        else:
            pos_draw = (int(pos[0]), int(pos[1]))
        img = cv.circle(img, pos_draw, 4, (0, 0, 255), 2)
    if img is not None:
        if not img_path:
            if proj_env.screenshot_dir:
                img_path = os.path.join(proj_env.screenshot_dir, label + "_" + str(int(time.time())) + ".jpg")
            else:
                img_path = os.path.join(os.path.dirname(__file__), label + "_" + str(int(time.time())) + ".jpg")
        imwrite(img_path, img)
        return img_path
    logger.warning("get img failed")
    return None


@log_deco(report=True)
def stop_driver():
    """结束驱动.

    脚本运行结束后调用，会释放相关驱动，生成报告等.

    """
    if proj_env.report_dir:
        generate_report(proj_env.report_dir)
    if DeviceEnv.run_mode == RunMode.CLOUDTEST:
        cloud_test_report(proj_env.report_dir, True, "执行成功")
    DeviceEnv.driver.stop_driver()


class OptionalScene:
    def __init__(self):
        self.t = None
        self.check_run = True
        self.scene_list = []

    def add_scene(self, loc, exec, args):
        self.check_run = True
        self.scene_list.append([loc, exec, args])

    def start_check(self):
        self.t = threading.Thread(target=self.check_thread)
        self.t.start()

    def stop_check(self):
        self.check_run = False

    def check_thread(self):
        while self.check_run:
            for scene in self.scene_list:
                if scene[0] == "test":
                    scene[1](*scene[2])
            time.sleep(1)


# scene_list = OptionalScene()
# scene_list.start_check()
# scene_list.add_scene("test", ztest, (c,))


"""Android Special API"""


def touch_down(pos, id=0, pressure=50):
    DeviceEnv.driver.touch_down(pos=pos, id=id, pressure=pressure)


def touch_move(pos, id=0, pressure=50):
    DeviceEnv.driver.touch_move(pos=pos, id=id, pressure=pressure)


def touch_up(pos=None, id=0, pressure=50):
    DeviceEnv.driver.touch_up(pos=pos, id=id, pressure=pressure)


"""iOS Special API"""

"""GA Special API"""


def init_ga(engine_type=DriverType.GA_UNITY, port=None):
    args = parse_args()
    # if port:
    #     ga_port = port
    # elif args.ga_port:
    #     ga_port = args.ga_port
    # else:
    #     ga_port = get_free_ports(1)[0]
    ga_port = port if port else args.ga_port

    driver = GADriver()
    driver.start_driver(port=ga_port, os_type=DeviceEnv.os_type, engine_type=engine_type, mode=DeviceEnv.run_mode)
    if engine_type == DriverType.GA_UNITY:
        ga_driver.unity = driver
    elif engine_type == DriverType.GA_UE:
        ga_driver.ue = driver


def find_ga(xpath, by=DriverType.GA_UNITY, timeout=30):
    """基于GA控件的查找.

    Args:
        xpath (str): 元素路径或路径+id的组合，如：/test[@id=1]
        by (DriverType): 查找类型，GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE
        timeout (int): 查找超时时间

    Returns:
        list: GA控件的中心点坐标

    """
    driver = None
    if by == DriverType.GA_UNITY:
        driver = ga_driver.unity
    elif by == DriverType.GA_UE:
        driver = ga_driver.ue
    if driver is None:
        return None
    tic = time.time()
    toc = tic
    while toc - tic <= timeout:
        pos = driver.get_pos(xpath)
        if pos:
            return pos
        toc = time.time()
    return None


def get_driver(by=DriverLib.WDA):
    """返回具体类型的驱动，以便于调用该框架的原生API.

    Args:
        by: 驱动类型，WDA为DriverLib.WDA，UIAutomator为DriverLib.UIA，GA Unity为DriverType.GA_UNITY，GA UE为DriverType.GA_UE

    Returns:
        DeviceEnv: 具体类型的驱动

    """
    if by == DriverLib.WDA:
        return DeviceEnv.ui_driver
    elif by == DriverLib.UIA:
        return DeviceEnv.ui_driver
    elif by == DriverLib.GA_UNITY:
        return ga_driver.unity.driver
    elif by == DriverLib.GA_UE:
        return ga_driver.ue.driver
