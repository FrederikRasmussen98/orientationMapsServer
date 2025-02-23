import zipfile
import io
import os
from flask import Flask, render_template, send_from_directory, request, abort, send_file

app = Flask(__name__)

ROOT_DIR = os.path.relpath(r"data")

@app.route("/browse/<path:subpath>")
@app.route("/browse", defaults={"subpath": ""})
@app.route("/")
def browse(subpath=""):
    abs_path = os.path.join(ROOT_DIR, subpath)

    if not os.path.exists(abs_path):
        return abort(404)

    files = []
    folders = []
    for item in sorted(os.listdir(abs_path)):
        item_path = os.path.join(abs_path, item)
        if os.path.isdir(item_path):
            folders.append(item)
        else:
            files.append(item)

    return render_template("index.html", folders=folders, files=files, current_path=subpath)


@app.route("/download/<path:filepath>")
def download(filepath):
    abs_path = os.path.join(ROOT_DIR, filepath)
    
    if not os.path.exists(abs_path):
        return abort(404)
    
    dir_path, filename = os.path.split(abs_path)
    return send_from_directory(dir_path, filename, as_attachment=True)


@app.route("/download_all")
def download_all():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(ROOT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, ROOT_DIR))

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="all_files.zip")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
