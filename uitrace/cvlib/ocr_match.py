import re
import os
import shutil
from uitrace.cvlib.cv_utils import imread
from uitrace.utils.log_handler import get_logger
from uitrace.utils.toolkit import is_contain_chinese, get_default_appdata

logger = get_logger()
cur_dir = os.path.dirname(os.path.abspath(__file__))


def check_zh_ocr_path():
    model_path = os.path.join(cur_dir, "ocrmodel")
    # if is_contain_chinese(model_path):
    app_data = get_default_appdata()
    model_local_path = os.path.join(app_data, "ocrmodel")
    if not os.path.exists(model_local_path):
        shutil.copytree(model_path, model_local_path)
    return model_local_path
    # return model_path


class OcrMatcher:
    def __init__(self):
        self.ocr_model = {}

    def ocr_core(self, img_data, text_type="ch"):
        try:
            try:
                from paddleocr import PaddleOCR
            except Exception as e:
                logger.warning("import ocrlib failed: %s" % str(e))
                return []
            if not (text_type in self.ocr_model.keys()):
                model_path = check_zh_ocr_path()
                ocr = PaddleOCR(det_model_dir=os.path.join(model_path, "det"),
                                rec_model_dir=os.path.join(model_path, "rec", text_type),
                                # rec_char_dict_path=os.path.join(self.cur_dir, "paddle", "rec", "ppocr_keys_v1.txt"),
                                cls_model_dir=os.path.join(model_path, "cls"),
                                use_angle_cls=True, lang=text_type, use_gpu=False)
                self.ocr_model[text_type] = ocr

            result = self.ocr_model[text_type].ocr(img_data, cls=True)
            return result
        except Exception as e:
            logger.error("OCR Error: " + str(e))
        return []

    # [[[789.0, 20.0], [992.0, 24.0], [991.0, 75.0], [788.0, 71.0]], ('Dolphin', 0.9992546)]
    def get_text(self, img, text_type="ch"):
        img_data = imread(img)
        return self.ocr_core(img_data, text_type)

    def rect2pos(self, rect, sp=None):
        x = int((rect[0][0] + rect[1][0] + rect[2][0] + rect[3][0]) / 4)
        y = int((rect[0][1] + rect[1][1] + rect[2][1] + rect[3][1]) / 4)
        if sp:
            x /= sp[1]
            y /= sp[0]
        return [x, y]

    def search_from_img(self, img, word, is_regular=True):
        text = []
        img = imread(img)
        text_list = self.get_text(img)
        if text_list:
            for item in text_list:
                rect, ocr_word = item
                if (is_regular and re.search(word, ocr_word[0])) or (not is_regular and word == ocr_word[0]):
                    text.append([ocr_word[0], self.rect2pos(rect, sp=img.shape)])
        return text


ocr_driver = OcrMatcher()
