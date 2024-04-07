import math
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
)
from flask_httpauth import HTTPBasicAuth
from flask_paginate import Pagination
from wand.image import Image

UPLOAD_FOLDER = "library"
APP_KEY = os.environ.get("DOCKER_PDF_SERVER_KEY", "super_secret_key")
APP_USER = os.environ.get("DOCKER_PDF_SERVER_USER", "admin")
APP_PASSWORD = os.environ.get("DOCKER_PDF_SERVER_PASSWORD", "password")
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = APP_KEY


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@auth.verify_password
def verify_password(username, password):
    return username == APP_USER and password == APP_PASSWORD


@auth.error_handler
def unauthorized():
    return jsonify({"error": "Unauthorized "}), 401


@app.errorhandler(500)
def internal_server_error():
    return (
        jsonify({"error": "Sorry, the app encountered a 500 internal server error. It just doesn't like you today."}),
        500,)


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

    return render_template(
        "index.html", files=pdf_files_slice, pagination=pagination, last=final_page
    )


@app.route("/search")
@auth.login_required
def search():
    query = request.args.get("query", "")
    limit_exceeded = False
    upload_folder = app.config["UPLOAD_FOLDER"]
    if query:
        query = query.strip()
    pdf_files = [
        file
        for file in os.listdir(upload_folder)
        if file.endswith(".pdf") and query.lower() in file.lower()
    ]
    if len(pdf_files) > 20:
        pdf_files = pdf_files[:20]
        limit_exceeded = True
    return render_template(
        "index.html",
        files=pdf_files,
        query=query,
        pagination=...,
        limit_exceeded=limit_exceeded,
    )


@app.route("/upload", methods=["POST"])
@auth.login_required
def upload_file():
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
            # Generate thumbnail for the first page
            thumbnail_path = os.path.join(app.config["UPLOAD_FOLDER"], filename + ".png")
            with Image(
                    filename=file_path + "[0]", resolution=100
            ) as img:  # Process only the first page
                img.format = "png"
                img.save(filename=thumbnail_path)
        except Exception:
            error_message = ("An error occurred while processing your request. Could not generate thumbnail. " +
                             "The PDF uploaded maybe malformed. You may still view it if your client supports it.")
            return render_template('error.html', error_message=error_message)

        return redirect(url_for("index"))


@app.route("/library/<filename>")
@auth.login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete", methods=["POST"])
@auth.login_required
def delete_file():
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


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


if __name__ == "__main__":
    app.run(port=3030, debug=False)
