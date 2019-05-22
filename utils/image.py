import base64
import csv
import json
import math
import os

import cv2
import face_recognition
import numpy as np
import tensorflow as tf

from models import UserImage
from .classfiy_utils import (
    ImageCoder,
    make_multi_crop_batch,
    make_multi_image_batch,
    ProgressBar,
)
from .model import select_model, get_checkpoint

RESIZE_FINAL = 227
GENDER_LIST = ["M", "F"]
AGE_LIST = [(0, 2), (4, 6), (8, 12), (15, 20), (25, 32), (38, 43), (48, 53), (60, 100)]
MAX_BATCH_SZ = 128


def get_embedding_code(image_path, model="hog"):
    image = cv2.imread(image_path)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model=model)
    encodings = face_recognition.face_encodings(rgb, boxes)
    encoding = [] if len(encodings) == 0 else encodings[0]
    return json.dumps(list(encoding))


def save_user_image(username, filename, file_stream):
    user_path = "static/file/upload/{}/".format(username)
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    file_path = user_path + filename
    if os.path.exists(file_path):
        return False
    with open(file_path, "wb") as opener:
        # from json
        if isinstance(file_stream, str):
            file_stream = base64.decodebytes(file_stream.encode("utf-8"))
        opener.write(file_stream)
    UserImage.create(
        user_name=username,
        file_path=file_path,
        embedding_code=get_embedding_code(file_path),
    )
    return True


def get_encodings():
    user_images = UserImage.select(UserImage.embedding_code, UserImage.user_name)
    data = {}
    print(user_images[0].embedding_code)
    data["embedding_code"] = [
        json.loads(user_image.embedding_code)
        for user_image in user_images
        if user_image.embedding_code != "[]"
    ]
    data["user_name"] = [
        user_image.user_name.name
        for user_image in user_images
        if user_image.embedding_code != "[]"
    ]
    return data


def guess_name(image, detection_method="cnn"):
    if isinstance(image, str):
        image = cv2.imread(image)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model=detection_method)
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []
    data = get_encodings()
    for encoding in encodings:
        # 这里 修改为根据最大的距离来选择人物
        name = "Unknown"
        distance = face_recognition.face_distance(data["embedding_code"], encoding)
        print(distance)
        max_index = np.argmin(distance)
        print(data['user_name'], distance[max_index])
        names.append(
            data["user_name"][int(max_index)] if distance[max_index] < 0.6 else name
        )
        # matches = face_recognition.compare_faces(data["embedding_code"], encoding, tolerance=0.8)
        # if True in matches:
        #     match_indexs = [index for (index, value) in enumerate(matches) if value]
        #     counts = defaultdict(int)
        #     for ind in match_indexs:
        #         name = data["user_name"][ind]
        #         counts[name] += 1
        #     print('this is count',counts)
        #     name = max(counts, key=counts.get)
        # names.append(name)
    for ((top, right, bottom, left), name) in zip(boxes, names):
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 1)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(
            image, str(name), (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.785, (0, 255, 0), 4
        )
    return image


def guess_age_and_sex(filename):
    model_type = "inception"
    requested_step = None
    checkpoint = "checkpoint"
    single_look = False
    device_id = "/cpu:0"
    reco_list = {"age": "model/22801", "gender": "model/21936"}
    results = {}
    for face_class_type, model_dir in reco_list.items():
        tf.reset_default_graph()
        config = tf.ConfigProto(allow_soft_placement=True)
        with tf.Session(config=config) as sess:
            label_list = AGE_LIST if face_class_type == "age" else GENDER_LIST
            n_labels = len(label_list)
            model_fn = select_model(model_type)
            with tf.device(device_id):
                # 初始化一个tensor
                images = tf.placeholder(
                    tf.float32, [None, RESIZE_FINAL, RESIZE_FINAL, 3]
                )
                logits = model_fn(n_labels, images, 1, False)
                tf.global_variables_initializer()
                requested_step = requested_step
                checkpoint_path = model_dir
                model_checkpoint_path, global_step = get_checkpoint(
                    checkpoint_path, requested_step, checkpoint
                )
                saver = tf.train.Saver()
                saver.restore(sess, model_checkpoint_path)
                softmax_output = tf.nn.softmax(logits)
                coder = ImageCoder()

                if single_look:
                    pass
                    # classify_many_single_crop(
                    #     sess, label_list, softmax_output, coder, images, image_files
                    # )
                else:
                    results[face_class_type] = classify_one_multi_crop(
                        sess, label_list, softmax_output, coder, images, filename
                    )
    return results


def classify_many_single_crop(
        sess, label_list, softmax_output, coder, images, image_files
):
    try:
        num_batches = math.ceil(len(image_files) / MAX_BATCH_SZ)
        pg = ProgressBar(num_batches)
        for j in range(num_batches):
            start_offset = j * MAX_BATCH_SZ
            end_offset = min((j + 1) * MAX_BATCH_SZ, len(image_files))

            batch_image_files = image_files[start_offset:end_offset]
            print(start_offset, end_offset, len(batch_image_files))
            image_batch = make_multi_image_batch(batch_image_files, coder)
            batch_results = sess.run(
                softmax_output, feed_dict={images: image_batch.eval()}
            )
            batch_sz = batch_results.shape[0]
            for i in range(batch_sz):
                output_i = batch_results[i]
                best_i = np.argmax(output_i)
                best_choice = (label_list[best_i], output_i[best_i])
                print("Guess @ 1 %s, prob = %.2f" % best_choice)
            pg.update()
        pg.done()
    except Exception as e:
        print(e)
        print("Failed to run all images")


def classify_one_multi_crop(
        sess, label_list, softmax_output, coder, images, image_file
):
    print("Running file %s" % image_file)
    image_batch = make_multi_crop_batch(image_file, coder)
    batch_results = sess.run(softmax_output, feed_dict={images: image_batch.eval()})
    output = batch_results[0]
    batch_sz = batch_results.shape[0]

    for i in range(1, batch_sz):
        output = output + batch_results[i]

    output /= batch_sz
    best = np.argmax(output)
    # ((15,20), '0.8562081')
    best_choice = (label_list[best], output[best])
    print("this is best choice", best_choice)
    if isinstance(best_choice[0], tuple):
        result = (best_choice[0][0] + best_choice[0][1]) // 2
    else:
        result = best_choice[0]
    return result


def list_images(srcfile):
    with open(srcfile, "r") as csvfile:
        delim = "," if srcfile.endswith(".csv") else "\t"
        reader = csv.reader(csvfile, delimiter=delim)
        if srcfile.endswith(".csv") or srcfile.endswith(".tsv"):
            print("skipping header")
            _ = next(reader)

        return [row[0] for row in reader]


def resolve_file(fname):
    if os.path.exists(fname):
        return fname
    for suffix in (".jpg", ".png", ".JPG", ".PNG", ".jpeg"):
        cand = fname + suffix
        if os.path.exists(cand):
            return cand
    return None


def add_label(image, **kwargs):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model="cnn")
    name_list = []
    for key, value in kwargs.items():
        name_list.append(":".join([str(key), str(value)]))
    names = ["\n".join(name_list)]
    for ((top, right, bottom, left), name) in zip(boxes, names):
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(
            image, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.785, (0, 255, 0), 2
        )
    return image
