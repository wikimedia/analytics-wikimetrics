from flask import Flask

app = Flask('wikimetrics')
app.config.from_object('config')

import controllers
