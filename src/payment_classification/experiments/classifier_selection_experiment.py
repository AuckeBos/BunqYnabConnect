import mlflow
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from payment_classification.classifier import Classifier
from payment_classification.dataset import Dataset
from payment_classification.experiments.base_experiment import BaseExperiment


class ClassifierSelectionExperiment(BaseExperiment):
    """
    An experiment to train and evaluate a list of classification algorithms

    ATTRIBUTES
    ----------
    CLASSIFIERS: List[clf]
        List of classifiers to train
    """

    # https://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html
    CLASSIFIERS = [
        # KNeighborsClassifier(),
        # SVC(kernel="linear", C=0.025),
        # SVC(gamma=2, C=1),
        DecisionTreeClassifier(max_depth=5),
        DecisionTreeClassifier(max_depth=10),
        # RandomForestClassifier(max_depth=5, n_estimators=10),
        # MLPClassifier(alpha=1, max_iter=1000),
        # AdaBoostClassifier(),
        # GaussianNB(),
    ]

    @BaseExperiment.register_mlflow
    def run(self, dataset: Dataset):
        mlflow.log_text(",".join(dataset.feature_names()), "features.txt")
        X_train, X_test, y_train, y_test = self.split_to_sets(dataset.X, dataset.y)

        for clf in self.CLASSIFIERS:
            try:
                Classifier().train_evaluate(clf, (X_train, X_test, y_train, y_test))
            except Exception as e:
                print(f"An Exception occurred: {e}")
        self.select_best_run()

    def select_best_run(self) -> None:
        runs = mlflow.search_runs(
            filter_string=f"tags.mlflow.parentRunId = '{self.run_id}'"
        )
        # Todo: Select and save best
