import os

import mlflow.pyfunc
from flask import Flask

from helpers.helpers import get_config


class ModelServer:
    """
    WIP:
    https://newbedev.com/using-flask-inside-class
    """

    app: Flask

    def __init__(self):
        self.app = Flask('ModelServer')
        model_url = "models:/Classifier for Budget XXX/Production"
        self.model = mlflow.sklearn.load_model(model_url)
        test = ''


    def serve(self):
        port = "5002"

        cfg = get_config()
        ssl_context = tuple(
            [
                f"{os.path.dirname(os.path.realpath(__file__))}/../../{f}"
                for f in cfg["ssl_context"]
            ]
        )
        self.app.add_url_rule("/predict", "predict", self.predict)
        self.app.run(
            host="localhost",
            port=port,
            ssl_context=ssl_context,
        )

    def predict(self):
        pass