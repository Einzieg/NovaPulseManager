import asyncio
import base64
import json
import logging
import time

import cv2
import requests
from rapidocr_onnxruntime import RapidOCR


class OcrTools:

    def __init__(self):
        self.ocr_engine = None

    def init_engine(self):
        try:
            # 配置 RapidOCR 参数
            # 注意：GPU模式需要安装 onnxruntime-gpu，否则会报错
            if device == "GPU (CUDA)":
                options = {
                    "Det": {"use_cuda": True},
                    "Cls": {"use_cuda": True},
                    "Rec": {"use_cuda": True}
                }
            else:
                # CPU 模式（默认配置）
                options = {}

            self.ocr_engine = RapidOCR(**options)
        except Exception as e:
            # 初始化失败（通常是因为缺少显卡驱动或DLL）
            print(f"Error init engine: {e}")
            # 强制回退到 CPU
            self.ocr_engine = RapidOCR()

    def run_ocr(self, img):
        try:
            result, elapse = self.ocr_engine(img)

            output_text = ""
            if result:
                for item in result:
                    output_text += f"{item[1]}\n"
            else:
                output_text = "未检测到文本。"

            self.root.after(0, lambda: self.finish_ocr(output_text))

        except Exception as e:
            raise RuntimeError(f"识别出错: {e}\n\n可能原因：\n1. 显存不足\n2. CUDA版本不匹配\n建议切换回 CPU 模式。")
