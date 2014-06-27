import features as f
import numpy as np
from sklearn import pipeline
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
from estimator_base import *

rfr_params_cc = {
    'n_estimators': 30,
    'max_features': "auto",
    'bootstrap': True,
    'verbose': 0,
    'min_density': 0.01,
    'n_jobs': 1,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'random_state': 1
    }

rfr_params_cn = {
    'n_estimators': 60,
    'max_features': "auto",
    'bootstrap': True,
    'verbose': 0,
    'min_density': 0.01,
    'n_jobs': 1,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'random_state': 1
    }

rfr_params_nn = {
    'n_estimators': 120,
    'max_features': "auto",
    'bootstrap': True,
    'verbose': 0,
    'min_density': 0.01,
    'n_jobs': 1,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'random_state': 1
    }

rfr_params_nn2 = {
    'n_estimators': 200,
    'max_features': "auto",
    'bootstrap': True,
    'verbose': 0,
    'min_density': 0.01,
    'n_jobs': 1,
    'min_samples_split': 10,
    'min_samples_leaf': 1,
    'random_state': 1
}

rfr_params_bb = {
    'n_estimators': 10,
    'max_features': "auto",
    'bootstrap': True,
    'verbose': 0,
    'min_density': 0.01,
    'n_jobs': 1,
    'min_samples_split': 8,
    'min_samples_leaf': 2,
    'random_state': 1
    }

gbc_params_cc = {
    'loss':'deviance',
    'learning_rate': 0.1,
    'n_estimators': 400,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 6,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
    }

gbc_params_cn = {
    'loss':'deviance',
    'learning_rate': 0.1,
    'n_estimators': 390,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 7,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
    }

gbc_params_nn = {
    'loss':'deviance',
    'learning_rate': 0.1,
    'n_estimators': 390,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 9,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
    }

gbc_params_union = {
    'loss':'deviance',
    'learning_rate': 0.1,
    'n_estimators': 390,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 8,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
    }

gbc_params_union2 = {
    'loss':'deviance',
    'learning_rate': 0.12,
    'n_estimators': 450,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 8,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
}

gbr_params_union = {
    'loss':'ls',
    'learning_rate': 0.08,
    'n_estimators': 450,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 8,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
}

class Pipeline(pipeline.Pipeline):
    def predict(self, X):
        try:
            p = pipeline.Pipeline.predict_proba(self, X)
            if p.shape[1] == 2:
                p = p[:,1]
            elif p.shape[1] == 3:
                p = p[:,2] - p[:,0]
        except AttributeError:
            p = pipeline.Pipeline.predict(self, X)
        return p


def get_pipeline(features, regressor=None, params=None):
    steps = [
        ("extract_features", f.FeatureMapper(features)),
        ("regressor", regressor(**params)),
        ]
    return Pipeline(steps)

class CauseEffectEstimatorOneStep(BaseEstimator):
    def __init__(self, features=None, regressor=None, params=None, symmetrize=True):
        self.extractor = f.extract_features
        self.classifier = get_pipeline(features, regressor, params)
        self.symmetrize = symmetrize

    def extract(self, features):
        return self.extractor(features)

    def fit(self, X, y=None):
        self.classifier.fit(X, y)
        return self

    def fit_transform(self, X, y=None):
        return self.classifier.fit_transform(X, y)

    def transform(self, X):
        return self.classifier.transform(X)

    def predict(self, X):
        predictions = self.classifier.predict(X)
        #print self.classifier
        #print predictions
        if self.symmetrize:
            predictions[0::2] = (predictions[0::2] - predictions[1::2])*0.5
            predictions[1::2] = -predictions[0::2]
        return predictions

class CauseEffectEstimatorSymmetric(BaseEstimator):
    def __init__(self, features=None, regressor=None, params=None, symmetrize=True):
        self.extractor = f.extract_features
        self.classifier_left = get_pipeline(features, regressor, params)
        self.classifier_right = get_pipeline(features, regressor, params)
        self.symmetrize = symmetrize

    def extract(self, features):
        return self.extractor(features)

    def fit(self, X, y=None):
        target_left = np.array(y)
        target_left[target_left != 1] = 0
        weight_left = np.ones(len(target_left))
        weight_left[target_left==0] = sum(target_left==1)/float(sum(target_left==0))
        try:
            self.classifier_left.fit(X, target_left, regressor__sample_weight=weight_left)
        except TypeError:
            self.classifier_left.fit(X, target_left)
        target_right = np.array(y)
        target_right[target_right != -1] = 0
        target_right[target_right == -1] = 1
        weight_right = np.ones(len(target_right))
        weight_right[target_right==0] = sum(target_right==1)/float(sum(target_right==0))
        try:
            self.classifier_right.fit(X, target_right, regressor__sample_weight=weight_right)
        except TypeError:
            self.classifier_right.fit(X, target_right)

        return self

    def fit_transform(self, X, y=None):
        target_left = np.array(y)
        target_left[target_left != 1] = 0
        X_left = self.classifier_left.fit_transform(X, target_left)
        target_right = np.array(y)
        target_right[target_right != -1] = 0
        target_right[target_right == -1] = 1
        X_right = self.classifier_right.fit_transform(X, target_right)
        return X_left, X_right

    def transform(self, X):
        return self.classifier_left.transform(X), self.classifier_right.transform(X)

    def predict(self, X):
        predictions_left = self.classifier_left.predict(X)
        predictions_right = self.classifier_right.predict(X)
        #print self.classifier_left
        #print predictions_left
        predictions = predictions_left - predictions_right
        if self.symmetrize:
            predictions[0::2] = (predictions[0::2] - predictions[1::2])*0.5
            predictions[1::2] = -predictions[0::2]
        return predictions

