from datetime import timedelta

import folium

from matplotlib import pyplot as plt

import numpy as np

import pandas as pd

import streamlit as st

from branca.colormap import LinearColormap

from streamlit_folium import folium_static

import plotly.express as px

from my_functions import getForecasts, getHourlyLOS, getMetrics, getPredictions

from sktime.forecasting.model_selection import temporal_train_test_split


class VolumeSpeedLOS:
    def __init__(self, factVolumeSpeed, dimCamera) -> None:
        self.factVolumeSpeed = factVolumeSpeed
        self.dimCamera = dimCamera
        self.dfHourlyLOS = None
        
    def displayOverallVolumeSpeedMetrics(self):
        st.subheader('Overall Metrics')
        
        st.write('Vehicle Count')
        
        minimumCarCount = int(self.factVolumeSpeed['car_count'].min())
        averageCarCount = int(self.factVolumeSpeed['car_count'].mean())
        maximumCarCount = int(self.factVolumeSpeed['car_count'].max())
        
        carColumn1, carColumn2 , carColumn3 = st.columns(3)
        
        with carColumn1:
            st.metric(label='Minimum Car Count', value=minimumCarCount)
            
        with carColumn2:
            st.metric(label='Average Car Count', value=averageCarCount)
            
        with carColumn3:
            st.metric(label='Maximum Car Count', value=maximumCarCount)
        
        st.write('Lane Speed (km/h)')
        
        descriptions = self.factVolumeSpeed.describe()
        minimumLaneSpeed  = round(descriptions.loc['min', 'lane_speed'], 2)
        averageLaneSpeed = round(descriptions.loc['mean', 'lane_speed'], 2)
        maxLaneSpeed = round(descriptions.loc['max', 'lane_speed'], 2)
        
        minimumLaneSpeedColumn, averageLaneSpeedColumn, maximumLaneSpeedColumn = st.columns(3)
        
        with minimumLaneSpeedColumn:
            st.metric(label='Minimum Lane Speed', value=minimumLaneSpeed)
        
        with averageLaneSpeedColumn:
            st.metric(label='Average Lane Speed', value=averageLaneSpeed)
        
        with maximumLaneSpeedColumn:
            st.metric(label='Maximum Lane Speed', value=maxLaneSpeed)
        
        st.write('LOS (%)')
        
        minimumLOS = round(descriptions.loc['min', 'LOS'], 4)
        averageLOS = round(descriptions.loc['mean', 'LOS'], 4)
        maximumLOS = round(descriptions.loc['max', 'LOS'], 4)
        
        minimumLOSColumn, averageLOSColumn, maximumLOSColumn = st.columns(3)
        
        with minimumLOSColumn:
            st.metric(label='Minimum LOS', value=minimumLOS)
        
        with averageLOSColumn:
            st.metric(label='Average LOS', value=averageLOS)

        with maximumLOSColumn:
            st.metric(label='Maximum LOS', value=maximumLOS)
        
    def displayHeatMap(self):
        st.subheader('Heat Map')
        
        mergedMetricsCamera = self.factVolumeSpeed.merge(
            self.dimCamera, 
            how='left', 
            on='camera_id'
        )
        
        groupbyCameras = mergedMetricsCamera.groupby(
            ['camera_id', 
            'latitude', 
            'longitude']
        ).agg({'LOS': np.mean})
        
        groupbyCamerasIndexResetted = groupbyCameras.reset_index()
        subsetted1 = groupbyCamerasIndexResetted[['camera_id', 'latitude', 'longitude', 'LOS']].dropna()
        subsetted = subsetted1[['latitude', 'longitude', 'LOS']]
        cameraIDs = subsetted1['camera_id'].values
        
        # Define the center of the map
        center = subsetted.values[0, 0: 2]

        # Create a folium map
        baseMap = folium.Map(
            location=center, 
            zoom_start=12, 
            tiles='OpenStreetMap'
        )
        # Add the updated layer to the map
        layer = folium.FeatureGroup(name='Updated Layer')

        # Add coordinates to the layer
        coordinates = np.array(subsetted.values, dtype=np.float64)
        
        # Define a color map
        minimumLOS = np.nanmin(coordinates[: , -1])
        medianLOS = np.nanmedian(coordinates[: , -1])
        maximumLOS = np.nanmax(coordinates[: , -1])
        index = [minimumLOS, medianLOS, maximumLOS]
        indexSorted = sorted(index)
        
        colormap = LinearColormap(
            colors=['green', 'yellow', 'red'], 
            index=indexSorted, 
            vmin=0.0, 
            vmax=150.0
        )
            
        # Add bubbles to the layer with color based on value
        for cameraID, coordinate in zip(cameraIDs, coordinates):
            radius = coordinate[-1] # Use the value as the radius
            folium.CircleMarker(
                location=coordinate[0: 2], 
                radius=radius, 
                color=colormap(coordinate[-1]),
                fill=True, 
                fill_color=colormap(coordinate[-1]),
                tooltip=f'<b>Camera ID: {cameraID} | LOS %: {coordinate[-1]: .2f}</b>'
            ).add_to(layer)

        # Add the layer to the map
        layer.add_to(baseMap)

        # Display the map in Streamlit
        folium_static(baseMap)

    def displayHourlyVehicleCount(self):
        st.header('Hourly Vehicle Count')
        
        dfHourlyCarCount = self.factVolumeSpeed.pivot_table(
            values=['car_count'],
            index=['datetime'],
            columns=['POV']
        )
        
        for columnName in self.factVolumeSpeed.columns[6: -4]:
            self.factVolumeSpeed[columnName] = pd.to_numeric(self.factVolumeSpeed[columnName], errors='coerce')
        
        dfHourlyVehicleCount = self.factVolumeSpeed.groupby(['datetime'])[['bus_count', 'car_count', 'lorry_count', 'truck_count', 'van_count', 'motorbike_count', 'total_count']].sum()

        dfHourlyVehicleCount.index.name = ""
        dfHourlyVehicleCount.columns = ['bus', 'car', 'lorry','truck', 'van', 'motorbike', 'total']
        
        figCarCount, axCarCount = plt.subplots(1, 1)
        dfHourlyVehicleCount.plot(
            kind='line',
            title=r'Hourly Vehicle Count',
            ax=axCarCount,
            ylabel='Count'
        )
        plt.style.use('dark_background')
        st.pyplot(figCarCount)
        
        dfHourlyCarCount.index.name = ""
        dfHourlyCarCount.columns = ['b2t', 't2b']
        
        plotlyFigHourlyCarCount = px.line(
            dfHourlyCarCount, 
            template="plotly_dark", 
            title='Hourly Car Count'
        )
        plotlyFigHourlyCarCount.update_layout(yaxis_title='Car Count')
        st.plotly_chart(
            plotlyFigHourlyCarCount, 
            use_container_width=True,   
            sharing="streamlit", 
            theme=None
        )

    def displayHourlyLOSInboundOutbound(self):
        st.header('Hourly LOS% Plot for Inbound & Outbound')
        
        self.dfHourlyLOS.index.name = ""
        
        figTimePlot, axTimePlot = plt.subplots(1, 1)
        self.dfHourlyLOS.plot(
            kind='line',
            title=r'Hourly LOS% For Inbound & Outbound',
            ax=axTimePlot,
            ylabel='LOS %'
        )
        plt.style.use('dark_background')
        st.pyplot(figTimePlot)
        
        plotlyFigHourlyLOS = px.line(
            self.dfHourlyLOS, 
            template="plotly_dark", 
            title='Hourly LOS'
        )
        plotlyFigHourlyLOS.update_layout(yaxis_title='LOS')
        st.plotly_chart(
            plotlyFigHourlyLOS, 
            use_container_width=True,   
            sharing="streamlit", 
            theme=None
        )
        
    def generateTimeSeriesAnalytics(self, selectedDestinations, hoursToForecast):
        self.dfHourlyLOS = getHourlyLOS(self.factVolumeSpeed, selectedDestinations)

        yEndogenous = self.dfHourlyLOS.loc[: , ['IN']]
        yEndogenous.index.name = ""
        yEndogenous.columns = ['Latest Observed Data']

        yTrain, yTest = temporal_train_test_split(yEndogenous, test_size=0.3)

        yTrain.index.name = ""
        yTrain.columns = ['Training Data']
        yTest.index.name = ""
        yTest.columns = ['Test Data']

        yPred, predictionInterval, yCombined, forecaster = getPredictions(yTrain, yTest)

        lastObservedDatetime = yEndogenous.index[-1]
        offsetDatetime = lastObservedDatetime + timedelta(hours=1) 
        dateRange = pd.date_range(
            start=offsetDatetime, 
            periods=hoursToForecast, 
            freq='H'
        )

        yForecast, predictionIntervalForecast, yCombinedForecast = getForecasts(
            forecaster, 
            yEndogenous, 
            dateRange
        )

        yList = [
            yTrain, yTest,
            yPred, predictionInterval, yCombined,
            yForecast, predictionIntervalForecast, yCombinedForecast,
            yEndogenous
        ]

        metrics = getMetrics(yTest, yPred)
        
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