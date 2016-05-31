import email.mime.application
import email.mime.multipart
import os
import smtplib
import subprocess
import tempfile

from flask import Flask, request

from kindle_daemon import config

app = Flask(__name__)


def send_mail(data):
    msg = email.mime.multipart.MIMEMultipart()
    msg["Subject"] = "Ebook"
    msg["From"] = "<" + config.from_mail + ">"
    msg["To"] = config.to_mail

    attachment = email.mime.application.MIMEApplication(_data=data, _subtype="x-mobipocket-ebook")
    attachment.add_header("Content-Disposition", "attachment", filename="book.mobi")
    msg.attach(attachment)

    with smtplib.SMTP_SSL(host=config.smtp_host) as smtp:
        smtp.login(config.from_mail, config.smtp_password)
        smtp.send_message(msg)


@app.route("/", methods=["POST"])
def publish():
    if "X-Api-Token" not in request.headers or request.headers["X-Api-Token"] != config.api_key:
        return "Invalid api token", 403

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as epub:
        epub.write(request.get_data())
    with tempfile.NamedTemporaryFile(suffix=".mobi", delete=False) as mobi:
        pass
    try:
        subprocess.run(("ebook-convert", epub.name, mobi.name), check=True)
        with open(mobi.name, "rb") as f:
            mobi_bytes = f.read()
    finally:
        os.unlink(epub.name)
        os.unlink(mobi.name)
    send_mail(mobi_bytes)
    return ""