class CauseEffectEstimatorID(BaseEstimator):
    def __init__(self, features_independence=None, features_direction=None, regressor=None, params=None, symmetrize=True):
        self.extractor = f.extract_features
        self.classifier_independence = get_pipeline(features_independence, regressor, params)
        self.classifier_direction = get_pipeline(features_direction, regressor, params)
        self.symmetrize = symmetrize
        #self.normalize = normalize

    def extract(self, features):
        return self.extractor(features)

    def fit(self, X, y=None):
        #independence training pairs
        train_independence = X
        target_independence = np.array(y)
        target_independence[target_independence != 0] = 1
        weight_independence = np.ones(len(target_independence))
        weight_independence[target_independence==0] = sum(target_independence==1)/float(sum(target_independence==0))
        try:
            self.classifier_independence.fit(train_independence, target_independence, regressor__sample_weight=weight_independence)
        except TypeError:
            self.classifier_independence.fit(train_independence, target_independence)
        #direction training pairs
        direction_filter = y != 0
        train_direction = X[direction_filter]
        target_direction = y[direction_filter]
        weight_direction = np.ones(len(target_direction))
        weight_direction[target_direction==0] = sum(target_direction==1)/float(sum(target_direction==0))
        try:
            self.classifier_direction.fit(train_direction, target_direction, regressor__sample_weight=weight_direction)
        except TypeError:
            self.classifier_direction.fit(train_direction, target_direction)
        return self

    def fit_transform(self, X, y=None):
        #independence training pairs
        train_independence = X
        target_independence = np.array(y)
        target_independence[target_independence != 0] = 1
        X_ind = self.classifier_independence.fit_transform(train_independence, target_independence)
        #direction training pairs
        direction_filter = y != 0
        train_direction = X[direction_filter]
        target_direction = y[direction_filter]
        self.classifier_direction.fit(train_direction, target_direction)
        X_dir = self.classifier_direction.transform(X)
        return X_ind, X_dir

    def transform(self, X):
        X_ind = self.classifier_independence.transform(X)
        X_dir = self.classifier_direction.transform(X)
        return X_ind, X_dir

    def predict(self, X):
        predictions_independence = self.classifier_independence.predict(X)
        if self.symmetrize:
            predictions_independence[0::2] = (predictions_independence[0::2] + predictions_independence[1::2])*0.5
            predictions_independence[1::2] = predictions_independence[0::2]
        assert predictions_independence.min() >= 0
        predictions_direction = self.classifier_direction.predict(X)
        if self.symmetrize:
            predictions_direction[0::2] = (predictions_direction[0::2] - predictions_direction[1::2])*0.5
            predictions_direction[1::2] = -predictions_direction[0::2]
        predictions = predictions_independence * predictions_direction
        return predictions

def train_model((m, X, y)):
    m.fit(X, y)
    return m

class CauseEffectSystemCombination(BaseEstimator):
    def extract(self, features):
        return self.extractor(features)

    def fit(self, X, y=None):
        #for m in self.systems:
        #    m.fit(X, y)
        ############### parallel training ##############
        import multiprocessing
        pool = multiprocessing.Pool(5)
        self.systems = pool.map(train_model, [(m, X, y) for m in self.systems])
        return self

    def fit_transform(self, X, y=None):
        return [m.fit_transform(X, y) for m in self.systems]

    def transform(self, X):
        return [m.transform(X) for m in self.systems]

    def predict(self, X):
        a = np.array([m.predict(X) for m in self.systems])
        if self.weights is not None:
            return np.dot(self.weights, a)
        else:
            return a

class CauseEffectSystemCombinationCC(CauseEffectSystemCombination):
    def __init__(self, extractor=f.extract_features, weights=None, symmetrize=True):
        self.extractor = extractor
        self.systems = [
            CauseEffectEstimatorID(
                features_direction=selected_direction_categorical_features,
                features_independence=selected_independence_categorical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cc,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=selected_symmetric_categorical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cc,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=selected_onestep_categorical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cc,
                symmetrize=symmetrize),
        ]
        self.weights = weights

