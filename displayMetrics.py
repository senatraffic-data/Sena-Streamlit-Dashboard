import streamlit as st

import matplotlib.pyplot as plt

import pandas as pd

import plotly.express as px

import numpy as np

import folium

from streamlit_folium import folium_static

from branca.colormap import LinearColormap


@st.cache_data
def getCSV(df):
    return df.to_csv().encode('utf-8')


def displayOverallMetrics(factEvent):
    st.header('Overall Metrics')

    totalNumberOfEvents = factEvent.shape[0]
    eventCountByEventType = factEvent.groupby('event_type')['camera_id'].count()
    availableEvents = list(eventCountByEventType.index)
    numberOfAvailableEvents = len(availableEvents)
    eventCountValues = eventCountByEventType.values

    st.metric(label='Total Number of Events', value=totalNumberOfEvents)

    eventColumns = st.columns(numberOfAvailableEvents)

    for i, (eventName, eventCount) in enumerate(zip(availableEvents, eventCountValues)):
        eventColumns[i].metric(label=eventName, value=eventCount)

    confidenceByEventType = factEvent.groupby('event_type')['confidence'].mean().dropna()
    eventsWithConfidence = list(confidenceByEventType.index)
    confidenceValues = confidenceByEventType.values
    numberOfEventsWithConfidence = len(eventsWithConfidence)

    confidenceColumns = st.columns(numberOfEventsWithConfidence)

    for i, (eventName, event_confidence) in enumerate(zip(eventsWithConfidence, confidenceValues)):
        confidenceColumns[i].metric(label=f'**{eventName}** Detection Confidence', 
                                    value=f'{event_confidence * 100 : .2f} %')


def displayStreetsAndCameras(dfHotspotStreets, dfInOutKL, dimCamera):
    st.header('Important Streets')

    leftColumn1, rightColumn1 = st.columns(2)

    with leftColumn1:
        st.subheader('Hot-Spot Streets')
        st.write(dfHotspotStreets)

    with rightColumn1:
        st.subheader('In-Out KL Streets')
        st.write(dfInOutKL)

    st.header('Cameras In Selected Road')

    st.write(dimCamera)


def displayEventCountByCameraID(factEvent):
    st.header('Event Counts per Camera ID')
    eventCountByCameraID = pd.crosstab(factEvent['camera_id'], factEvent['event_type'])
    leftColumn2, rightColumn2 = st.columns(2)
    
    with leftColumn2:
        st.bar_chart(factEvent['camera_id'].value_counts(dropna=False))
        
    with rightColumn2:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(1, 1)
        eventCountByCameraID.plot(kind='barh', 
                                stacked=True, 
                                ax=ax)
        st.pyplot(fig)
    
    eventCountString = 'Event Counts'
    plotlyFigEventCountByCameraID = px.bar(factEvent['camera_id'].value_counts(dropna=False), 
                                            orientation='v',
                                            labels={'index': 'Camera ID',
                                                    'value': eventCountString})
    st.plotly_chart(plotlyFigEventCountByCameraID, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)
    st.write(eventCountByCameraID)
    
    eventCountByCameraIDCSV = getCSV(eventCountByCameraID)
    
    st.download_button(label="Download data as CSV",
                       data=eventCountByCameraIDCSV,
                       file_name='event_count_by_camera_id.csv',
                       mime='text/csv')
    
    
def displayTreemap(factEvent):
    st.header('Event Counts per Lane/Zone Treemap')
    eventCountByLane = factEvent.groupby(['event_type', 'zone'], as_index=False).agg({'camera_id': 'count'})
    eventCountByLaneCSV = getCSV(eventCountByLane)
    treemapFig = px.treemap(eventCountByLane,
                             path=[eventCountByLane['event_type'], eventCountByLane['zone']],
                             values=eventCountByLane['camera_id'],
                             width=500,
                             height=750)
    
    st.plotly_chart(treemapFig, use_container_width=True)
    
    st.write(eventCountByLane)
    st.download_button(label="Download data as CSV",
                       data=eventCountByLaneCSV,
                       file_name='event_count_by_zone_lane.csv',
                       mime='text/csv')


