from flask import Flask
from flask_login import LoginManager

app = Flask('wikimetrics')
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)

import controllers
