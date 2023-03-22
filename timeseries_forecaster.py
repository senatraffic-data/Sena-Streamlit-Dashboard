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
        self.yEndogenous: pd.DataFrame
        self.yTrain: pd.DataFrame
        self.yTest: pd.DataFrame
        self.yPred: pd.DataFrame
        
    def trainTestSplitData(self):
        pass
        
    def generateTimeSeriesAnalytics(self, selectedDestinations, hoursToForecast):
        self.volumeSpeedLOS.generateHourlyLOS(selectedDestinations)

        self.yEndogenous = self.volumeSpeedLOS.dfHourlyLOS.loc[: , ['IN']]
        self.yEndogenous.index.name = ""
        self.yEndogenous.columns = ['Latest Observed Data']

        self.yTrain, self.yTest = temporal_train_test_split(self.yEndogenous, test_size=0.3)

        self.yTrain.index.name = ""
        self.yTrain.columns = ['Training Data']
        self.yTest.index.name = ""
        self.yTest.columns = ['Test Data']

        yPred, predictionInterval, yCombined, forecaster = self.getPredictions(self.yTrain, self.yTest)

        lastObservedDatetime = self.yEndogenous.index[-1]
        offsetDatetime = lastObservedDatetime + timedelta(hours=1) 
        dateRange = pd.date_range(
            start=offsetDatetime, 
            periods=hoursToForecast, 
            freq='H'
        )

        yForecast, predictionIntervalForecast, yCombinedForecast = self.getForecasts(
            forecaster, 
            self.yEndogenous, 
            dateRange
        )

        yList = [
            self.yTrain, self.yTest,
            yPred, predictionInterval, yCombined,
            yForecast, predictionIntervalForecast, yCombinedForecast,
            self.yEndogenous
        ]

        metrics = self.getMetrics(self.yTest, self.yPred)
        
        return yList, metrics, forecaster
        
    def displayTimeseriesTesting(self, forecaster, metrics, yList):
        st.header('Time-Series Model Testing')

        st.write(forecaster.summary())
        st.write(f'The testing MAPE is {metrics[0]}')
        st.write(f'The testing MSE is {metrics[1]}')
        st.write(yList[2])

        figForecast, axForecast = plt.subplots(1, 1)
        yList[0].plot(
            kind='line', 
            ax=axForecast,
            title=r'Hourly LOS% For Train, Testing, and Prediction',
            ylabel='LOS %'
        )
        yList[1].plot(kind='line', ax=axForecast)
        yList[2].plot(kind='line', ax=axForecast)
        plt.fill_between(
            yList[3].index,
            yList[3].loc[: , ('Coverage', 0.9, 'lower')],
            yList[3].loc[: , ('Coverage', 0.9, 'upper')],
            alpha=0.25
        )
        axForecast.legend()
        plt.tight_layout()
        st.pyplot(figForecast)
            
        plotlyFigHourlyLOSTrainTest = px.line(
            yList[4],
            template="plotly_dark",
            title=r'Hourly LOS% For Train, Testing, and Prediction'
        )
        plotlyFigHourlyLOSTrainTest.update_layout(yaxis_title='LOS%')
        st.plotly_chart(
            plotlyFigHourlyLOSTrainTest,
            use_container_width=True,
            sharing="streamlit",
            theme=None
        )
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write('Testing Data')
            st.write(yList[1])
            
        with col2:
            st.write('Predictions')
            st.write(yList[2])
            
        with col3:
            st.write('Confidence Interval')
            st.write(yList[3])

    def displayTimeseriesForecasting(self, yList):
        st.header('Forecasting')

        figForecastAlt, axForecastAlt = plt.subplots(1, 1)
        yList[-1].plot(
            kind='line',
            ax=axForecastAlt,
            title=r'Hourly LOS% For Observed Data & Forecast',
            ylabel='LOS %'
        )
        yList[5].plot(kind='line', ax=axForecastAlt)
        plt.fill_between(
            yList[6].index,
            yList[6].loc[: , ('Coverage', 0.9, 'lower')],
            yList[6].loc[: , ('Coverage', 0.9, 'upper')],
            alpha=0.25
        )
        axForecastAlt.legend()
        plt.tight_layout()
        st.pyplot(figForecastAlt)
        
        plotlyFigHourlyLOSForecast = px.line(
            yList[7], 
            template="plotly_dark",
            title=r'Hourly LOS% For Observed Data & Forecast'
        )
        plotlyFigHourlyLOSForecast.update_layout(yaxis_title='LOS%')
        st.plotly_chart(
            plotlyFigHourlyLOSForecast,
            use_container_width=True,
            sharing="streamlit",
            theme=None
        )
        
        col1Alt, col2Alt, col3Alt = st.columns(3)
        
        with col1Alt:
            st.write('All Observed Data')
            st.write(yList[-1])
            
        with col2Alt:
            st.write('Forecasted Values')
            st.write(yList[5])
            
        with col3Alt:
            st.write('Confidence Interval')
            st.write(yList[6])
            
    def getMetrics(self, yTest, yPred):
        mape = mean_absolute_percentage_error(
            yTest,
            yPred,
            symmetric=False
        )
        
        mse = mean_squared_error(
            yTest,
            yPred,
            squared=False
        )

        return [mape, mse]

    def getPredictions(self, yTrain, yTest):
        fh = ForecastingHorizon(yTest.index, is_relative=False)

        forecaster = AutoARIMA()
        forecaster.fit(yTrain)

        yPred = forecaster.predict(fh=fh)
        yPred.index.name = ""
        yPred.columns = ['Prediction']

        predictionInterval = forecaster.predict_interval(fh=fh)

        yCombined = pd.concat([yTrain, yTest, yPred], axis=1)

        return yPred, predictionInterval, yCombined, forecaster

    def getForecasts(self, forecaster, yEndogenous, dateRange):
        fh1 = ForecastingHorizon(dateRange, is_relative=False)

        yForecast = forecaster.predict(fh=fh1)
        yForecast.index.name = ''
        yForecast.columns = ['Forecast']

        predictionIntevalForecast = forecaster.predict_interval(fh=fh1)

        yCombinedForecast = pd.concat([yEndogenous, yForecast], axis=1)

        return yForecast, predictionIntevalForecast, yCombinedForecast