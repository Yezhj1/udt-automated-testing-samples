# event: https://github.com/Genymobile/scrcpy/blob/25aff0093500c95c90192bc7e78f40ec3f617519/app/src/control_msg.h
# action: https://github.com/Genymobile/scrcpy/blob/25aff0093500c95c90192bc7e78f40ec3f617519/app/src/android/input.h
class TouchEvent:
    EVENT = b'\x02'

    DOWN = b'\x00'
    UP = b'\x01'
    MOVE = b'\x02'
    CANCEL = b'\x03'
    PRESS = b'\x0b'

    PRESS_RELEASE = b'\x0c'
    PLACEHOLDER = b'\x00\x00\x00\x00\x00\x00\x00\x00'
    BUTTON_PRIMARY = b'\x00\x00\x00\x01'
