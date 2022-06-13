# coding=utf-8
import platform

import numpy as np
import cv2 as cv
import os
import socket
import struct
import time
import ctypes
from threading import Thread
from collections import deque
from uitrace.utils.env import proj_env
from uitrace.utils.param import OSType
from uitrace.utils.env import DeviceEnv
from uitrace.device.android.scrcpy.scrcpy_protocol import *
from uitrace.device.android.scrcpy.ffmpeg_wrapper import AVFormatContext, AVCodecContext, AVPacket, AVFrame, \
    read_packet_func
from uitrace.utils.log_handler import get_logger

logger = get_logger()


class ScrcpyDecoder:
    def __init__(self, port=61550):
        self.buff_size = 0x10000
        self.img_queue = deque(maxlen=5)

        if proj_env.platform == OSType.WINDOWS:
            self.lib_path = os.path.join(os.path.dirname(__file__), "lib", "ffmpeg", "win")
        elif proj_env.platform == OSType.MAC:
            self.lib_path = os.path.join(os.path.dirname(__file__), "lib", "ffmpeg", "mac")

        # TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port

        # pointers
        self.frame_ptr = 0
        self.codec_ctx_ptr = 0
        self.format_ctx_ptr = 0

        # thread and flag
        self.decode_thread = None
        self.should_run = False

    @staticmethod
    def ff_err_tag(cd):
        mk_tag = 0
        for i in reversed(cd):
            mk_tag = mk_tag << 8
            mk_tag |= (ord(i) & 0xff)
        result = -int(mk_tag)
        return result

    def start_decoder(self):
        self.should_run = True
        if self.decode_thread is None:
            self.decode_thread = Thread(target=self._run_decoder)
            self.decode_thread.start()

    def _run_decoder(self):
        try:
            lib_file_list = os.listdir(self.lib_path)

            def get_lib_full_path(keyword):
                if proj_env.platform == OSType.WINDOWS:
                    for lib in lib_file_list:
                        if keyword in lib:
                            return os.path.join(self.lib_path, lib)
                elif proj_env.platform == OSType.MAC:
                    for lib in lib_file_list:
                        if "lib" + keyword + ".dylib" == lib:
                            return os.path.join(self.lib_path, lib)
                logger.error("could not find runtime %s at %s" % (keyword, self.lib_path))
                return None

            avutil_lib = get_lib_full_path("avutil")
            swresample_lib = get_lib_full_path("swresample")
            avcodec_lib = get_lib_full_path("avcodec")
            avformat_lib = get_lib_full_path("avformat")

            if None in [avutil_lib, swresample_lib, avcodec_lib, avformat_lib]:
                return -2

            lib_avutil = ctypes.CDLL(avutil_lib)
            lib_swresample = ctypes.CDLL(swresample_lib)
            lib_avcodec = ctypes.CDLL(avcodec_lib)
            lib_avformat = ctypes.CDLL(avformat_lib)

            lib_avformat.av_register_all()

            def clean_decoder():
                if self.frame_ptr:
                    # logger.info("Free frame")
                    lib_avutil.av_free(self.frame_ptr)
                    self.frame_ptr = 0
                if self.codec_ctx_ptr:
                    # logger.info("Free avcodec")
                    lib_avcodec.avcodec_close(self.codec_ctx_ptr)
                    self.codec_ctx_ptr = 0
                if self.format_ctx_ptr:
                    # logger.info("Free avformat")
                    lib_avformat.avformat_close_input(ctypes.byref(self.format_ctx_ptr))
                    self.format_ctx_ptr = 0
                self.sock.close()

            find_decoder = lib_avcodec.avcodec_find_decoder_by_name
            find_decoder.restype = ctypes.POINTER(AVCodecContext)
            decoder_list = [b'h264_mmal', b'h264']
            for decoder in decoder_list:
                codec_ptr = find_decoder(ctypes.c_char_p(decoder))
                if codec_ptr:
                    logger.info("Found %s decoder" % decoder.decode('utf8'))
                    break
            else:
                logger.error("H.264 decoder not found")
                return 1

            # avcodec_alloc_context3创建AVCodecContext结构体
            # 每个AVStream存储一个视频/音频流的相关数据
            # 每个AVStream对应一个AVCodecContext，存储该视频/音频流使用解码方式的相关数据
            alloc_context = lib_avcodec.avcodec_alloc_context3
            alloc_context.restype = ctypes.POINTER(AVCodecContext)
            self.codec_ctx_ptr = alloc_context(codec_ptr)
            if not self.codec_ctx_ptr:
                logger.error("Could not allocate decoder context")
                clean_decoder()
                return 2

            # int avcodec_open2(AVCodecContext *avctx, const AVCodec *codec, AVDictionary **options)
            # 初始化编解码器的AVCodecContext
            # avctx：需要初始化的AVCodecContext
            # codec：输入的AVCodec
            # options：一些选项。例如使用libx264编码的时候，“preset”，“tune”等都可以通过该参数设置
            ret = lib_avcodec.avcodec_open2(self.codec_ctx_ptr, codec_ptr, None)
            if ret < 0:
                logger.error("Could not open H.264 decoder")
                clean_decoder()
                return 3

            format_alloc_context = lib_avformat.avformat_alloc_context
            # AVFormatContext主要存储视音频封装格式中包含的信息
            format_alloc_context.restype = ctypes.POINTER(AVFormatContext)
            self.format_ctx_ptr = format_alloc_context()
            if not self.format_ctx_ptr:
                logger.error("Could not allocate format context")
                clean_decoder()
                return 4

            av_malloc = lib_avutil.av_malloc
            av_malloc.restype = ctypes.POINTER(ctypes.c_ubyte)
            buffer_ptr = av_malloc(self.buff_size)
            if not buffer_ptr:
                logger.error("Could not allocate buffer")
                clean_decoder()
                return 5

            def read_packet_wrapper(_, buff, c_size):
                """获取视频流数据放入解码缓冲，data->buff"""
                try:
                    s, data = self.receive_data(c_size)
                    if s == 0:
                        return self.ff_err_tag('EOF ')
                    else:
                        ctypes.memmove(buff, data, s)
                        return s
                except Exception as e:
                    logger.error(str(e))
                    return self.ff_err_tag('EOF ')

            read_packet_ptr = read_packet_func(read_packet_wrapper)
            av_alloc_ctx = lib_avformat.avio_alloc_context
            av_alloc_ctx.restype = ctypes.c_void_p
            avio_ctx_ptr = av_alloc_ctx(buffer_ptr, self.buff_size, 0, None, read_packet_ptr, None, None)
            if not avio_ctx_ptr:
                logger.error("could not allocate avio context")
                clean_decoder()
                return 6
            self.format_ctx_ptr.contents.pb = avio_ctx_ptr
            open_input = lib_avformat.avformat_open_input
            logger.info("format_ctx_ptr: " + str(self.format_ctx_ptr))
            ret = open_input(ctypes.byref(self.format_ctx_ptr), None, None, None)
            if ret < 0:
                logger.error("could not open video stream")
                clean_decoder()
                return 7
            alloc_frame = lib_avutil.av_frame_alloc
            # 解码后数据：AVFrame
            alloc_frame.restype = ctypes.POINTER(AVFrame)
            self.frame_ptr = alloc_frame()
            # 解码前数据：AVPacket
            packet = AVPacket()
            lib_avcodec.av_init_packet(ctypes.byref(packet))

            while self.should_run:
                # av_read_frame读取码流中的音频若干帧或者视频一帧
                if not lib_avformat.av_read_frame(self.format_ctx_ptr, ctypes.byref(packet)):
                    # 给解码器发送压缩数据
                    ret = lib_avcodec.avcodec_send_packet(self.codec_ctx_ptr, ctypes.byref(packet))
                    if ret < 0:
                        logger.error("Could not send video packet: %d" % ret)
                        break
                    # avcodec_receive_frame获取解码数据
                    ret = lib_avcodec.avcodec_receive_frame(self.codec_ctx_ptr, self.frame_ptr)
                    if not ret:
                        self.push_frame(self.frame_ptr)
                    else:
                        logger.error("Could not receive video frame: %d" % ret)
                    # av_packet_unref将缓存空间的引用计数-1，并将Packet中的其他字段设为初始值。如果引用计数为0，自动的释放缓存空间
                    lib_avcodec.av_packet_unref(ctypes.byref(packet))
                else:
                    logger.error("Could not read packet, quit.")
                    self.should_run = False
            clean_decoder()
        except Exception as e:
            logger.error("Start Decoder error: %s" % str(e))
        return 0

    def close_decoder(self):
        self.should_run = False
        if self.decode_thread:
            self.decode_thread.join()
            self.decode_thread = None

    def push_frame(self, frame_ptr):
        frame = frame_ptr.contents
        w = frame.width
        h = frame.height
        img_yuv = np.zeros((h + h // 2, w, 1), dtype=np.uint8)
        img_yuv[:h, :] = np.ctypeslib.as_array(frame.data[0], shape=(h, frame.linesize[0], 1))[:, :w]
        img_u = np.ctypeslib.as_array(frame.data[1], shape=(h // 2, frame.linesize[1], 1))[:, :w // 2]
        img_v = np.ctypeslib.as_array(frame.data[2], shape=(h // 2, frame.linesize[2], 1))[:, :w // 2]
        img_yuv[h:h + h // 4, : w // 2] = img_u[::2, :]
        img_yuv[h + h // 4:, : w // 2] = img_v[::2, :]
        img_yuv[h:h + h // 4, w // 2:] = img_u[1::2, :]
        img_yuv[h + h // 4:, w // 2:] = img_v[1::2, :]
        img = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR_I420)
        self.img_queue.append(img)

    def get_next_frame(self, latest_image=False):
        if not self.img_queue:
            return None
        else:
            img = self.img_queue.popleft()
            if latest_image:
                while self.img_queue:
                    img = self.img_queue.popleft()
            return img

    def receive_data(self, c_size):
        while self.should_run:
            try:
                data = self.sock.recv(c_size)
                return len(data), data
            except socket.timeout:
                continue
            except:
                return 0, []

    def send_data(self, data):
        return self.sock.send(data)

    def connect(self):
        """建立与scrcpy获取手机画面的连接"""
        try:
            self.sock.settimeout(5)
            self.sock.connect(("127.0.0.1", self.port))
        except Exception:
            logger.exception("scrcpy server connect failed")
            return False

        dummy_byte = self.sock.recv(1)
        if not len(dummy_byte):
            logger.warning("did not receive dummy byte")
            return False
            # raise ConnectionError("Did not receive Dummy Byte!")
        else:
            logger.info("scrcpy server connected!")
        return True

    def get_info(self):
        """获取设备信息"""
        device_name = self.sock.recv(64)
        device_name = device_name.decode("utf-8")
        if not len(device_name):
            raise ConnectionError("Did not receive Device Name!")
        logger.info("Device Name: " + device_name)

        res = self.sock.recv(4)
        frame_width, frame_height = struct.unpack(">HH", res)
        logger.info("WxH: " + str(frame_width) + "x" + str(frame_height))
        info = {
            "device": device_name,
            "height": frame_height,
            "width": frame_width
        }
        return info


class ScrcpyCtrl:
    """建立与scrcpy获取手机画面的连接"""

    def __init__(self, port=61550):
        self.sock = None
        self.height = None
        self.width = None
        self.port = port

    def set_screen(self, height, width):
        self.height = height
        self.width = width

    def connect(self):
        logger.debug("scrcpy server connecting")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", self.port))
        return True

    def write_pos(self, pos):
        buf = (pos[0]).to_bytes(4, byteorder="big")
        buf += (pos[1]).to_bytes(4, byteorder="big")
        buf += self.width.to_bytes(2, byteorder="big")
        buf += self.height.to_bytes(2, byteorder="big")
        return buf

    def touch(self, touch_type, pos, pressure=1, pointer_id=0):
        buf = TouchEvent.EVENT # 触摸事件
        buf += touch_type # 操作类型
        buf += pointer_id.to_bytes(8, byteorder="big") # 操作编号
        buf += self.write_pos(pos) # 操作位置及画面尺寸（非设备真实尺寸）
        buf += pressure.to_bytes(2, byteorder="big") # 触摸压力
        buf += TouchEvent.BUTTON_PRIMARY # AMOTION_EVENT_BUTTON_PRIMARY
        self.sock.send(buf)


class ScrcpyMgr:
    def __init__(self, max_size=800, fps="100", bit_rate="8000000", port=61550):
        self.dev_mgr = DeviceEnv.dev_mgr
        self.port = port

        self.max_size = str(max_size)
        self.max_fps = str(fps)
        self.bit_rate = str(bit_rate)
        self.decoder = None
        self.ctrler = None
        self.info = None
        self.img_cache = None
        self.landscape = False

        self.lib_path = os.path.join(os.path.dirname(__file__), "lib")

        self.last_pos = {}

        self.height = 0
        self.width = 0

        self._scrcpy_pre()

    def _scrcpy_pre(self):
        """初始化并启动scrcpy server"""
        try:
            self.dev_mgr.cmd_adb("forward --remove-all", timeout=10)
            self.dev_mgr.cmd_adb("shell pkill -9 app_process", timeout=10)
            self.dev_mgr.cmd_adb("shell killall -9 app_process", timeout=10)

            self.dev_mgr.cmd_adb(
                "push %s /data/local/tmp/scrcpy-server.jar" % os.path.join(self.lib_path, 'scrcpy-server'), timeout=10)
            self.dev_mgr.cmd_adb("forward tcp:%d localabstract:scrcpy" % self.port, timeout=10)

            logger.info("start scrcpy server")
            clientVersion = "1.17"
            logLevel = "error"  # debug, info, warn or error
            maxSize = self.max_size
            bitRate = self.bit_rate
            maxFps = self.max_fps
            lockedVideoOrientation = "-1"
            tunnelForward = "true"
            rectCrop = "9999:9999:0:0"
            sendFrameMeta = "false"
            control = "true"
            displayId = "0"
            showTouches = "false"
            stayAwake = "true"
            codecOptions = "-"  # profile=1,level=4096

            # 'OMX.qcom.video.encoder.avc' 高通硬解
            # 'c2.android.avc.encoder' 软解
            # 'OMX.google.h264.encoder' 软解
            encoderName = "-"

            self.dev_mgr.cmd_adb(['shell', 'CLASSPATH=/data/local/tmp/scrcpy-server.jar', 'app_process', '/',
                                  'com.genymobile.scrcpy.Server',
                                  clientVersion, logLevel, maxSize, bitRate, maxFps, lockedVideoOrientation,
                                  tunnelForward,
                                  rectCrop,
                                  sendFrameMeta, control, displayId, showTouches, stayAwake, codecOptions, encoderName])

            time.sleep(1.5)
            # if self.__adb.cmd("reverse", "localabstract:scrcpy", "tcp:{0}".format(self.port)).wait() != 0:
            #     raise Exception("bind {} to {} error:".format(self.port, "localabstract:scrcpy"))
        except Exception:
            logger.exception("start scrcpy server error")

    def _disable_forward(self):
        self.dev_mgr.cmd_adb('forward --remove tcp:%d' % self.port)

    def start(self):
        if self.decoder:
            return True
        self.decoder = ScrcpyDecoder(port=self.port)
        self.ctrler = ScrcpyCtrl(port=self.port)
        try:
            # 连接以获取手机画面
            self.decoder.connect()
            self.ctrler.connect()
            # 获取设备信息
            self.info = self.decoder.get_info()
            self.height = self.info["height"]
            self.width = self.info["width"]
            self.ctrler.set_screen(self.height, self.width)
            self.decoder.start_decoder()
            return True
        except Exception:
            self.stop_loop()
            logger.exception("scrcpy start error")
            return False

    def stop(self):
        if self.decoder:
            self.decoder.close_decoder()
            self.decoder = None
        self.dev_mgr.cmd_adb("shell pkill -9 app_process", timeout=10)
        self.dev_mgr.cmd_adb("shell killall -9 app_process", timeout=10)
        self._disable_forward()

    def get_img(self):
        img = self.decoder.get_next_frame(True)
        if img is not None:
            self.height = img.shape[0]
            self.width = img.shape[1]
            self.ctrler.set_screen(self.height, self.width)
            self.landscape = self.height < self.width
            self.img_cache = img.copy()
        return self.img_cache

    def touch_down(self, pos, id=0, pressure=50):
        self.ctrler.touch(touch_type=TouchEvent.DOWN, pos=pos, pressure=pressure, pointer_id=id)
        self.last_pos[id] = pos

    def touch_move(self, pos, id=0, pressure=50):
        self.ctrler.touch(touch_type=TouchEvent.MOVE, pos=pos, pressure=pressure, pointer_id=id)
        self.last_pos[id] = pos

    def touch_up(self, pos=None, id=0, pressure=50):
        if pos:
            up_pos = pos
        else:
            up_pos = self.last_pos[id]
        self.ctrler.touch(touch_type=TouchEvent.UP, pos=up_pos, pressure=pressure, pointer_id=id)

    def touch_reset(self):
        self.ctrler.touch(touch_type=TouchEvent.CANCEL, pos=[0, 0], pressure=0, pointer_id=0)

    def get_info(self):
        return self.info

    def get_rotation(self):
        if self.height > self.width:
            return 0
        else:
            return 1

        # try:
        #     adb_display = subprocess.Popen(
        #         self.adb + ['shell', 'dumpsys', 'display'],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE)
        #     display_info = str(adb_display.communicate())
        #     orientation = int(re.search("orientation=([0-9]+),", display_info).group(1))
        #     return orientation
        # except:
        #     logger.error("adb get orientation error")
        #     if self.height > self.width:
        #         return 0
        #     else:
        #         return 1
