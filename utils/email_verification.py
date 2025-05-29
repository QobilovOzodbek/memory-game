from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_verification_code(email, code):
    try:
        msg = Message("Verification Code", sender=current_app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your verification code is: {code}"
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
