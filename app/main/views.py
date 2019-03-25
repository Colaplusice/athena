from flask import (
    Blueprint,
    render_template,
    Response,
    redirect,
    url_for,
    request,
    flash,
    jsonify
)
from flask_login import logout_user, login_user

from app.models.user import verify_user
from app.tasks import write_in_database
from app.utils.camera import MacCamera, gen, recognize_image
from app.utils.file import convert_and_save

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/video_feed")
def video_feed():
    res = gen(MacCamera())
    return Response(res, mimetype="multipart/x-mixed-replace; boundary=frame")


@main.route("/snapshot")
def snapshot():
    # 新创建了一个camera
    camera = MacCamera()
    photo = camera.get_frame()
    file = open("test.jpg", "wb+")
    file.write(photo)
    file.close()
    return redirect(url_for(".index"))


@main.route("/upload_recognition", methods=["POST"])
def upload_recognition():
    if request.json:
        image_flow = request.json["data"]
        file_path = convert_and_save(image_flow, request.json["image_name"], "records")
        reco_result = recognize_image(file_path)
        return jsonify(reco_result)
    return render_template("index.html")


@main.route("/results")
def result():
    pass


@main.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")
        remember = True if remember == "on" else False
        user = verify_user(username, password)
        if user is not None:
            login_user(user, remember=remember)
            flash("login success")
            return redirect(url_for("main.index"))
        flash("username and password is invalid")
    return render_template("login.html")


@main.route("/register")
def register():
    return render_template("register.html")


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/test_ajax", methods=["POST", "GET"])
def test_ajax():
    print(request.data)
    print(request.json)
    return render_template("index.html")


@main.route("/save_database", methods=["POST"])
def save_database():
    if request.json:
        image_name = request.json["image_name"]
        file_path = convert_and_save(request.json["data"], image_name, "media")
    else:
        file = request.files["file"]
        file_path = convert_and_save(file, file.filename, "media")
    write_in_database(file_path)
    return render_template("index.html")
