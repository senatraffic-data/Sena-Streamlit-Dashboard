from datetime import timedelta
import pandas as pd

import streamlit as st

from my_functions import dataframeToCSV, getFactVolumeSpeed, getFilteredCameras, getForecasts, getHourlyLOS, getMetrics, getPredictions, getfactEventDataframe

from sktime.forecasting.model_selection import temporal_train_test_split


class Sidebar:
    def __init__(
        self, 
        availableRoads, 
        hourlyDatetimeList, 
        todayMinus2Str, 
        todayStr, 
        databaseCredentials, 
        dateFormat
    ) -> None:
        self.availableRoads = availableRoads
        self.hourlyDatetimeList = hourlyDatetimeList
        self.todayMinus2Str = todayMinus2Str
        self.todayStr = todayStr
        self.databaseCredentials = databaseCredentials
        self.dateFormat = dateFormat
        
    def renderSidebar(self, option: str):
        if option == 'event':
            with st.sidebar:
                with st.form(key='slicer'):
                    selectedRoads = st.multiselect('Which road you want to view?',
                                                    self.availableRoads, 
                                                    [self.availableRoads[0]])
                    selectedDatetime = st.select_slider('Timestamp', 
                                                        self.hourlyDatetimeList,
                                                        value=(self.todayMinus2Str, self.todayStr))
                    selectedDestinations = st.multiselect('Inbound or Outbound of KL?',
                                                        ['IN', 'OUT'],
                                                        ['IN'])
                    submitButton = st.form_submit_button("Submit")

                    if submitButton:
                        dimCamera = getFilteredCameras(
                            selectedRoads,
                            self.databaseCredentials
                        )
            
                        factEvent = getfactEventDataframe(
                            self.dateFormat,
                            selectedDatetime,
                            selectedRoads,
                            selectedDestinations,
                            self.databaseCredentials
                        )
                        
                        factEventCSV = dataframeToCSV(factEvent)
                        
                        return dimCamera, factEvent, factEventCSV, selectedDestinations
        elif option == 'volume-speed-LOS':
            with st.sidebar:
                with st.form(key='queryDataKey'):
                    st.write('Choose your relevant filters below then click "Submit". Will take some time...')
                    
                    selectedRoads = st.multiselect(
                        'Which road you want to view?', 
                        self.availableRoads, 
                        [self.availableRoads[0]]
                    )
                    selectedDatetime = st.select_slider(
                        'Timestamp', 
                        self.hourlyDatetimeList,
                        value=(self.todayMinus2Str, self.todayStr)
                    )
                    selectedDestinations = st.multiselect(
                        'Inbound or Outbound of KL?', 
                        ['IN', 'OUT'], 
                        ['IN']
                    )
                    
                    daysToForecast = st.slider('How many days you want to forecast ahead?', 1, 7, 1)
                    hoursToForecast = daysToForecast * 24
                    
                    submitButton = st.form_submit_button("Submit")

                    if submitButton:
                        dimCamera = getFilteredCameras(selectedRoads, self.databaseCredentials)
                        
                        factVolumeSpeed = getFactVolumeSpeed(
                            selectedRoads, 
                            selectedDestinations,
                            self.databaseCredentials, 
                            selectedDatetime
                        )
                        factVolumeSpeedCSV = dataframeToCSV(factVolumeSpeed)
                                                
                        return dimCamera, factVolumeSpeed, factVolumeSpeedCSV
        else:
            raise ValueError('Invalid Sidebar Option')