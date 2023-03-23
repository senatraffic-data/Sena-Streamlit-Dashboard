from datetime import timedelta
from matplotlib import pyplot as plt
import pandas as pd

from sktime.forecasting.arima import AutoARIMA

from sktime.forecasting.base import ForecastingHorizon

from sklearn.metrics import mean_squared_error

from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

import streamlit as st

import plotly.express as px

from sktime.forecasting.model_selection import temporal_train_test_split

from volume_speed_los import VolumeSpeedLOS


class TimeSeriesForecaster:
    def __init__(self, volumeSpeedLOS: VolumeSpeedLOS) -> None:
        self.volumeSpeedLOS = volumeSpeedLOS
        self.yEndogenous: pd.DataFrame = None
        self.yTrain: pd.DataFrame = None
        self.yTest: pd.DataFrame = None
        self.forecaster = None
        self.yPred: pd.DataFrame = None
        self.predictionInterval = None
        self.yCombined = None
        self.yForecast = None
        self.predictionIntevalForecast = None
        self.yCombinedForecast = None
        self.mape = None
        self.mse = None
        
    def trainTestSplitData(self, dfHourlyLOS):
        self.yEndogenous = dfHourlyLOS.loc[: , ['IN']]
        self.yEndogenous.index.name = ""
        self.yEndogenous.columns = ['Latest Observed Data']
        self.yTrain, self.yTest = temporal_train_test_split(self.yEndogenous, test_size=0.3)
        self.yTrain.index.name = ""
        self.yTrain.columns = ['Training Data']
        self.yTest.index.name = ""
        self.yTest.columns = ['Test Data']
        
    def fitPredict(self):
        fh = ForecastingHorizon(self.yTest.index, is_relative=False)
        self.forecaster = AutoARIMA()
        self.forecaster.fit(self.yTrain)
        self.yPred = self.forecaster.predict(fh=fh)
        self.yPred.index.name = ""
        self.yPred.columns = ['Prediction']
        self.predictionInterval = self.forecaster.predict_interval(fh=fh)
        self.yCombined = pd.concat([self.yTrain, self.yTest, self.yPred], axis=1)
        
    def getForecasts(self, hoursToForecast):
        lastObservedDatetime = self.yEndogenous.index[-1]
        offsetDatetime = lastObservedDatetime + timedelta(hours=1) 
        dateRange = pd.date_range(
            start=offsetDatetime, 
            periods=hoursToForecast, 
            freq='H'
        )
        fh1 = ForecastingHorizon(dateRange, is_relative=False)
        self.yForecast = self.forecaster.predict(fh=fh1)
        self.yForecast.index.name = ''
        self.yForecast.columns = ['Forecast']
        self.predictionIntevalForecast = self.forecaster.predict_interval(fh=fh1)
        self.yCombinedForecast = pd.concat([self.yEndogenous, self.yForecast], axis=1)
        
    def getMetrics(self):
        self.mape = mean_absolute_percentage_error(
            self.yTest,
            self.yPred,
            symmetric=False
        )
        self.mse = mean_squared_error(
            self.yTest,
            self.yPred,
            squared=False
        )