def displayEventCountByLane(factEvent):
    st.header('Event Count By Lanes')

    b2tLaneFilter = factEvent['zone'].str.startswith('b2t')
    t2bLaneFilter = factEvent['zone'].str.startswith('t2b')
    
    b2tEvents  =factEvent.loc[b2tLaneFilter]
    t2bEvents = factEvent.loc[t2bLaneFilter]
    
    b2tEventCountByLane = pd.crosstab(b2tEvents['zone'], 
                                      b2tEvents['event_type']).sort_values(by='zone', 
                                                                           ascending=False)
    t2bEventCountByLane = pd.crosstab(t2bEvents['zone'], t2bEvents['event_type'])
    
    figEventCountByLane, axEventCountByLane = plt.subplots(1, 2)
    
    b2tEventCountByLane.plot(kind='bar', 
                             stacked=True, 
                             ax=axEventCountByLane[0])
    t2bEventCountByLane.plot(kind='bar', 
                             stacked=True, 
                             ax=axEventCountByLane[1])
    plt.tight_layout()
    st.pyplot(figEventCountByLane)
    
    byLane1, byLane2 = st.columns(2)
        
    with byLane1:
        b2tPlotlyFigEventCountByLane = px.bar(b2tEventCountByLane, 
                                              orientation='v')
        st.plotly_chart(b2tPlotlyFigEventCountByLane, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)
        
    with byLane2:
        t2bPlotlyFigEventCountByLane = px.bar(t2bEventCountByLane, 
                                                orientation='v')
        st.plotly_chart(t2bPlotlyFigEventCountByLane, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)


def displayDetectionConfidenceByEventAndItemType(factEvent):
    st.header('Event Detection Confidence by Event Type and Item Type')
    confidence = pd.crosstab(factEvent['event_type'], 
                             factEvent['item_type'], 
                             factEvent['confidence'], 
                             aggfunc=np.mean)

    figConfidence, axConfidence = plt.subplots(1, 1)
    confidencePlot = confidence.plot(kind='barh', 
                                      stacked=False, 
                                      ax=axConfidence)
    axConfidence.set_yticklabels(confidence.index, rotation=0)
    axConfidence.legend(loc="upper left")
    axConfidence.set_ylabel('Event Type')
    axConfidence.set_xlabel('Detection Confidence')
    
    for i in confidencePlot.containers:
        labels = [f'{val * 100 :.2f} %' if val > 0 else '' for val in i.datavalues]
        axConfidence.bar_label(i,
                               label_type='edge',
                               labels=labels,
                               fontsize=10,
                               padding=3)

    plt.tight_layout()
    st.pyplot(figConfidence)

    confidenceIndexResetted = confidence.reset_index()
    plotlyFigEventConfidence = px.bar(confidenceIndexResetted, 
                                      x='event_type',
                                      y=confidenceIndexResetted.columns[1: ],
                                      barmode='group',
                                      orientation='v')
    st.plotly_chart(plotlyFigEventConfidence, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)


def displayHourlyDetectionConfidence(factEvent):
    st.header('Hourly Detection Confidence')
    
    factEvent['datetime'] = pd.to_datetime(factEvent['datetime'])
    dfHourlyConfidence = factEvent.pivot_table(values=['confidence'],
                                               index=['datetime'],
                                               columns=['event_type'],
                                               aggfunc={'confidence': np.mean})
    dfHourlyConfidence = dfHourlyConfidence.asfreq('H')
    dfHourlyConfidence = dfHourlyConfidence.ffill().rolling(3).mean()
    
    previousColumns = list(dfHourlyConfidence.columns)
    newColumns = [multi_column[-1] for multi_column in previousColumns]
    dfHourlyConfidence.columns = newColumns
    dfHourlyConfidence.index.name = ""
    
    figHourlyConfidence, axHourlyConfidence = plt.subplots(1, 1)
    dfHourlyConfidence.plot(kind='line',
                              title=r'Hourly Detection Confidence by Event Type',
                              ax=axHourlyConfidence,
                              ylabel='Confidence')
    st.pyplot(figHourlyConfidence)
    
    plotlyFigHourlyConfidence = px.line(dfHourlyConfidence)
    plotlyFigHourlyConfidence.update_layout(yaxis_title="Confidence")
    st.plotly_chart(plotlyFigHourlyConfidence, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)


