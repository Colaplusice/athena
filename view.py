import base64
import json
import logging
import os
import time

import cv2
import numpy as np
import oss2
import tornado.ioloop
from playhouse.shortcuts import model_to_dict
from tornado import gen, web, httpclient, httpserver
from tornado.web import url, RequestHandler, Application

from camera import MacCamera
from models import database, User, encode_user, UserImage
from utils.faceswap import merge
from utils.image import save_user_image, guess_age_and_sex, add_label, guess_name

cam = MacCamera()


def select_demo_path():
    image_path = "static/file/upload/"
    path_list = []
    temp_list = []
    for person_dir in os.listdir(image_path):
        person_path = os.path.join(image_path, person_dir)
        if not os.path.isdir(person_path) or not os.listdir(person_path):
            continue
        image = os.path.join(person_path, os.listdir(person_path)[-1])
        temp_list.append(image)
        if len(temp_list) == 5:
            path_list.append(temp_list)
            temp_list = []
    return path_list


class App(Application):
    def __init__(self, *args, **kwargs):
        self.db = database.database
        super(App, self).__init__(*args, **kwargs)


class BaseHandler(RequestHandler):
    def get_current_user(self):
        id = self.get_cookie("_id")
        if id is not None:
            user = User.get_user(id)
            if user is not None:
                return user


def make_app():
    current_dir = os.path.dirname(__file__)
    static_dir = os.path.join(current_dir, "static")
    template_dir = os.path.join(current_dir, "templates")
    settings = {
        "template_path": template_dir,
        "login_url": "/login",
        "static_path": static_dir,
        "debug": True,
    }
    app = App(
        [
            url(r"/", MainHandler, name="index"),
            url(r"/play", PlayHandler),
            url("/stream_handler", StreamingIoHandler, name="stream"),
            url("/video_stream", StreamVideoHandler, name="video_stream"),
            url("/login", LoginHandler, name="login"),
            url("/register", RegisterHandler, name="register"),
            url("/add_database", AddDatabaseHandler, name="add_database"),
            url("/snapshot", SnapshotHandler, name="snapshot"),
            url("/profile", ProfileHandler, name="profile"),
            url("/logout", LogoutHandler, name="logout"),
            url("/recognize", RecognizeHandler, name="recognize"),
            url("/showimage", ShowImageHandler, name="showimage"),
            url("/real_time", RealTimeHandler, name="real_time"),
            url(
                "/feature_recognition",
                FeatureRecognitionHandler,
                name="feature_recognition",
            ),
            url("/add_people", AddPeopleHandler, name="add_people"),
            url("/face_merge", FaceMergeHandler, name="face_merge"),
        ],
        **settings
    )
    return app


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.clear_cookie("_id")
        self.redirect("/")


class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html", image_list=select_demo_path())


class RegisterHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render("register.html")

    def post(self, *args, **kwargs):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")
        email = self.get_body_argument("email")
        user, _created = User.get_or_create(
            name=username, defaults={"password": password, "email": email}
        )

        if not _created:
            self.render("register.html", message="用户名或邮箱重复")
        if self.request.files.get("image"):
            image = self.request.files["image"][0]
            filename = image["filename"]
            save_user_image(username, filename, image["body"])
        return self.redirect(self.render("login.html", message="注册成功"))


class RecognizeHandler(BaseHandler):
    def post(self, *args, **kwargs):
        image_name = self.get_body_argument("image_name", default=None)
        if image_name:
            image = guess_name(image_name)
        else:
            file_stream = self.request.files["image"][0]["body"]
            img = cv2.imdecode(np.fromstring(file_stream, np.uint8), 1)
            image = guess_name(img)
        cv2.imwrite("static/face_result.jpg", image)
        self.write("success")


class ShowImageHandler(BaseHandler):
    # 接受参数 将图片画上去
    def get(self, *args, **kwargs):
        age = int(self.get_argument("age"))
        # gender = self.get_argument('gender')
        image_name = "temp.png"
        image = cv2.imread(image_name)
        image = add_label(image, age=age)
        self.set_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0",
        )
        self.set_header("Pragma", "no-cache")
        self.set_header(
            "Content-Type", "multipart/x-mixed-replace;boundary=--jpgboundary"
        )
        self.set_header("Connection", "close")
        my_boundary = "--jpgboundary"
        self.write(my_boundary)
        self.write("Content-type: image/jpeg\r\n")
        self.write("Content-length: %s\r\n\r\n" % len(image))
        ret, jpeg = cv2.imencode(".jpg", image)
        self.write(jpeg.tobytes())


class LoginHandler(BaseHandler):
    def post(self, *args, **kwargs):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")
        user = (
            User.select()
            .where(User.password == password, User.name == username)
            .first()
        )
        if user is not None:
            self.set_cookie("_id", encode_user(username, password))
            self.redirect("/")
        self.render("login.html", message="登录失败，用户名或密码不正确")

    def get(self, *args, **kwargs):
        self.render("login.html")


class PlayHandler(BaseHandler):
    def get(self):
        self.write("HELLO")


