import cv2
import dlib

from utils.image import guess_name


class MacCamera:
    def __init__(self):
        # select first video device in system
        self.cam = cv2.VideoCapture(0)
        # set camera resolution
        self.w = 800
        self.h = 600
        # set crop factor
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
        self.detection_method = "hog"

    def get_frame(self, fd=False):
        success, image = self.cam.read()
        # scale image
        image = cv2.resize(image, (self.w, self.h))
        if fd:
            image = guess_name(image)
        # encoding picture to jpeg
        ret, jpeg = cv2.imencode(".jpg", image)
        return jpeg.tobytes()

    def face_detection(self, image):
        detector = dlib.get_frontal_face_detector()
        font = cv2.FONT_HERSHEY_COMPLEX
        img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = detector(img_gray, 0)
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
                        d.right() + ww > 640
                        or d.bottom() + hh > 480
                        or d.left() - ww < 0
                        or d.top() - hh < 0
                ):
                    cv2.putText(
                        image,
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
                    image,
                    tuple([d.left() - ww, d.top() - hh]),
                    tuple([d.right() + ww, d.bottom() + hh]),
                    color_rectangle,
                    2,
                )
        return image
