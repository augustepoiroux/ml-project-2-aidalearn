import os
import pickle
import sys
from pathlib import Path

import numpy as np
import xgboost as xgb
from rich.console import Console
from rich.table import Table
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

sys.path.append(str(Path(__file__).parent.parent.absolute()))
from tools.data_loader import data_loader
from tools.utils import Encoding, Target, custom_mape

# Set Up
DATA_DIR = os.path.join(
    str(Path(__file__).parent.parent.parent.absolute()), "data/"
)

DATA_PATH = os.path.join(DATA_DIR, "data.csv")

MODELS_DIR = os.path.join(
    str(Path(__file__).parent.parent.parent.absolute()), "models/log_delta_E/"
)

encoding = Encoding.COLUMN_MASS
target = Target.LOG_DELTA_E
console = Console(record=True)

# Data Loading
X_train, X_test, logy_train, logy_test = data_loader(
    target=target,
    encoding=encoding,
    data_path=DATA_PATH,
    test_size=0.2,
    generalization=False,
)

# Model Definitions
linear_log_augmented_model = Pipeline(
    [
        ("scaler_init", StandardScaler()),
        ("features", PolynomialFeatures(degree=2)),
        ("scaler_final", StandardScaler()),
        ("regressor", LinearRegression()),
    ]
)

rf_log_model = RandomForestRegressor(random_state=0)

xgb_log_model = xgb.XGBRegressor(
    max_depth=7, n_estimators=400, learning_rate=1.0, random_state=0
)

# detect if gpu is usable with xgboost by training on toy data
try:
    xgb_log_model.set_params(tree_method="gpu_hist")
    xgb_log_model.fit(np.array([[1, 2, 3]]), np.array([[1]]))
    console.print("[italic bright_black]Using GPU for XGBoost")
except:
    xgb_log_model.set_params(tree_method="hist")
    console.print("[italic bright_black]Using CPU for XGBoost")

models_log = {
    "Dummy - log": DummyRegressor(),
    "Linear - log": LinearRegression(),
    "Augmented Linear - log": linear_log_augmented_model,
    "Random Forest - log": rf_log_model,
    "XGBoost - log": xgb_log_model,
}

# Model training
with console.status("") as status:
    for model_name, model in models_log.items():
        status.update(f"[bold blue]Training {model_name}...")
        model.fit(X_train, logy_train)
        console.log(f"[blue]Finished training {model_name}[/blue]")

# Model evaluation
with console.status("") as status:
    for model_name, model in models_log.items():
        status.update(f"[bold blue]Evaluating {model_name}...")

        table = Table(title=model_name)
        table.add_column("Loss name", justify="center", style="cyan")
        table.add_column("Train", justify="center", style="green")
        table.add_column("Test", justify="center", style="green")

        # first we evaluate the log-transformed prediction
        logy_pred_train = model.predict(X_train)
        logy_pred_test = model.predict(X_test)

        for loss_name, loss_fn in [
            ("MSE - log", mean_squared_error),
            ("MAE - log", mean_absolute_error),
            ("MAPE - log", mean_absolute_percentage_error),
            ("Custom MAPE - log", custom_mape),
        ]:
            train_loss = loss_fn(logy_train, logy_pred_train)
            test_loss = loss_fn(logy_test, logy_pred_test)
            table.add_row(loss_name, f"{train_loss:.4E}", f"{test_loss:.4E}")

        # then we transform the predictions back and evaluate
        y_pred_train = log_transform.inverse_transform(
            logy_pred_train.squeeze()
        )
        y_pred_test = log_transform.inverse_transform(logy_pred_test.squeeze())

        y_train = log_transform.inverse_transform(logy_train.squeeze())
        y_test = log_transform.inverse_transform(logy_test.squeeze())

        for loss_name, loss_fn in [
            ("MSE", mean_squared_error),
            ("MAE", mean_absolute_error),
            ("MAPE", mean_absolute_percentage_error),
            ("Custom MAPE", lambda a, b: custom_mape(a, b, True)),
        ]:
            train_loss = loss_fn(y_train, y_pred_train)
            test_loss = loss_fn(y_test, y_pred_test)
            table.add_row(loss_name, f"{train_loss:.4E}", f"{test_loss:.4E}")

        console.print(table)

# print some samples
n_sample = 10

table = Table(title="Test samples")
table.add_column("Real", justify="center", style="green")
for model_name, _ in models_log.items():
    table.add_column(model_name, justify="center", style="yellow")

idx_sample = np.random.choice(X_test.index, size=n_sample, replace=False)
results = [np.array(y_test[y_test.index.intersection(idx_sample)].squeeze())]
for model_name, model in models_log.items():
    results.append(
        log_transform.inverse_transform(
            np.array(
                model.predict(
                    X_test.loc[X_test.index.intersection(idx_sample)]
                ).squeeze()
            )
        )
    )

for i in range(n_sample):
    table.add_row(*[f"{r[i]:.3E}" for r in results],)
console.print(table)

# save results
if input("Save models? (y/[n]) ") == "y":
    save_models = {
        "Random Forest - log": (rf_log_model, "random_forest_model.pkl"),
        # "Gradient Boosting - log": (gb_log_model, "gb_model.pkl"),
        "XGBoost - log": (xgb_log_model, "xgb_model.pkl"),
    }

    Path(MODELS_DIR).mkdir(parents=True, exist_ok=True)
    results_file = os.path.join(MODELS_DIR, "results.html")
    console.save_html(results_file)
    console.print(f"Results stored in {results_file}")
    with console.status("[bold green]Saving models...") as status:
        for model_name, (model, filename) in save_models.items():
            modelpath = MODELS_DIR + filename
            with open(modelpath, "wb") as file:
                pickle.dump(model, file)
            console.log(f"[green]Saved {model_name} to {modelpath}[/green]")