class StreamingIoHandler(web.RequestHandler):
    def on_chunk(self, chunk):
        self.write("some chunk")
        self.flush()

    @gen.coroutine
    def get(self):
        client = httpclient.AsyncHTTPClient()
        self.write("some opening")
        self.flush()
        requests = [
            httpclient.HTTPRequest(
                url="http://httpbin.org/delay/" + str(delay),
                streaming_callback=self.on_chunk,
            )
            for delay in [5, 4, 3, 2, 1]
        ]
        yield list(map(client.fetch, requests))
        self.write("some closing")
        self.finish()


class AddDatabaseHandler(BaseHandler):
    """
    user take photo from client camera
    and upload to server
    """

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        return self.render("add_user_image.html")

    def post(self, *args, **kwargs):
        name = None
        if self.request.files.get("image"):
            # from form
            file_stream = self.request.files["image"][0]["body"]
            filename = self.request.files["image"][0]["filename"]
            name = self.get_body_argument("username")

        else:
            # from client camera
            body = json.loads(self.request.body)
            file_stream = base64.decodebytes(body["data"].encode("utf-8"))
            filename = "snapshot_{}.png".format(time.time())
        save_user_image(name or self.current_user.name, filename, file_stream)
        self.write("添加成功!")


class AddPeopleHandler(RequestHandler):
    """
    user take photo from client camera
    and upload to server
    """

    def post(self, *args, **kwargs):
        # from form
        file_stream = self.request.files["image"][0]["body"]
        filename = self.request.files["image"][0]["filename"]
        username = self.get_body_argument("username")
        User.get_or_create(
            name=username,
            defaults={
                "password": "password",
                "email": "{}@icecola.com".format(username),
            },
        )
        result = save_user_image(username, filename, file_stream)
        if result:
            message = "添加成功"
        else:
            message = "您添加的照片已存在"
        self.render("index.html", message=message, image_list=select_demo_path())


class StreamVideoHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
        self.set_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0",
        )
        self.set_header("Pragma", "no-cache")
        self.set_header(
            "Content-Type", "multipart/x-mixed-replace;boundary=--jpgboundary"
        )
        self.set_header("Connection", "close")
        self.served_image_timestamp = time.time()
        face_detection = self.get_argument("fd")
        my_boundary = "--jpgboundary"
        while True:
            img = cam.get_frame(face_detection)
            interval = 0.1
            if self.served_image_timestamp + interval < time.time():
                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                self.write(img)
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)


class RealTimeHandler(BaseHandler):
    def get(self, *args, **kwargs):
        pass

        # self.render("server_camera.html")


class SnapshotHandler(BaseHandler):
    def get(self, *args, **kwargs):
        cam = MacCamera()
        file_stream = cam.get_frame()
        user = self.current_user
        file_name = "snapshot_{}.png".format(time.time())
        save_user_image(user.name, file_name, file_stream)
        self.write("success")
        # return self.render('server_camera.html', message="采集成功!")


class ProfileHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        user = self.current_user
        user_images = UserImage.select().where(UserImage.user_name == user.name)
        user_messages = [
            model_to_dict(user_image, recurse=False) for user_image in user_images
        ]
        self.render("profile.html", user_messages=user_messages)


class FeatureRecognitionHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render("feature_recognition.html")

    def post(self, *args, **kwargs):

        if self.request.files.get("image"):
            # file stream
            file_stream = self.request.files["image"][0]["body"]
        else:
            body = json.loads(self.request.body)
            file_stream = base64.decodebytes(body["data"].encode("utf-8"))
        file_name = os.path.join(os.path.abspath(os.curdir), "temp.png")
        with open(file_name, "wb") as writer:
            writer.write(file_stream)
        result = guess_age_and_sex(file_name)
        self.write(json.dumps(result))


auth = oss2.Auth("LTAIA21kRoVgFGeD", "qrsTxcohl0kyouN9XWujOKULu5SUMR")
service = oss2.Service(auth, "oss-cn-beijing.aliyuncs.com")
import datetime


# # 上传图片文件到OSS上，返回网络路径，上传完之后删除本地的文件
def uploadFileToOSS(output_file):
    bucket = oss2.Bucket(auth, "oss-cn-beijing.aliyuncs.com", "icecola")
    file_url = "https://icecola.oss-cn-beijing.aliyuncs.com"
    fileName = (
        "merge_image/" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    )
    bucket.put_object_from_file(fileName, output_file)
    if os.path.exists(output_file):
        # 删除文件
        os.remove(output_file)
    return os.path.join(file_url, fileName)


class FaceMergeHandler(RequestHandler):
    def get(self, *args, **kwargs):
        self.render("face_merge.html")

    def post(self):
        try:
            # 显示照片
            src_image = self.request.files["base_image"][0]["body"]
            # 待融合照片
            merge_image = self.request.files["merge_image"][0]["body"]
        except KeyError:
            self.write("not image")
            return
        src_img = cv2.imdecode(np.fromstring(src_image, np.uint8), 1)
        merge_img = cv2.imdecode(np.fromstring(merge_image, np.uint8), 1)
        try:
            image_name = merge(src_img, merge_img)
            image_path = uploadFileToOSS(image_name)
            self.write(image_path)
        except Exception as e:
            raise tornado.web.HTTPError(status_code=400, log_message=str(e.args))


if __name__ == "__main__":
    app = make_app()
    port = 8888
    logging.warning("index:http://localhost:{}".format(port))
    http_server = httpserver.HTTPServer(make_app())
    http_server.listen(port)
    # app.listen(port)
    tornado.ioloop.IOLoop.instance().start()
