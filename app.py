import os
from flask import Flask, request, jsonify
import requests
import paramiko
import pathlib

app = Flask(__name__)

@app.route("/upload_chart", methods=["POST"])
def upload_chart():
    data = request.get_json(force=True)
    image_url = data.get("url")
    filename = data.get("filename", "chart.png")

    if not image_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # 1) Bild herunterladen
        resp = requests.get(image_url)
        resp.raise_for_status()
        content = resp.content

        # 2) Temporäre Datei speichern
        tmp_path = pathlib.Path("/tmp") / filename
        tmp_path.write_bytes(content)

        # 3) SFTP-Parameter aus Env-Variablen
        host = os.environ["SFTP_HOST"]
        port = int(os.environ.get("SFTP_PORT", 22))
        user = os.environ["SFTP_USER"]
        password = os.environ.get("SFTP_PASS")
        remote_dir = os.environ.get("SFTP_PATH", "/")

        # 4) Mit SFTP hochladen
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=user, password=password)

        sftp = ssh.open_sftp()
        remote_path = pathlib.Path(remote_dir) / filename
        sftp.put(str(tmp_path), str(remote_path))
        sftp.close()
        ssh.close()

        # 5) Temp-Datei löschen
        tmp_path.unlink()

        return jsonify({"status": "uploaded", "remote_path": str(remote_path)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
