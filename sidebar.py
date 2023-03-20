import streamlit as st

from my_functions import dataframeToCSV, getFilteredCameras, getfactEventDataframe


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
        
    def renderSidebar(self):
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