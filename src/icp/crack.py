import base64
import platform

import onnxruntime
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


def letterbox_cv2(image, size):
    """
    OpenCV 替代 PIL 的 resize + letterbox 操作。
    image: BGR 格式的 np.ndarray (cv2.imread 结果)
    size: (width, height)
    return: letterbox 后的新图像
    """
    ih, iw = image.shape[:2]
    w, h = size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)

    # 调整图像尺寸
    image_resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_CUBIC)

    # 创建灰底图像
    new_image = np.full((h, w, 3), 128, dtype=np.uint8)

    # 计算偏移量并粘贴
    top = (h - nh) // 2
    left = (w - nw) // 2
    new_image[top:top + nh, left:left + nw] = image_resized

    return new_image


input_shape = (105, 105)


def preprocess(image_path):
    image = letterbox_cv2(image_path, input_shape)
    image = np.asarray(image).astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))  # HWC -> CHW
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image


def get_system_chinese_font(size=80):

    return ImageFont.truetype("STHeiti Medium.ttc", size)


class Crack:
    def __init__(self, siamese_model_path="siamese.onnx", detect_onnx="best.onnx"):
        self.siamese_onnx = onnxruntime.InferenceSession(siamese_model_path)
        self.detect_onnx = onnxruntime.InferenceSession(detect_onnx)

    def read_base64_image(self, base64_string):
        # 解码Base64字符串为字节串
        img_data = base64.b64decode(base64_string)

        # 将解码后的字节串转换为numpy数组（OpenCV使用numpy作为其基础）
        np_array = np.frombuffer(img_data, np.uint8)

        # 使用OpenCV的imdecode函数将字节数据解析为cv::Mat对象
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        return img

    def detect(self, big_img, font_size=5):
        confidence_thres = 0.7
        iou_thres = 0.7
        model_inputs = self.detect_onnx.get_inputs()

        self.big_img = self.read_base64_image(big_img)
        img_height, img_width = self.big_img.shape[:2]
        img = cv2.cvtColor(self.big_img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (512, 192))
        image_data = np.array(img) / 255.0
        image_data = np.transpose(image_data, (2, 0, 1))
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
        input = {model_inputs[0].name: image_data}
        output = self.detect_onnx.run(None, input)
        outputs = np.transpose(np.squeeze(output[0]))
        rows = outputs.shape[0]
        boxes, scores = [], []
        x_factor = img_width / 512
        y_factor = img_height / 192
        for i in range(rows):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            if max_score >= confidence_thres:
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
                left = int((x - w / 2) * x_factor)
                top = int((y - h / 2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                boxes.append([left, top, width, height])
                scores.append(max_score)
        indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_thres, iou_thres)
        # print(len(indices))
        # 取 前5个
        if len(indices) < font_size:
            return False
        new_boxes = [boxes[i] for i in indices[:font_size]]

        return new_boxes

    def detect_ga(self, big_img):
        font_size = 4
        confidence_thres = 0.7
        iou_thres = 0.7
        model_inputs = self.detect_onnx.get_inputs()

        self.big_img = self.read_base64_image(big_img)
        img_height, img_width = self.big_img.shape[:2]
        img = cv2.cvtColor(self.big_img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (330, 155))
        image_data = np.array(img) / 255.0
        image_data = np.transpose(image_data, (2, 0, 1))
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
        input = {model_inputs[0].name: image_data}
        output = self.detect_onnx.run(None, input)
        outputs = np.transpose(np.squeeze(output[0]))
        rows = outputs.shape[0]
        boxes, scores = [], []
        x_factor = img_width / 330
        y_factor = img_height / 155
        for i in range(rows):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            if max_score >= confidence_thres:
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
                left = int((x - w / 2) * x_factor)
                top = int((y - h / 2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                boxes.append([left, top, width, height])
                scores.append(max_score)
        indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_thres, iou_thres)
        # print(len(indices))
        # 取 前5个
        if len(indices) < font_size:
            return False
        new_boxes = [boxes[i] for i in indices[:font_size]]
        pass

    def siamese(self, image_list, boxes, ):
        result_list = []
        for i, origin in enumerate(image_list):
            if len(result_list) == len(image_list):
                break
            ress = []
            for j, box in enumerate(boxes):
                raw_image1 = self.big_img[box[1]:box[1] + box[3] + 2, box[0]:box[0] + box[2] + 2]
                img1 = cv2.cvtColor(raw_image1, cv2.COLOR_BGR2RGB)
                img1 = cv2.resize(img1, (105, 105))
                # cv2.imwrite(f"./{i}_{j}.png", img1)

                image_data_1 = np.array(img1).astype(np.float32) / 255.0
                image_data_1 = np.transpose(image_data_1, (2, 0, 1))
                image_data_1 = np.expand_dims(image_data_1, axis=0)

                inputs = {'input': image_data_1, "input.53": origin}
                output = self.siamese_onnx.run(None, inputs)
                output_sigmoid = 1 / (1 + np.exp(-output[0]))
                res = output_sigmoid[0][0]

                ress.append([res, box[0], box[1]])
            ress.sort(key=lambda x: x[0], reverse=True)
            # print(ress)
            max_res = ress[0]
            result_list.append([max_res[1], max_res[2]])
        # print(result_list)
        return result_list

    def generate_char_image(self, char, size=28):
        # 创建蓝底图像，蓝色 RGB=(0,0,255)
        img = Image.new("RGB", (size, size), color=(0, 143, 255))
        draw = ImageDraw.Draw(img)

        # 加载字体（大小略小于画布，防止超出）
        font = get_system_chinese_font(size=int(size * 0.8))

        # 获取文字边界框
        bbox = draw.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 居中绘制
        x = (size - text_w) // 2
        y = (size - text_h) // 2

        # 字体颜色白色
        draw.text((x, y), char, fill=(255, 255, 255), font=font)
        # 转为 numpy 并处理成模型输入格式
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # cv2.imwrite(f"./{char}.png", img)
        img = cv2.resize(img, (105, 105))

        image_data = img.astype(np.float32) / 255.0
        image_data = np.transpose(image_data, (2, 0, 1))  # (C, H, W)
        image_data = np.expand_dims(image_data, axis=0)  # (1, C, H, W)

        return image_data

    def get_origin_image(self, small_img=None, word_list=None):
        if small_img is not None:
            smaill_img_list = []
            for x in [165, 200, 231, 265]:
                image = self.read_base64_image(small_img)
                image = image[11:11 + 28, x:x + 26]
                img2 = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                img2 = cv2.resize(img2, (105, 105))
                image_data_2 = np.array(img2).astype(np.float32) / 255.0
                image_data_2 = np.transpose(image_data_2, (2, 0, 1))
                image_data_2 = np.expand_dims(image_data_2, axis=0)
                smaill_img_list.append(image_data_2)
            return smaill_img_list
        if word_list is not None:
            img_list = []
            for word in word_list:

                img = self.generate_char_image(word)
                img_list.append(img)
            return img_list

        pass


if __name__ == '__main__':
    crack = Crack()
    image_data = open("./image_data.txt", "r").read()
    boxes = crack.detect(image_data, font_size=4)

    print(crack.siamese(crack.get_origin_image(word_list=[
        "各",
        "很",
        "跟"
    ]), boxes))
