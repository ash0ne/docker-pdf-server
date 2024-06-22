import os
import math
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
    g,
)
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_paginate import Pagination
from werkzeug.security import generate_password_hash, check_password_hash
from wand.image import Image

UPLOAD_FOLDER = "library"
APP_KEY = os.environ.get("DOCKER_PDF_SERVER_KEY", "super_secret_key")
APP_USER = os.environ.get("DOCKER_PDF_SERVER_USER", "admin")
APP_PASSWORD = os.environ.get("DOCKER_PDF_SERVER_PASSWORD", "password")
ENABLE_GUEST_ACCESS = os.environ.get("ENABLE_GUEST_ACCESS", "no")
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = APP_KEY

db = SQLAlchemy(app)
app.app_context().push()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            ("reader", "Reader"),
            ("admin", "Admin"),
            ("maintainer", "Maintainer"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add User")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@auth.verify_password
def verify_password(username, password):
    if username == APP_USER and password == APP_PASSWORD:
        g.current_user = User(username=username, role="admin")
        return g.current_user
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        g.current_user = user
        return g.current_user
    if "yes" == ENABLE_GUEST_ACCESS:
        g.current_user = User(username="default_guest", role="reader")
        return g.current_user
    return None


@auth.error_handler
def unauthorized():
    return jsonify({"error": "Unauthorized"}), 401


@app.before_request
def before_request():
    g.current_user = auth.current_user()


@app.errorhandler(500)
def internal_server_error():
    return (
        jsonify(
            {
                "error": "Sorry, the app encountered a 500 internal server error. It just doesn't like you today."
            }
        ),
        500,
    )


@app.route("/")
@auth.login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 12
    upload_folder = app.config["UPLOAD_FOLDER"]
    pdf_files = [file for file in os.listdir(upload_folder) if file.endswith(".pdf")]

    total_files = len(pdf_files)
    final_page = math.ceil(total_files / per_page)

    start = (page - 1) * per_page
    end = start + per_page

    pdf_files_slice = pdf_files[start:end] if start < total_files else []
    pagination = Pagination(page=page, per_page=per_page, total=total_files)

    pdf_files_with_thumbnails = []
    for file in pdf_files_slice:
        thumbnail_path = f"{file}.png"
        if not os.path.exists(os.path.join(upload_folder, f"{file}.png")):
            thumbnail_path = "pdf-file.png"
        pdf_files_with_thumbnails.append({"file": file, "thumbnail": thumbnail_path})

    return render_template(
        "index.html",
        files=pdf_files_with_thumbnails,
        pagination=pagination,
        last=final_page,
    )


@app.route("/search")
@auth.login_required
def search():
    query = request.args.get("query", "")
    page = request.args.get("page", 1, type=int)
    per_page = 12
    limit_exceeded = False
    upload_folder = app.config["UPLOAD_FOLDER"]

    if query:
        query = query.strip()

    pdf_files = [
        file
        for file in os.listdir(upload_folder)
        if file.endswith(".pdf") and query.lower() in file.lower()
    ]

    total_files = len(pdf_files)
    final_page = math.ceil(total_files / per_page)

    if total_files > 20:
        limit_exceeded = True

    start = (page - 1) * per_page
    end = start + per_page

    pdf_files_slice = pdf_files[start:end] if start < total_files else []
    pagination = Pagination(page=page, per_page=per_page, total=total_files)

    pdf_files_with_thumbnails = []
    for file in pdf_files_slice:
        thumbnail_path = f"{file}.png"
        if not os.path.exists(os.path.join(upload_folder, f"{file}.png")):
            thumbnail_path = "pdf-file.png"
        pdf_files_with_thumbnails.append({"file": file, "thumbnail": thumbnail_path})

    return render_template(
        "index.html",
        files=pdf_files_with_thumbnails,
        query=query,
        pagination=pagination,
        last=final_page,
        limit_exceeded=limit_exceeded,
    )


@app.route("/upload", methods=["POST"])
@auth.login_required
def upload_file():
    if g.current_user.role not in ["admin", "maintainer"]:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("index"))

    if "file" not in request.files:
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            thumbnail_path = os.path.join(
                app.config["UPLOAD_FOLDER"], filename + ".png"
            )
            with Image(filename=file_path + "[0]", resolution=100) as img:
                img.format = "png"
                img.save(filename=thumbnail_path)
        except Exception:
            error_message = "An error occurred while processing your request. Could not generate thumbnail. The PDF uploaded maybe malformed. You may still view it if your client supports it."
            return render_template("error.html", error_message=error_message)

        return redirect(url_for("index"))


@app.route("/library/<filename>")
@auth.login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete", methods=["POST"])
@auth.login_required
def delete_file():
    if g.current_user.role not in ["admin", "maintainer"]:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("index"))

    filename = request.form["filename"]
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        thumbnail_path = os.path.join(app.config["UPLOAD_FOLDER"], filename + ".png")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        flash("File deleted successfully", "success")
    else:
        flash("File not found", "error")
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
@auth.login_required
def admin():
    if g.current_user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("index"))

    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully", "success")
            return redirect(url_for("admin"))

    users = User.query.all()
    return render_template("admin.html", form=form, users=users)


@app.route("/delete_user", methods=["POST"])
@auth.login_required
def delete_user():
    if g.current_user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("index"))

    user_id = request.form["user_id"]
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully", "success")
    else:
        flash("User not found", "error")
    return redirect(url_for("admin"))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


if __name__ == "__main__":
    db.create_all()
    app.run(port=3030, debug=False)
else:
    with app.app_context():
        db.create_all()
