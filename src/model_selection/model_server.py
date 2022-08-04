import json
import os
import pickle
from typing import Dict

import mlflow.pyfunc
from bunq.sdk.model.generated.endpoint import Payment
from flask import Flask, request
from mlflow.tracking import MlflowClient
from sklearn.base import ClassifierMixin
from sklearn.preprocessing import LabelEncoder

from bunq_ynab_connector._bunq.bunq_account import BunqAccount
from helpers.helpers import (
    get_config,
    MODEL_PORT_FILE,
    get_model_port,
    get_mlflow_model_name,
    log,
    get_bunq_connector,
)
from model_selection.dataset import Dataset
from model_selection.feature_extractor import FeatureExtractor


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
    model: ClassifierMixin
        The deployed model
    category_encoder: LabelEncoder
        The category encoder belonging to the model
    feature_extractor: FeatureExtractor
        The feature extractor belonging to the model

    """

    app: Flask
    dataset: Dataset
    model: ClassifierMixin
    category_encoder: LabelEncoder
    feature_extractor: FeatureExtractor

    def __init__(self, dataset: Dataset):
        self.app = Flask("ModelServer")
        self.dataset = dataset
        self.load_model()

    def load_model(self):
        """
        Load the mlflow model that was deployed for this dataset. Then:
        - Load the run of the model
        - Load the category encoder and feature extractor, save as attributes of self
        - Load the actual sklearn model, ste as attribute of self
        """
        name = get_mlflow_model_name(self.dataset)
        client = MlflowClient()
        run_id = client.get_registered_model(name).latest_versions[0].run_id
        # For these two artifacts
        for art_name in ["category_encoder", "feature_extractor"]:
            # Download the artifact to local. Will return the dir of the artifact
            dir = client.download_artifacts(run_id, art_name)
            # Was saved under this name
            path = f"{dir}/artifact.pickle"
            # Open it, load it, save it
            with open(path, "rb") as f:
                try:
                    art = pickle.load(f)
                    setattr(self, art_name, art)
                except:
                    continue
        model_url = f"models:/{name}/Production"
        self.model = mlflow.sklearn.load_model(model_url)

    def serve(self):
        port = self.port
        if port is None:
            raise Exception(
                f"Cannot serve budget {self.dataset.budget.id}, "
                f"please set the port to serve on first"
            )
        budget = self.dataset.budget
        self.app.add_url_rule("/predict", "predict", self.predict, methods=["POST"])
        endpoint = f"http://localhost:{port}"
        log_msg = f"ENDPOINT FOR BUDGET {budget.id}: {endpoint}"
        log(log_msg, False, True)
        self.app.run(host="localhost", port=port)

    @property
    def port(self) -> int:
        return get_model_port(self.dataset.budget.id)

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

    def predict(self) -> str:
        """
        Predict the category of a payment:
        - Create a Payment object from the payment dict. Try to do this by parsing the
        json. If this fails, load it by calling the api.
        - Update the payment, by adding the datetime. Otherwise the transformer can
        transform it
        - Predict the code of the category
        - Convert the catgory code to string, using the label encoder
        Parameters
        ----------
        The request data should be a dict representation of a payment

        """
        payment_data = json.loads(request.data.decode())

        try:
            payment = Payment.from_json(json.dumps(payment_data))
            log(f"Payment {payment.id_} loaded from json")
        except:
            payment_id, monetary_account_id = (
                payment_data["id"],
                payment_data["monetary_account_id"],
            )
            payment = get_bunq_connector().get_payment(payment_id, monetary_account_id)
            log(f"Could not load payment {payment_id} by json, loaded it by api call")

        payment = BunqAccount.update_transaction(payment)
        data = [payment]
        features = self.feature_extractor.transform(data)
        prediction_code = self.model.predict(features)
        prediction_label = self.category_encoder.inverse_transform(prediction_code)[0]
        return prediction_label
