from flask import Flask
from flask_mail import Mail


app = Flask(__name__)
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "yousseffrikel7@gmail.com"
app.config['MAIL_PASSWORD'] = "hvje udzp eabq pchf"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