def displayHourlyEventCount(factEvent, selectedDestinations, eventCountString):
    st.header('Hourly Event Count by Event Type')
    
    factEventInbound = factEvent[factEvent['direction']=='IN']
    factEventOutbound = factEvent[factEvent['direction']=='OUT']
    
    dfHourlyEventCountInbound = pd.crosstab(index=factEventInbound['datetime'], 
                                           columns=factEventInbound['event_type'])
    dfHourlyEventCountInbound = dfHourlyEventCountInbound.asfreq('H')
    dfHourlyEventCountInbound = dfHourlyEventCountInbound.ffill()
    dfHourlyEventCountInbound.index.name = ''
        
    dfHourlyEventCountOutbound = pd.crosstab(index=factEventOutbound['datetime'], 
                                            columns=factEventOutbound['event_type'])
    dfHourlyEventCountOutbound = dfHourlyEventCountOutbound.asfreq('H')
    dfHourlyEventCountOutbound = dfHourlyEventCountOutbound.ffill()
    dfHourlyEventCountOutbound.index.name = ''
        
    singleOrDoubleDestinationPlotting(selectedDestinations,
                                        dfHourlyEventCountInbound,
                                        dfHourlyEventCountOutbound,
                                        eventCountString)
    
    
def singleOrDoubleDestinationPlotting(selectedDestinations, 
                                      dfHourlyEventCountInbound, 
                                      dfHourlyEventCountOutbound,
                                      eventCountString):
    if ( selectedDestinations == ['IN', 'OUT'] ) or ( selectedDestinations == ['OUT', 'IN'] ):
        inColumn, outColumn = st.columns(2)
            
        with inColumn:
            figHourlyInbound, axHourlyInbound = plt.subplots(1, 1)
            dfHourlyEventCountInbound.plot(kind='line',
                                        title='Inbound',
                                        ax=axHourlyInbound,
                                        ylabel=eventCountString)
            st.pyplot(figHourlyInbound)
            
            plotlyFigHourlyCountInbound = px.line(dfHourlyEventCountInbound, 
                                                template="plotly_dark", 
                                                title='IN-bound')
            plotlyFigHourlyCountInbound.update_layout(yaxis_title=eventCountString)
            st.plotly_chart(plotlyFigHourlyCountInbound, 
                            use_container_width=True,
                            sharing="streamlit", 
                            theme=None)
        
        with outColumn:
            figHourlyOutbound, axHourlyOutbound = plt.subplots(1, 1)
            dfHourlyEventCountOutbound.plot(kind='line',
                                        title='Outbound',
                                        ax=axHourlyOutbound)
            st.pyplot(figHourlyOutbound)
            
            plotlyFigHourlyCountOutbound = px.line(dfHourlyEventCountOutbound,
                                                template="plotly_dark",
                                                title='OUT-bound')
            plotlyFigHourlyCountOutbound.update_layout(yaxis_title='')
            st.plotly_chart(plotlyFigHourlyCountOutbound,
                            use_container_width=True,
                            sharing="streamlit",
                            theme=None)
    elif selectedDestinations == ['IN']:
        figHourlyInbound, axHourlyInbound = plt.subplots(1, 1)
        dfHourlyEventCountInbound.plot(kind='line',
                                      title='Inbound',
                                      ax=axHourlyInbound,
                                      ylabel=eventCountString)
        st.pyplot(figHourlyInbound)
        
        plotlyFigHourlyCountInbound = px.line(dfHourlyEventCountInbound, 
                                             template="plotly_dark", 
                                             title='IN-bound')
        plotlyFigHourlyCountInbound.update_layout(yaxis_title=eventCountString)
        st.plotly_chart(plotlyFigHourlyCountInbound, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)
    elif selectedDestinations == ['OUT']:
        figHourlyOutbound, axHourlyOutbound = plt.subplots(1, 1)
        dfHourlyEventCountOutbound.plot(kind='line',
                                       title='Outbound',
                                       ax=axHourlyOutbound)
        st.pyplot(figHourlyOutbound)
        
        plotlyFigHourlyCountOutbound = px.line(dfHourlyEventCountOutbound,
                                              template="plotly_dark",
                                              title='OUT-bound')
        plotlyFigHourlyCountOutbound.update_layout(yaxis_title='')
        st.plotly_chart(plotlyFigHourlyCountOutbound,
                        use_container_width=True,
                        sharing="streamlit",
                        theme=None)
    else:
        st.write('ERROR')
        

