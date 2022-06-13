import os
import logging
from uitrace.utils.env import proj_env

logger_level = logging.INFO
shell_level = logging.INFO
file_level = logging.DEBUG


def stream_handler(formatter=None):
    """日志输出到控制台"""
    sh = logging.StreamHandler()
    sh.setLevel(shell_level)
    if formatter is not None:
        sh.setFormatter(formatter)
    return sh


def file_handler():
    """日志输出到文件"""
    log_dir = proj_env.log_dir
    log_file = os.path.join(log_dir, "log")
    fh = logging.FileHandler(log_file, encoding='utf-8')
    # fh = logging.handlers.TimedRotatingFileHandler(
    #     filename = log_file_path,
    #     when = 'midnight',
    #     backupCount = 0,
    #     encoding = 'utf-8')
    fh.setLevel(file_level)
    log_format = logging.Formatter('[%(asctime)s][%(levelname)s][%(pathname)s-%(lineno)d]%(message)s')
    fh.setFormatter(log_format)
    return fh


def report_handler(log_name):
    """报告数据输出到文件，废弃"""
    report_dir = proj_env.report_dir
    report_file = os.path.join(report_dir, "report_record")
    rh = logging.FileHandler(report_file, encoding='utf-8')
    return rh


def get_logger(log_name="log"):
    logger = logging.getLogger(log_name + str(os.getpid()))
    logger.setLevel(logger_level)

    if not logger.handlers:
        # log输出格式
        log_format = logging.Formatter('[%(asctime)s][%(levelname)s][%(pathname)s-%(lineno)d]%(message)s')

        sh = stream_handler(formatter=log_format)
        logger.addHandler(sh)
        # fh = file_handler(log_name, formatter=log_format)
        # logger.addHandler(fh)
        #
        # if log_name == "report":
        #     rh = report_handler(log_name)
        #     logger.addHandler(rh)

    return logger