class CauseEffectSystemCombinationCN(CauseEffectSystemCombination):
    def __init__(self, extractor=f.extract_features, weights=None, symmetrize=True):
        self.extractor = extractor
        self.systems = [
            CauseEffectEstimatorID(
                features_direction=selected_direction_cn_features,
                features_independence=selected_independence_cn_features,
                regressor=RandomForestRegressor,
                params=rfr_params_cn,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=selected_symmetric_cn_features,
                regressor=RandomForestRegressor,
                params=rfr_params_cn,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=selected_onestep_cn_features,
                regressor=RandomForestRegressor,
                params=rfr_params_cn,
                symmetrize=symmetrize),
            CauseEffectEstimatorID(
                features_direction=selected_direction_cn_features,
                features_independence=selected_independence_cn_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cn,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=selected_symmetric_cn_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cn,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=selected_onestep_cn_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_cn,
                symmetrize=symmetrize),
        ]
        self.weights = weights

class CauseEffectSystemCombinationNN(CauseEffectSystemCombination):
    def __init__(self, extractor=f.extract_features, weights=None, symmetrize=True):
        self.extractor = extractor
        self.systems = [
            CauseEffectEstimatorID(
                features_direction=selected_direction_numerical_features,
                features_independence=selected_independence_numerical_features,
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=selected_symmetric_numerical_features,
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=selected_onestep_numerical_features,
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorID(
                features_direction=selected_direction_numerical_features,
                features_independence=selected_independence_numerical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=selected_symmetric_numerical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=selected_onestep_numerical_features,
                regressor=GradientBoostingClassifier,
                params=gbc_params_nn,
                symmetrize=symmetrize),
        ]
        self.weights = weights

class CauseEffectSystemCombinationUnion(CauseEffectSystemCombination):
    def __init__(self, extractor=f.extract_features, weights=None, symmetrize=True):
        self.extractor = extractor
        self.systems = [
            CauseEffectEstimatorID(
                features_direction=sorted(list(set(selected_direction_categorical_features + selected_direction_cn_features + selected_direction_numerical_features))),
                features_independence=sorted(list(set(selected_independence_categorical_features + selected_independence_cn_features + selected_independence_numerical_features))),
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=sorted(list(set(selected_symmetric_categorical_features + selected_symmetric_cn_features + selected_symmetric_numerical_features))),
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=sorted(list(set(selected_onestep_categorical_features + selected_onestep_cn_features + selected_onestep_numerical_features))),
                regressor=RandomForestRegressor,
                params=rfr_params_nn,
                symmetrize=symmetrize),
            CauseEffectEstimatorID(
                features_direction=sorted(list(set(selected_direction_categorical_features + selected_direction_cn_features + selected_direction_numerical_features))),
                features_independence=sorted(list(set(selected_independence_categorical_features + selected_independence_cn_features + selected_independence_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params_union,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=sorted(list(set(selected_symmetric_categorical_features + selected_symmetric_cn_features + selected_symmetric_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params_union,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=sorted(list(set(selected_onestep_categorical_features + selected_onestep_cn_features + selected_onestep_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params_union,
                symmetrize=symmetrize),
        ]
        self.weights = weights

gbc_params = {
    'loss':'deviance',
    'learning_rate': 0.1,
    'n_estimators': 500,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 9,
    'init': None,
    'random_state': 1,
    'max_features': None,
    'verbose': 0
}

gbr_params = {
    'loss':'huber',
    'learning_rate': 0.1,
    'n_estimators': 500,
    'subsample': 1.0,
    'min_samples_split': 8,
    'min_samples_leaf': 1,
    'max_depth': 9,
    'init': None,
    'random_state': 1,
    'verbose': 0
}

class CauseEffectSystemCombinationUnion2(CauseEffectSystemCombination):
    def __init__(self, extractor=f.extract_features, weights=None, symmetrize=True):
        self.extractor = extractor
        self.systems = [
            CauseEffectEstimatorSymmetric(
                features=['A type', 'B type'] + sorted(list(set(selected_symmetric_categorical_features + selected_symmetric_cn_features + selected_symmetric_numerical_features))),
                regressor=GradientBoostingRegressor,
                params=gbr_params,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=['A type', 'B type'] + sorted(list(set(selected_onestep_categorical_features + selected_onestep_cn_features + selected_onestep_numerical_features))),
                regressor=GradientBoostingRegressor,
                params=gbr_params,
                symmetrize=symmetrize),
            CauseEffectEstimatorID(
                features_direction=['A type', 'B type'] + sorted(list(set(selected_direction_categorical_features + selected_direction_cn_features + selected_direction_numerical_features))),
                features_independence=['A type', 'B type'] + sorted(list(set(selected_independence_categorical_features + selected_independence_cn_features + selected_independence_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params,
                symmetrize=symmetrize),
            CauseEffectEstimatorSymmetric(
                features=['A type', 'B type'] + sorted(list(set(selected_symmetric_categorical_features + selected_symmetric_cn_features + selected_symmetric_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params,
                symmetrize=symmetrize),
            CauseEffectEstimatorOneStep(
                features=['A type', 'B type'] + sorted(list(set(selected_onestep_categorical_features + selected_onestep_cn_features + selected_onestep_numerical_features))),
                regressor=GradientBoostingClassifier,
                params=gbc_params,
                symmetrize=symmetrize),
            ]
        print len(self.systems)
        self.weights = weights
