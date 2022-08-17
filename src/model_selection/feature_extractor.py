from typing import List

import numpy as np
import pandas as pd
from bunq.sdk.model.generated.endpoint import Payment
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


class FeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Class responsible for extracting features of raw Bunq Payments

    ATTRIBUTES
    ----------
    description_encoder: CountVectorizer
        The encoder that encodes bunq-transaction 'Descriptions' into vectors, using BOW
    """

    description_encoder: CountVectorizer
    COLUMNS = [
        "amount",
        "hour",
        "minute",
        "weekday",
    ]

    def fit(self, X: List[Payment], y=None) -> "FeatureExtractor":

        # Fit TFIDF encoder
        descriptions = [t.description for t in X]
        description_encoder = TfidfVectorizer(lowercase=False)
        description_encoder.fit(descriptions)
        self.description_encoder = description_encoder
        return self

    def transform(self, X: List[Payment], y=None) -> pd.DataFrame:
        # Load all data
        data = np.array(
            [
                [
                    t.description,
                    float(t.amount.value),
                    int(t.datetime.hour),
                    int(t.datetime.minute),
                    int(t.datetime.weekday()),
                ]
                for t in X
            ],
            dtype="object",
        )
        # Convert descriptions into bag of words
        descriptions = data[:, 0]
        bag_of_words = np.array(
            self.description_encoder.transform(descriptions).toarray()
        )
        # Merge into one array, and convert to frame
        data = np.concatenate((data, bag_of_words), axis=1)
        return pd.DataFrame(
            data[:, 1:],
            columns=[
                *self.COLUMNS,
                *[
                    f"word_{w}"
                    for w in self.description_encoder.get_feature_names_out()
                ],
            ],
        )

    def feature_names(self) -> List[str]:
        """
        Get the names of all features that are used
        """
        return [
            f"description ({self.description_encoder.__class__.__name__})",
            *self.COLUMNS,
        ]