def displayOverallVolumeSpeedMetrics(factVolumeSpeed):
    st.subheader('Overall Metrics')
    
    st.write('Vehicle Count')
    
    minimumCarCount = int(factVolumeSpeed['car_count'].min())
    averageCarCount = int(factVolumeSpeed['car_count'].mean())
    maximumCarCount = int(factVolumeSpeed['car_count'].max())
    
    carColumn1, carColumn2 , carColumn3 = st.columns(3)
    
    with carColumn1:
        st.metric(label='Minimum Car Count', value=minimumCarCount)
        
    with carColumn2:
        st.metric(label='Average Car Count', value=averageCarCount)
        
    with carColumn3:
        st.metric(label='Maximum Car Count', value=maximumCarCount)
    
    st.write('Lane Speed (km/h)')
    
    descriptions = factVolumeSpeed.describe()
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
    
    
def displayHourlyVehicleCount(factVolumeSpeed):
    st.header('Hourly Vehicle Count')
    
    dfHourlyCarCount = factVolumeSpeed.pivot_table(values=['car_count'],
                                                     index=['datetime'],
                                                     columns=['POV'])
    
    for columnName in factVolumeSpeed.columns[6: -4]:
        factVolumeSpeed[columnName] = pd.to_numeric(factVolumeSpeed[columnName], errors='coerce')
    
    dfHourlyVehicleCount = factVolumeSpeed.groupby(['datetime'])[['bus_count', 'car_count', 'lorry_count', 'truck_count', 'van_count', 'motorbike_count', 'total_count']].sum()

    dfHourlyVehicleCount.index.name = ""
    dfHourlyVehicleCount.columns = ['bus', 'car', 'lorry','truck', 'van', 'motorbike', 'total']
    
    figCarCount, axCarCount = plt.subplots(1, 1)
    dfHourlyVehicleCount.plot(kind='line',
                              title=r'Hourly Vehicle Count',
                              ax=axCarCount,
                              ylabel='Count')
    plt.style.use('dark_background')
    st.pyplot(figCarCount)
    
    dfHourlyCarCount.index.name = ""
    dfHourlyCarCount.columns = ['b2t', 't2b']
    
    # fig_car_count, ax_car_count = plt.subplots(1, 1)
    # df_hourly_car_count.plot(kind='line',
    #                         title=r'Hourly Car Count (b2t & t2b)',
    #                         ax=ax_car_count,
    #                         ylabel='Count')
    # plt.style.use('dark_background')
    # st.pyplot(fig_car_count)
        
    plotlyFigHourlyCarCount = px.line(dfHourlyCarCount, 
                                      template="plotly_dark", 
                                      title='Hourly Car Count')
    plotlyFigHourlyCarCount.update_layout(yaxis_title='Car Count')
    st.plotly_chart(plotlyFigHourlyCarCount, 
                    use_container_width=True,   
                    sharing="streamlit", 
                    theme=None)
    
    
def displayHourlyLOSInboundOutbound(dfHourlyLOS):
    st.header('Hourly LOS% Plot for Inbound & Outbound')
    
    dfHourlyLOS.index.name = ""
    
    figTimePlot, axTimePlot = plt.subplots(1, 1)
    dfHourlyLOS.plot(kind='line',
                    title=r'Hourly LOS% For Inbound & Outbound',
                    ax=axTimePlot,
                    ylabel='LOS %')
    plt.style.use('dark_background')
    st.pyplot(figTimePlot)
    
    plotlyFigHourlyLOS = px.line(dfHourlyLOS, 
                                 template="plotly_dark", 
                                 title='Hourly LOS')
    plotlyFigHourlyLOS.update_layout(yaxis_title='LOS')
    st.plotly_chart(plotlyFigHourlyLOS, 
                    use_container_width=True,   
                    sharing="streamlit", 
                    theme=None)
    
    
