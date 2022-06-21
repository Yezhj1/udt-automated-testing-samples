"""运行参数"""
import  argparse


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device_type', type=str, default='HUAWEI')
    parser.add_argument('--phone_address', type=str, default=None)
    parser.add_argument('--app_address', type=str, default=None)
    parser.add_argument('--app_name', type=str, default='com.sohu.inputmathod.sogou')
    return parser.parse_args()
