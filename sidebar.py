import streamlit as st


class Sidebar:
    def __init__(self, availableRoads, hourlyDatetimeList) -> None:
        self.availableRoads = availableRoads
        self.hourlyDatetimeList = hourlyDatetimeList
    
    def renderSidebar(self):
        with st.sidebar:

            with st.form(key='slicer'):
                selectedRoads = st.multiselect('Which road you want to view?',
                                                self.availableRoads, 
                                                [self.availableRoads[0]])
                selectedDatetime = st.select_slider('Timestamp', 
                                                    self.hourlyDatetimeList,
                                                    value=(todayMinus2Str, todayStr))
                selectedDestinations = st.multiselect('Inbound or Outbound of KL?',
                                                    ['IN', 'OUT'],
                                                    ['IN'])
                submitButton = st.form_submit_button("Submit")

                if submitButton:
                    dimCamera = getFilteredCameras(selectedRoads,
                                                    HOSTNAME,
                                                    USERNAME,
                                                    USERPASSWORD,
                                                    DATABASENAME)

                    factEvent = getfactEventDataframe(dateFormat,
                                                    selectedDatetime,
                                                    selectedRoads,
                                                    selectedDestinations,
                                                    HOSTNAME,
                                                    USERNAME,
                                                    USERPASSWORD,
                                                    DATABASENAME)
                    factEventCSV = dataframeToCSV(factEvent)