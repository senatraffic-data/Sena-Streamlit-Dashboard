from matplotlib import pyplot as plt
import pandas as pd
from volume_speed_los import VolumeSpeedLOS

import streamlit as st

import numpy as np

import folium

from branca.colormap import LinearColormap

from streamlit_folium import folium_static

import plotly.express as px


class VolumeDisplayer:
    def __init__(self, volumeSpeedLOS: VolumeSpeedLOS) -> None:
        self.volumeSpeedLOS = volumeSpeedLOS
    
    def displayOverallVolumeSpeedMetrics(self, destination: str):
        st.subheader('Overall Metrics')
        st.write('Vehicle Count')
        destinationFilteredFactVolumeSpeed = self.volumeSpeedLOS.factVolumeSpeed\
            .loc[self.volumeSpeedLOS.factVolumeSpeed['destination']==destination]
        minimumCarCount = int(destinationFilteredFactVolumeSpeed['car_count'].min())
        averageCarCount = int(destinationFilteredFactVolumeSpeed['car_count'].mean())
        maximumCarCount = int(destinationFilteredFactVolumeSpeed['car_count'].max())
        carColumn1, carColumn2 , carColumn3 = st.columns(3)
        with carColumn1:
            st.metric(label='Minimum Car Count', value=minimumCarCount)
        with carColumn2:
            st.metric(label='Average Car Count', value=averageCarCount)
        with carColumn3:
            st.metric(label='Maximum Car Count', value=maximumCarCount)
        st.write('Lane Speed (km/h)')
        descriptions = destinationFilteredFactVolumeSpeed.describe()
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
        
    def displayHeatMap(self, destination: str):
        st.subheader('Heat Map')
        destinationFilteredFactVolumeSpeed = self.volumeSpeedLOS.factVolumeSpeed\
            .loc[self.volumeSpeedLOS.factVolumeSpeed['destination']==destination]
        mergedMetricsCamera = destinationFilteredFactVolumeSpeed.merge(
            self.volumeSpeedLOS.dimCamera, 
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
        
        for columnName in self.volumeSpeedLOS.factVolumeSpeed.columns[6: -4]:
            self.volumeSpeedLOS.factVolumeSpeed[columnName] = \
                pd.to_numeric(self.volumeSpeedLOS.factVolumeSpeed[columnName], errors='coerce')
        
        dfHourlyVehicleCount = self.volumeSpeedLOS.factVolumeSpeed.groupby(['datetime'])[['bus_count', 'car_count', 'lorry_count', 'truck_count', 'van_count', 'motorbike_count', 'total_count']].sum()
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
        plotlyFigHourlyCarCount = px.line(
            dfHourlyVehicleCount, 
            template="plotly_dark", 
            title='Hourly Vehicle Count'
        )
        plotlyFigHourlyCarCount.update_layout(yaxis_title='Vehicle Count')
        st.plotly_chart(
            plotlyFigHourlyCarCount, 
            use_container_width=True,   
            sharing="streamlit", 
            theme=None
        )
        
    def displayHourlyLOSInboundOutbound(self, dfHourlyLOS):
        st.header('Hourly LOS Plot')
        dfHourlyLOS.index.name = ""
        figTimePlot, axTimePlot = plt.subplots(1, 1)
        dfHourlyLOS.plot(
            kind='line',
            title=r'Hourly LOS% For Inbound & Outbound',
            ax=axTimePlot,
            ylabel='LOS %'
        )
        plt.style.use('dark_background')
        st.pyplot(figTimePlot)
        plotlyFigHourlyLOS = px.line(
            dfHourlyLOS, 
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