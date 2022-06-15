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
        # SVC(),
        DecisionTreeClassifier(),
        # RandomForestClassifier(n_estimators=200),
        # MLPClassifier(max_iter=1000, solver='lbfgs'),
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
        runs = runs.sort_values('metrics.cohens_kappa', ascending=False)
        best_run_row = runs.iloc[0]
        best_run_id = best_run_row['run_id']
        self.best_run = mlflow.get_run(best_run_id)
