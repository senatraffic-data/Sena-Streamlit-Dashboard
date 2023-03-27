import streamlit as st

from abc import ABC, abstractmethod


class Sidebar(ABC):
    def __init__(self, temporalSpatialInfo: dict) -> None:
        self.temporalSpatialInfo = temporalSpatialInfo
    
    @abstractmethod
    def renderSidebar(self):
        pass
    
    
class EventSidebar(Sidebar):
    def __init__(self, temporalSpatialInfo: dict) -> None:
        super().__init__(temporalSpatialInfo)
        
    def renderSidebar(self):
        with st.sidebar:
                
            with st.form(key='slicer'):
                selectedDatetime = st.select_slider(
                    'Timestamp', 
                    self.temporalSpatialInfo['hourlyDatetime'],
                    value=(self.temporalSpatialInfo['todayMinus2'], self.temporalSpatialInfo['today'])
                )
                
                selectedRoads = st.multiselect(
                    'Which road you want to view?',
                    self.temporalSpatialInfo['roads'], 
                    [self.temporalSpatialInfo['roads'][0]]
                )
                
                selectedDestinations = st.multiselect(
                    'Inbound or Outbound of KL?',
                    self.temporalSpatialInfo['destinations'],
                    [self.temporalSpatialInfo['destinations'][0]]
                )
                
                submitButton = st.form_submit_button("Submit")

                if submitButton:
                    return selectedDatetime, selectedRoads, selectedDestinations
    
    
class VolumeSidebar(Sidebar):
    def __init__(self, temporalSpatialInfo: dict) -> None:
        super().__init__(temporalSpatialInfo)
        
    def renderSidebar(self):
        with st.sidebar:
                
            with st.form(key='queryDataKey'):
                st.write('Choose your relevant filters below then click "Submit". Will take some time...')
                
                selectedDatetime = st.select_slider(
                    'Timestamp', 
                    self.temporalSpatialInfo['hourlyDatetime'],
                    value=(self.temporalSpatialInfo['todayMinus2'], self.temporalSpatialInfo['today'])
                )
                
                selectedRoads = st.multiselect(
                    'Which road you want to view?', 
                    self.temporalSpatialInfo['roads'], 
                    [self.temporalSpatialInfo['roads'][0]]
                )
                
                selectedDestinations = st.multiselect(
                    'Inbound or Outbound of KL?', 
                    self.temporalSpatialInfo['destinations'], 
                    [self.temporalSpatialInfo['destinations'][0]]
                )
                
                daysToForecast = st.slider(
                    'How many days you want to forecast ahead?', 
                    1, 
                    7, 
                    1
                )
                
                hoursToForecast = daysToForecast * 24
                submitButton = st.form_submit_button("Submit")

                if submitButton:                    
                    return selectedDatetime, selectedRoads, selectedDestinations, hoursToForecast