class DriverType(object):
    """面向用户的驱动类型参数，尽量避免用户选择具体的框架"""
    POS = 0
    UI = 1
    OCR = 2
    CV = 3
    GA = 4
    GA_UNITY = 5
    GA_UE = 6

class RunMode(object):
    SINGLE = 0
    MULTI = 1
    IDE = 2
    CLOUDTEST = 3

class DriverLib(object):
    """驱动执行时调用的具体库"""
    SCRCPY = 0
    STF = 1
    WETEST_ONLINE = 2
    WDA = 3
    GA = 4
    GA_UNITY = 5
    GA_UE = 6
    UIA = 7

class OSType(object):
    ANDROID = 0
    IOS = 1
    WINDOWS = 2
    MAC = 3
    LINUX = 4
    OTHER = 5

# Android keys
class DeviceButton(object):
    HOME = 3
    BACK = 4
    VOLUME_UP = 24
    VOLUME_DOWN = 25
    POWER = 26
    DEL = 67
    MENU = 82

    # for iOS special
    LOCK = 1000
    UNLOCK = 1001
