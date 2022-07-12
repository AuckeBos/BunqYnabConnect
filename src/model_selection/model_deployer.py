from datetime import datetime
from typing import Dict, Any

import mlflow
import numpy as np
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from helpers.helpers import object_to_mlflow, log, get_mlflow_model_name
from model_selection.dataset import Dataset
from model_selection.feature_extractor import FeatureExtractor


from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

class ModelDeployer:
    dataset: Dataset

    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def deploy(self, classifier_class: str, hyperparameters: Dict[str, Any]):
        log(f"Deploying classifier")
        self._fully_train_best_classifier(classifier_class, hyperparameters)
        self._bring_model_into_production()
        log(f"Classifier deployed")

    def _fully_train_best_classifier(
        self, cls_name: str, hyperparameters: dict
    ) -> None:
        """
        After the best classifier and its best params have been selected, create a new
        instance of the classifier with the best params, train it on the full dataset,
        log it to mlflow
        """

        mlflow.set_experiment("Full training")
        mlflow.sklearn.autolog()
        with mlflow.start_run(run_name="experiment"):
            mlflow.set_tag("budget", self.dataset.budget.id)
            classifier = eval(cls_name)(**hyperparameters)

            X, y = np.array(self.dataset.X), np.array(self.dataset.y, int)
            # Create feature extractor and transform X. Log extractor as object
            feature_extractor = FeatureExtractor()
            X = feature_extractor.fit_transform(X, y)
            object_to_mlflow(feature_extractor, "feature_extractor")
            # Log label transformer to mlflow as well
            object_to_mlflow(self.dataset.category_encoder, "category_encoder")
            # Fit and log
            classifier.fit(X, y)

            signature = infer_signature(X, y)

            path = "model"
            model_name = self._get_model_name()
            mlflow.sklearn.log_model(
                classifier,
                artifact_path=path,
                registered_model_name=model_name,
                signature=signature,
            )

    def _bring_model_into_production(self):
        """
        Bringing the model into production means:
        - Call transition_model_version_stage with the version just created. Retrieve
        the version number by getting the latest version
        - Update model description
        """
        client = MlflowClient()
        model_name = self._get_model_name()
        # Get the version of the just logged model
        version = client.get_latest_versions(model_name, stages=["None"])[0].version
        # Transition the just trained model into production
        client.transition_model_version_stage(
            name=model_name, version=version, stage="Production"
        )
        date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        set_size = len(self.dataset.X)
        client.update_model_version(
            name=model_name,
            version=version,
            description=f"This model has been trained on {date}, on {set_size} "
            f"transactions",
        )

    def _get_model_name(self):
        return get_mlflow_model_name(self.dataset)