def displayTimeseriesTesting(forecaster, metrics, yList):
    st.header('Time-Series Model Testing')

    st.write(forecaster.summary())
    st.write(f'The testing MAPE is {metrics[0]}')
    st.write(f'The testing MSE is {metrics[1]}')
    st.write(yList[2])

    figForecast, axForecast = plt.subplots(1, 1)
    yList[0].plot(kind='line', 
                ax=axForecast,
                title=r'Hourly LOS% For Train, Testing, and Prediction',
                ylabel='LOS %')
    yList[1].plot(kind='line', 
                ax=axForecast)
    yList[2].plot(kind='line', 
                ax=axForecast)
    plt.fill_between(yList[3].index,
                        yList[3].loc[: , ('Coverage', 0.9, 'lower')],
                        yList[3].loc[: , ('Coverage', 0.9, 'upper')],
                        alpha=0.25)
    axForecast.legend()
    plt.tight_layout()
    st.pyplot(figForecast)
        
    plotlyFigHourlyLOSTrainTest = px.line(yList[4],
                                          template="plotly_dark",
                                          title=r'Hourly LOS% For Train, Testing, and Prediction')
    plotlyFigHourlyLOSTrainTest.update_layout(yaxis_title='LOS%')
    st.plotly_chart(plotlyFigHourlyLOSTrainTest,
                    use_container_width=True,
                    sharing="streamlit",
                    theme=None)
        
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
    
     
def displayTimeseriesForecasting(yList):
    st.header('Forecasting')

    figForecastAlt, axForecastAlt = plt.subplots(1, 1)
    yList[-1].plot(kind='line',
                    ax=axForecastAlt,
                    title=r'Hourly LOS% For Observed Data & Forecast',
                    ylabel='LOS %')
    yList[5].plot(kind='line',
                ax=axForecastAlt)
    plt.fill_between(yList[6].index,
                        yList[6].loc[: , ('Coverage', 0.9, 'lower')],
                        yList[6].loc[: , ('Coverage', 0.9, 'upper')],
                        alpha=0.25)
    axForecastAlt.legend()
    plt.tight_layout()
    st.pyplot(figForecastAlt)
    
    plotlyFigHourlyLOSForecast = px.line(yList[7], 
                                         template="plotly_dark",
                                         title=r'Hourly LOS% For Observed Data & Forecast')
    plotlyFigHourlyLOSForecast.update_layout(yaxis_title='LOS%')
    st.plotly_chart(plotlyFigHourlyLOSForecast,
                    use_container_width=True,
                    sharing="streamlit",
                    theme=None)
    
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
    
    
def displayHeatMap(factVolumeSpeed, dimCamera):
    st.subheader('Heat Map')
    
    mergedMetricsCamera = factVolumeSpeed.merge(dimCamera, 
                                                how='left', 
                                                on='camera_id')
    groupbyCameras = mergedMetricsCamera.groupby(['camera_id', 
                                                  'latitude', 
                                                  'longitude']).agg({'LOS': np.mean})
    groupbyCamerasIndexResetted = groupbyCameras.reset_index()
    subsetted1 = groupbyCamerasIndexResetted[['camera_id', 'latitude', 'longitude', 'LOS']].dropna()
    subsetted = subsetted1[['latitude', 'longitude', 'LOS']]
    cameraIDs = subsetted1['camera_id'].values
    
    # Define the center of the map
    center = subsetted.values[0, 0: 2]

    # Create a folium map
    baseMap = folium.Map(location=center, 
                zoom_start=12, 
                tiles='OpenStreetMap')
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
    colormap = LinearColormap(colors=['green', 'yellow', 'red'], 
                              index=indexSorted, 
                              vmin=0.0, 
                              vmax=150.0)
        
    # Add bubbles to the layer with color based on value
    for cameraID, coordinate in zip(cameraIDs, coordinates):
        radius = coordinate[-1] # Use the value as the radius
        folium.CircleMarker(location=coordinate[0: 2], 
                            radius=radius, 
                            color=colormap(coordinate[-1]),
                            fill=True, 
                            fill_color=colormap(coordinate[-1]),
                            tooltip=f'<b>Camera ID: {cameraID} | LOS %: {coordinate[-1]: .2f}</b>').add_to(layer)

    # Add the layer to the map
    layer.add_to(baseMap)

    # Display the map in Streamlit
    folium_static(baseMap)