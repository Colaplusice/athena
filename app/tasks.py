import json

import cv2
import face_recognition
from flask import current_app
from flask_login import current_user

from app.extentions import celery
from app.models.user import UserImage


@celery.task
def encode_face(image_path, people_name, detection_method="hog"):
    image = cv2.imread(image_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # 在图片上定位到人脸 cnn 精确但缓慢
    boxes = face_recognition.face_locations(rgb, model=detection_method)
    # compute the facial embedding for each face  计算脸的embedding值 结果为128维
    encodings = face_recognition.face_encodings(rgb, boxes)
    # 将数据写入数据库

    UserImage.create({""})


@celery.task
def write_in_database(file_path):
    image = cv2.imread(file_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(
        rgb, model=current_app.config["DETECTION_METHOD"]
    )
    encodings = face_recognition.face_encodings(rgb, boxes)
    if len(encodings):
        encodings = encodings[0]
    user_image_data = {
        "user_name": current_user.name,
        "file_path": file_path,
        "embedding_code": json.dumps(list(encodings)),
    }
    UserImage.create(**user_image_data)
