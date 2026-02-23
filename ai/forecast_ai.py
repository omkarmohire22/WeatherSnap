import numpy as np
from sklearn.linear_model import LinearRegression

def train_temperature_model(historical_dates, historical_temps):
    """
    Train a simple linear regression model on historical temperature data.
    Args:
        historical_dates (list): List of date indices (e.g., [0, 1, 2, ...])
        historical_temps (list): List of temperatures corresponding to the dates
    Returns:
        model: Trained LinearRegression model
    """
    X = np.array(historical_dates).reshape(-1, 1)
    y = np.array(historical_temps)
    model = LinearRegression()
    model.fit(X, y)
    return model

def predict_future_temps(model, future_dates):
    """
    Predict future temperatures using the trained model.
    Args:
        model: Trained LinearRegression model
        future_dates (list): List of future date indices to predict
    Returns:
        list: Predicted temperatures
    """
    X_future = np.array(future_dates).reshape(-1, 1)
    return model.predict(X_future).tolist()

# Example usage (for integration):
# historical_dates = [0, 1, 2, 3, 4, 5, 6]  # e.g., days
# historical_temps = [28, 29, 30, 31, 29, 28, 27]
# model = train_temperature_model(historical_dates, historical_temps)
# future_dates = [7, 8, 9]
# predictions = predict_future_temps(model, future_dates)