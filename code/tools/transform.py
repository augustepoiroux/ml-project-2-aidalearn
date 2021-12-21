import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class LogTransform:
    def __init__(self, y):
        self.miny = float(np.min(y))
        miny2 = sorted(set(np.array(y.squeeze())))[1]
        self.eps = (miny2 - self.miny) / 10
        self.bias = 0
        self.bias = np.max(self.transform(y)) + 1

    def transform(self, y):
        return np.log(y - self.miny + self.eps) - self.bias

    def inverse_transform(self, logy):
        return np.exp(logy + self.bias) + self.miny - self.eps


class CustomLogTargetTransformer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.log_transformer = None

    def fit(self, target):
        self.log_transformer = LogTransform(target)
        return self

    def transform(self, target):
        return self.log_transformer.transform(target)

    def inverse_transform(self, log_target):
        return self.log_transformer.inverse_transform(log_target)


def magnitude(x: float) -> int:
    return -int(np.floor(np.log10(x)))


def magnitude_inv(x: int) -> float:
    return 10 ** float(-x)


def magnitude_transform(a: np.array) -> np.array:
    return np.vectorize(magnitude)(a)


def magnitude_inv_transform(a: np.array) -> np.array:
    return np.vectorize(magnitude_inv)(a)


class TargetMagnitudeTransformer(BaseEstimator, TransformerMixin):
    def fit(self, target):
        return self

    def transform(self, target):
        if isinstance(target, pd.Series):
            return target.apply(magnitude)
        else:
            return magnitude_transform(target)

    def inverse_transform(self, target):
        if isinstance(target, pd.Series):
            return target.apply(magnitude_inv)
        else:
            return magnitude_inv_transform(target)
