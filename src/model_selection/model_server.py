import json
import os

import mlflow.pyfunc
from flask import Flask
from sklearn.base import ClassifierMixin

from helpers.helpers import (
    get_config,
    MODEL_PORT_FILE,
    get_model_port,
    get_mlflow_model_name,
    log,
)
from model_selection.dataset import Dataset


class ModelServer:
    """
    WIP:
    https://newbedev.com/using-flask-inside-class

    ATTRIBUTES
    ----------
    app: Flask
        The flask app
    dataset: Dataset
        The dataset for the model
    """

    app: Flask
    dataset: Dataset
    model: ClassifierMixin

    def __init__(self, dataset: Dataset):
        self.app = Flask("ModelServer")
        self.dataset = dataset
        model_url = f"models:/{get_mlflow_model_name(dataset)}/Production"
        self.model = mlflow.sklearn.load_model(model_url)

    def serve(self):
        port = self.port
        if port is None:
            raise Exception(
                f"Cannot serve budget {self.dataset.budget.id}, "
                f"please set the port to serve on first"
            )
        budget = self.dataset.budget
        self.app.add_url_rule("/predict", "predict", self.predict)
        endpoint = f"http://localhost:{port}"
        log_msg = f"ENDPOINT FOR BUDGET {budget.id}: {endpoint}"
        log(log_msg, False, True)
        self.app.run(host="localhost", port=port)

    @property
    def port(self) -> int:
        return get_model_port(self.dataset)

    @port.setter
    def port(self, port: int):
        """
        Save the port on which this model is served, to file system
        """

        with open(MODEL_PORT_FILE, "r") as file:
            ports = json.load(file)

        with open(MODEL_PORT_FILE, "w") as file:
            ports[self.dataset.budget.id] = port
            json.dump(ports, file)

    def predict(self, *args):
        log(str(args))
