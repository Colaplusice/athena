import json
import threading
import time
from collections import defaultdict
from greenlet import getcurrent as get_ident

import cv2
import dlib
import face_recognition
from flask import current_app
from playhouse.shortcuts import model_to_dict

from app.models.user import UserImage, RecoResult


class CameraEvent(object):
    def __init__(self):
        self.events = {}

    # 唤醒client 线程等待下一帧
    def wait(self):
        ident = get_ident()
        if ident not in self.events:
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    # 当新的frame可用时调用这个函数 发送数据到client
    def set(self):
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                event[0].set()
                event[1] = now
            else:
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    # 当每个帧产生后 唤醒客户端
    def clear(self):
        # print(self.events)
        self.events[get_ident()][0].clear()


class BaseCamera:
    thread = None
    frame = None
    last_access = None

    event = CameraEvent()

    def __init__(self):
        # 初始化线程 定好frame
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            while self.get_frame() is None:
                print("阻塞")
                time.sleep(0)

    def get_frame(self):
        BaseCamera.last_access = time.time()
        BaseCamera.event.wait()
        BaseCamera.event.clear()
        BaseCamera.event.wait()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """
        :return:generator instance
        this function should be used as  Response(BaseCamera.frames())
        you can implement it for kinds of types methods
        """
        raise RuntimeError("must be implemented by subclass")

    @classmethod
    def _thread(cls):
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                break
        BaseCamera.thread = None


class MacCamera(BaseCamera):
    video_source = 0

    def set_video_source(self, source):
        MacCamera.video_source = source

    # core
    @staticmethod
    def frames():
        camera = cv2.VideoCapture(MacCamera.video_source)
        if not camera.isOpened():
            raise RuntimeError("camera not opened")

        while True:
            _, img = camera.read()
            # face_number
            img = get_face_number(img)
            res = cv2.imencode(".jpg", img)[1].tobytes()
            yield res


def get_face_number(img):
    detector = dlib.get_frontal_face_detector()
    font = cv2.FONT_HERSHEY_COMPLEX
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    faces = detector(img_gray, 0)
    print("face number:", faces)
    if len(faces) != 0:
        # 矩形框
        for k, d in enumerate(faces):
            # 计算矩形大小
            # (x,y), (宽度width, 高度height)

            # 计算矩形框大小
            height = d.bottom() - d.top()
            width = d.right() - d.left()

            hh = int(height / 2)
            ww = int(width / 2)

            # 设置颜色 / The color of rectangle of faces detected
            if (
                    (d.right() + ww) > 640
                    or (d.bottom() + hh > 480)
                    or (d.left() - ww < 0)
                    or (d.top() - hh < 0)
            ):
                cv2.putText(
                    img,
                    "OUT OF RANGE",
                    (20, 300),
                    font,
                    0.8,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA,
                )
                color_rectangle = (0, 0, 255)
            else:
                color_rectangle = (255, 255, 255)
            cv2.rectangle(
                img,
                tuple([d.left() - ww, d.top() - hh]),
                tuple([d.right() + ww, d.bottom() + hh]),
                color_rectangle,
                2,
            )
    return img


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


def recognize_image(image_path):
    image = cv2.imread(image_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(
        rgb, model=current_app.config["DETECTION_METHOD"]
    )
    encodings = face_recognition.face_encodings(rgb, boxes)
    name = "unkown"
    if len(encodings) > 0:
        encodings = encodings[0]
        user_encodings = UserImage.select(UserImage.embedding_code, UserImage.user_name)
        name_list = [user_encoding.user_name for user_encoding in user_encodings]
        encoding_list = [
            json.loads(user_encoding.embedding_code) for user_encoding in user_encodings
        ]
        matches = face_recognition.compare_faces(encoding_list, encodings)
        if True in matches:
            match_index = [index for index, value in enumerate(matches) if value]
            counts = defaultdict(int)
            for index in match_index:
                counts[index] += 1
            name = name_list[max(counts.keys(), key=counts.get)]
    reco_result = RecoResult.create(**{"reco_file_path": image_path, "result": name})
    return model_to_dict(reco_result, recurse=False)
