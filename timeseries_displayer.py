from matplotlib import pyplot as plt

import streamlit as st

import plotly.express as px

from timeseries_forecaster import TimeSeriesForecaster


class TimeSeriesDisplayer:
    def __init__(self, timeSeriesForecaster: TimeSeriesForecaster) -> None:
        self.timeSeriesForecaster = timeSeriesForecaster
    
    def displayTimeseriesTesting(self):
        st.header('Time-Series Model Testing')
        
        st.write(self.timeSeriesForecaster.forecaster.summary())
        st.write(f'The testing MAPE is {self.timeSeriesForecaster.mape}')
        st.write(f'The testing MSE is {self.timeSeriesForecaster.mse}')
        st.write(self.timeSeriesForecaster.yPred)
        
        figForecast, axForecast = plt.subplots(1, 1)
        self.timeSeriesForecaster.yTrain.plot(
            kind='line', 
            ax=axForecast,
            title=r'Hourly LOS% For Train, Testing, and Prediction',
            ylabel='LOS %'
        )
        self.timeSeriesForecaster.yTest.plot(kind='line', ax=axForecast)
        self.timeSeriesForecaster.yPred.plot(kind='line', ax=axForecast)
        plt.fill_between(
            self.timeSeriesForecaster.predictionInterval.index,
            self.timeSeriesForecaster.predictionInterval.loc[: , ('Coverage', 0.9, 'lower')],
            self.timeSeriesForecaster.predictionInterval.loc[: , ('Coverage', 0.9, 'upper')],
            alpha=0.25
        )
        axForecast.legend()
        plt.tight_layout()
        st.pyplot(figForecast)
        
        plotlyFigHourlyLOSTrainTest = px.line(
            self.timeSeriesForecaster.yCombined,
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
            st.write(self.timeSeriesForecaster.yTest)
            
        with col2:
            st.write('Predictions')
            st.write(self.timeSeriesForecaster.yPred)
            
        with col3:
            st.write('Confidence Interval')
            st.write(self.timeSeriesForecaster.predictionInterval)

    def displayTimeseriesForecasting(self):
        st.header('Forecasting')
        
        figForecastAlt, axForecastAlt = plt.subplots(1, 1)
        self.timeSeriesForecaster.yEndogenous.plot(
            kind='line',
            ax=axForecastAlt,
            title=r'Hourly LOS% For Observed Data & Forecast',
            ylabel='LOS %'
        )
        self.timeSeriesForecaster.yForecast.plot(kind='line', ax=axForecastAlt)
        plt.fill_between(
            self.timeSeriesForecaster.predictionIntevalForecast.index,
            self.timeSeriesForecaster.predictionIntevalForecast.loc[: , ('Coverage', 0.9, 'lower')],
            self.timeSeriesForecaster.predictionIntevalForecast.loc[: , ('Coverage', 0.9, 'upper')],
            alpha=0.25
        )
        axForecastAlt.legend()
        plt.tight_layout()
        st.pyplot(figForecastAlt)
        
        plotlyFigHourlyLOSForecast = px.line(
            self.timeSeriesForecaster.yCombinedForecast, 
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
            st.write(self.timeSeriesForecaster.yEndogenous)
            
        with col2Alt:
            st.write('Forecasted Values')
            st.write(self.timeSeriesForecaster.yForecast)
            
        with col3Alt:
            st.write('Confidence Interval')
            st.write(self.timeSeriesForecaster.predictionIntevalForecast)