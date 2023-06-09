from matplotlib import pyplot as plt

import numpy as np

import pandas as pd

import streamlit as st

import folium

from branca.colormap import LinearColormap

from streamlit_folium import folium_static

import plotly.express as px


def displayOverallVolumeSpeedMetrics(factVolumeSpeed, destination: str):
    st.subheader('Overall Metrics')
    
    st.write('Vehicle Count')
    
    destinationCondition = ( factVolumeSpeed['destination'] == destination )
    destinationFilteredFactVolumeSpeed = factVolumeSpeed.loc[destinationCondition]
    
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


def displayHeatMap(factVolumeSpeed, dimCamera, destination: str):
    st.subheader('Heat Map')
    
    destinationCondition = ( factVolumeSpeed['destination'] == destination )
    destinationFilteredFactVolumeSpeed = factVolumeSpeed.loc[destinationCondition]
    
    mergedMetricsCamera = destinationFilteredFactVolumeSpeed.merge(
        dimCamera, 
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
    center = np.mean(subsetted.values[: , 0: 2], axis=0)
    
    baseMap = folium.Map(
        location=center, 
        zoom_start=12, 
        tiles='OpenStreetMap'
    )
    
    layer = folium.FeatureGroup(name='Updated Layer')
    coordinates = np.array(subsetted.values, dtype=np.float64)
    
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
    
    for cameraID, coordinate in zip(cameraIDs, coordinates):
        radius = coordinate[-1] 
        # Use the value as the radius
        folium.CircleMarker(
            location=coordinate[0: 2], 
            radius=radius, 
            color=colormap(coordinate[-1]),
            fill=True, 
            fill_color=colormap(coordinate[-1]),
            tooltip=f'<b>Camera ID: {cameraID} | LOS %: {coordinate[-1]: .2f}</b>'
        ).add_to(layer)

    layer.add_to(baseMap)
    folium_static(baseMap)


def displayHourlyVehicleCount(factVolumeSpeed):
    st.header('Hourly Vehicle Count')
    
    for columnName in factVolumeSpeed.columns[6: -4]:
        factVolumeSpeed[columnName] = \
            pd.to_numeric(factVolumeSpeed[columnName], errors='coerce')
    
    columnsToAggregate = [
        'bus_count', 'car_count', 
        'lorry_count', 'truck_count', 
        'van_count', 'motorbike_count', 
        'total_count'
    ]
    
    dfHourlyVehicleCount = factVolumeSpeed.groupby(['datetime'])[columnsToAggregate].sum()
    dfHourlyVehicleCount.index.name = ""
    dfHourlyVehicleCount.columns = ['bus', 'car', 'lorry','truck', 'van', 'motorbike', 'total']
    
    averageVehicleCount = dfHourlyVehicleCount.mean(axis=0)['car']
    
    figCarCount, axCarCount = plt.subplots(1, 1)
    dfHourlyVehicleCount.plot(
        kind='line',
        title=r'Hourly Vehicle Count',
        ax=axCarCount,
        ylabel='Count'
    )
    axCarCount.axhline(y=averageVehicleCount, color='g', linestyle='--')
    plt.style.use('dark_background')
    st.pyplot(figCarCount)
    
    plotlyFigHourlyCarCount = px.line(
        dfHourlyVehicleCount, 
        template="plotly_dark", 
        title='Hourly Vehicle Count'
    )
    
    plotlyFigHourlyCarCount.add_hline(y=averageVehicleCount, line_dash="dash", line_color="green")
    plotlyFigHourlyCarCount.update_layout(yaxis_title='Vehicle Count')
    
    st.plotly_chart(
        plotlyFigHourlyCarCount, 
        use_container_width=True,   
        sharing="streamlit", 
        theme=None
    )


def displayHourlyLOSInboundOutbound(dfHourlyLOS):
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
    
    yThresholds = [24.36, 39.94, 57.73, 77.72, 100, 125]
    hexColorCodes = ['#00901a', '#6db046', '#a38600', '#d9d61c', '#e66c37', '#ff0000']
    
    for yThreshold, hexColorCode in zip(yThresholds, hexColorCodes):
        plt.axhline(
            y=yThreshold, 
            color=hexColorCode, 
            linestyle='--', 
            alpha=0.5
        )
        
    st.pyplot(figTimePlot)
    
    plotlyFigHourlyLOS = px.line(
        dfHourlyLOS, 
        template="plotly_dark", 
        title='Hourly LOS'
    )
    
    for yThreshold, hexColorCode in zip(yThresholds, hexColorCodes):
        plotlyFigHourlyLOS.add_shape(
            type="line",
            x0=dfHourlyLOS.index[0],
            y0=yThreshold,
            x1=dfHourlyLOS.index[-1],
            y1=yThreshold,
            line=dict(
                color=hexColorCode,
                width=1,
                dash="dashdot",
            ),
        )

    plotlyFigHourlyLOS.update_layout(yaxis_title='LOS')
    st.plotly_chart(
        plotlyFigHourlyLOS, 
        use_container_width=True,   
        sharing="streamlit", 
        theme=None
    )