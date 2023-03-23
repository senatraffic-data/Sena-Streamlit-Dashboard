import streamlit as st


class Sidebar:
    def __init__(
        self, 
        hourlyDatetimeList,
        availableRoads, 
        availableDestinations, 
        todayStr, 
        todayMinus2Str, 
        databaseCredentials, 
        dateFormat 
    ) -> None:
        self.hourlyDatetimeList = hourlyDatetimeList
        self.availableRoads = availableRoads
        self.availableDestinations = availableDestinations
        self.todayStr = todayStr
        self.todayMinus2Str = todayMinus2Str
        self.databaseCredentials = databaseCredentials
        self.dateFormat = dateFormat
    
    def renderSidebar(self, option: str):
        if option == 'event':
            
            with st.sidebar:
                
                with st.form(key='slicer'):
                    selectedDatetime = st.select_slider(
                        'Timestamp', 
                        self.hourlyDatetimeList,
                        value=(self.todayMinus2Str, self.todayStr)
                    )
                    selectedRoads = st.multiselect(
                        'Which road you want to view?',
                        self.availableRoads, 
                        [self.availableRoads[0]]
                    )
                    selectedDestinations = st.multiselect(
                        'Inbound or Outbound of KL?',
                        self.availableDestinations,
                        [self.availableDestinations[0]]
                    )
                    submitButton = st.form_submit_button("Submit")

                    if submitButton:
                        return selectedDatetime, selectedRoads, selectedDestinations
        elif option == 'volume-speed-LOS':
            
            with st.sidebar:
                
                with st.form(key='queryDataKey'):
                    st.write('Choose your relevant filters below then click "Submit". Will take some time...')
                    selectedDatetime = st.select_slider(
                        'Timestamp', 
                        self.hourlyDatetimeList,
                        value=(self.todayMinus2Str, self.todayStr)
                    )
                    selectedRoads = st.multiselect(
                        'Which road you want to view?', 
                        self.availableRoads, 
                        [self.availableRoads[0]]
                    )
                    selectedDestinations = st.multiselect(
                        'Inbound or Outbound of KL?', 
                        self.availableDestinations, 
                        [self.availableDestinations[0]]
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
        else:
            raise ValueError('Invalid Sidebar Option')