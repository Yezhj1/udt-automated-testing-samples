# version: 2.2
import cv2 as cv
import numpy as np
from threading import Thread


class RThread(Thread):
    def __init__(self, target, args):
        super(RThread, self).__init__()
        self.func = target
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except:
            return None


def match_thread(tpl, img, ratio, scale_type, tpl_pos=None, tpl_l=None, offset=None, pos_weight=0.05):
    img_sp = img.shape
    tpl_sp = tpl.shape
    if tpl_sp[0] > img_sp[0] or tpl_sp[1] > img_sp[1]:
        return None
    if tpl_l is not None:
        tpll_sp = tpl_l.shape
        if tpll_sp[0] > img_sp[0] or tpll_sp[1] > img_sp[1]:
            tpl_l = None

    # img_blur = cv.medianBlur(img, 3)  # cv.GaussianBlur(img_re, (3, 3), 0)
    # tpl_blur = cv.medianBlur(tpl, 3)  # cv.GaussianBlur(tpl, (3, 3), 0)

    res_s = cv.matchTemplate(tpl, img, cv.TM_CCOEFF_NORMED)
    if tpl_l is not None:
        res_l = cv.matchTemplate(tpl_l, img, cv.TM_CCOEFF_NORMED)

        M = np.float32([[1, 0, offset[0]], [0, 1, offset[1]]])
        sp_l = res_l.shape
        res_l = cv.warpAffine(res_l, M, (sp_l[1], sp_l[0]))
        sp_s = res_s.shape
        res_l = cv.copyMakeBorder(res_l, 0, sp_s[0] - sp_l[0], 0, sp_s[1] - sp_l[1], cv.BORDER_CONSTANT, value=(0))
        res = res_s + res_l * 0.8
        # res = res_l
        # min_vals, max_vals, min_locs, max_locs = cv.minMaxLoc(res_s)
        # min_vall, max_vall, min_locl, max_locl = cv.minMaxLoc(res_l)
    else:
        res = res_s

    pos_ratio = 1
    if scale_type == "img":
        pos_ratio = ratio

    if tpl_pos:
        # flat_indices = np.argsort(-res.ravel())
        # row_indices, col_indices = np.unravel_index(flat_indices, res.shape)
        flat_indices = np.argpartition(-res.ravel(), 10)[:11]
        row_indices, col_indices = np.unravel_index(flat_indices, res.shape)
        rlt = []
        for i in range(10):
            r = row_indices[i]
            c = col_indices[i]
            sim = res[r][c] + pos_weight / (
                    (((r - tpl_pos[1] * pos_ratio) ** 2 + (c - tpl_pos[0] * pos_ratio) ** 2) ** 0.5) / 100 + 1)
            rlt.append([sim, (c, r)])

        # def get_dist(item):
        #     return item[0]
        #
        # rlt.sort(key=get_dist, reverse=True)
        rlt.sort(reverse=True)

        max_val = rlt[0][0]
        max_loc = rlt[0][1]
        return [max_val, max_loc, ratio, scale_type]

    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    return [max_val, max_loc, ratio, scale_type]


def translucent_proc(img, binary_thr):
    img_blur = cv.GaussianBlur(img, (3, 3), 0)
    img_gray = cv.cvtColor(img_blur, cv.COLOR_BGR2GRAY)
    retval, img_binary = cv.threshold(img_gray, binary_thr, 255, cv.THRESH_BINARY)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2, 2))
    img_proc = cv.erode(img_binary, kernel)
    return img_proc


def tpl_match(tpl, img, tpl_pos=None, pos_weight=0.05, ratio_lv=21, is_translucent=False, tpl_l=None, offset=None):
    if is_translucent:
        img_blur = cv.GaussianBlur(tpl, (3, 3), 0)
        binary_thr = np.mean(img_blur)
        tpl = translucent_proc(tpl, binary_thr)
        img = translucent_proc(img, binary_thr)
        if tpl_l is not None:
            tpl_l = translucent_proc(tpl_l, binary_thr)

    img_sp = img.shape
    tpl_sp = tpl.shape
    if tpl_l is not None:
        tpll_sp = tpl_l.shape
    t_list = []
    isp_re = (0, 0)
    tsp_re = (0, 0)
    for ratio in range(1, ratio_lv):
        ratio = 1 - ratio / 100
        sp_re = (round(img_sp[1] * ratio), round(img_sp[0] * ratio))
        if sp_re != isp_re:
            img_re = cv.resize(img, sp_re)
            t = RThread(target=match_thread,
                        args=(tpl, img_re, ratio, "img", tpl_pos, tpl_l, offset, pos_weight))
            t.start()
            t_list.append(t)
            isp_re = sp_re

        sps_re = (round(tpl_sp[1] * ratio), round(tpl_sp[0] * ratio))
        if sps_re != tsp_re:
            tpl_re = cv.resize(tpl, sps_re)
            if tpl_l is not None:
                spl_re = (round(tpll_sp[1] * ratio), round(tpll_sp[0] * ratio))
                tpll_re = cv.resize(tpl_l, spl_re)
                offset_re = [round(offset[0] * ratio), round(offset[1] * ratio)]
            else:
                tpll_re = tpl_l
                offset_re = offset

            t = RThread(target=match_thread,
                        args=(tpl_re, img, ratio, "tpl", tpl_pos, tpll_re, offset_re, pos_weight))
            t.start()
            t_list.append(t)
            tsp_re = sps_re

    t = RThread(target=match_thread, args=(tpl, img, 1, "none", tpl_pos, tpl_l, offset, pos_weight))
    t.start()
    t_list.append(t)

    thread_rlt = []
    for t in t_list:
        t.join()
        result = t.get_result()
        if result:
            thread_rlt.append(result)

    # def get_dist(item):
    #     return item[0]
    #
    # thread_rlt.sort(key=get_dist, reverse=True)
    thread_rlt.sort(reverse=True)
    max_val, max_loc, ratio, scale_type = thread_rlt[0]
    if scale_type == "img":
        max_loc = (round(max_loc[0] / ratio), round(max_loc[1] / ratio))

    width = tpl_sp[1]
    height = tpl_sp[0]
    if scale_type == "img":
        width /= ratio
        height /= ratio
    elif scale_type == "tpl":
        width *= ratio
        height *= ratio

    target_center = (max_loc[0] + int(width / 2), max_loc[1] + int(height / 2))
    target_vertex = max_loc

    return max_val, target_center, ratio, scale_type, target_vertex
