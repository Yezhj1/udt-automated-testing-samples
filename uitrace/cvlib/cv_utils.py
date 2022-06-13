import os
import cv2 as cv
import numpy as np


def imread(img, flags=-1):
    if isinstance(img, np.ndarray):
        return img
    elif isinstance(img, str) and os.path.exists(img):
        return cv.imdecode(np.fromfile(img, dtype=np.uint8), flags)
    return None


def imwrite(file_path, img, params=[]):
    ext = ".jpg"
    ext_arr = file_path.split(".")
    if len(ext_arr) > 0:
        ext = "." + ext_arr[-1]
    return cv.imencode(ext, img, params)[1].tofile(file_path)
