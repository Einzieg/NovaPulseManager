from pathlib import Path

import cv2


class Template:
    def __init__(self, name, threshold, template_path, forbidden=False):
        self.name = name
        self.threshold = threshold
        self.template_path = Path(template_path)
        self.cv_tmp = cv2.imread(str(self.template_path))
        if self.cv_tmp is None:
            raise FileNotFoundError(f"模板图片加载失败: {self.template_path}")
        self.forbidden = forbidden
        # print(f"加载模板:{name} {template_path}")
