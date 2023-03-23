import pandas as pd

import streamlit as st

import streamlit_authenticator as stauth
from event_displayer import EventDisplayer

from my_functions import dataframeToCSV, displayStreetsAndCameras, generateHourlyDatetime

from authenticator import Authenticator

from streamlit_authenticator import SafeLoader

import os

from sidebar import Sidebar

from event import Event


def main() -> None:
    # hashedPasswords = stauth.Hasher(['senatraffic123']).generate()
    DATEFORMAT = '%Y-%m-%d %H:00:00'
    NODATAMESSAGE = 'No data to display. Apply and submit slicers in sidebar first'
    eventCountString = 'Event Counts'
    hourlyDatetimeList, todayStr, todayMinus2Str = generateHourlyDatetime(DATEFORMAT)
    
    myAuthenticator = Authenticator()
    userLoginsYamlPath = os.path.join(os.getcwd(), 'user_logins.yaml')   
    streamlitLoader=SafeLoader
    myAuthenticator.authenticate(filePath=userLoginsYamlPath, fileLoader=streamlitLoader)
    
    if myAuthenticator.authenticationStatus:
        myAuthenticator.streamlitAuthenticator.logout('Logout', 'main')
        st.write(f'Welcome *{myAuthenticator.name}*')
        databaseCredentials = {
            'HOSTNAME': st.secrets.mysql.HOSTNAME,
            'USERNAME': st.secrets.mysql.USERNAME,
            'USERPASSWORD': st.secrets.mysql.USERPASSWORD,
            'DATABASENAME': st.secrets.mysql.DATABASENAME
        }
        DATAPATH = os.path.join(
            os.getcwd(),
            'data',
            'Important_Roads.xlsx'
        )
        dfHotspotStreets = pd.read_excel(DATAPATH, sheet_name='Hotspot Congestion')
        dfInOutKL = pd.read_excel(DATAPATH, sheet_name='InOut KL Traffic')
        availableRoads = tuple(dfHotspotStreets['road'].values)
        availableDestinations = ['IN', 'OUT']
        sidebar = Sidebar(
            hourlyDatetimeList,
            availableRoads, 
            availableDestinations, 
            todayStr, 
            todayMinus2Str, 
            databaseCredentials, 
            DATEFORMAT
            )
        
        try:
            selectedDatetime, selectedRoads, selectedDestinations = sidebar.renderSidebar(option='event')
        except:
            st.write(NODATAMESSAGE)
            
        event = Event()
        
        try:
            event.getFilteredCameras(selectedRoad=selectedRoads, databaseCredentials=databaseCredentials)
            event.getfactEventDataframe(
                selectedDatetime=selectedDatetime,
                selectedRoad=selectedRoads,
                selectedDestinations=selectedDestinations,
                dateFormat=DATEFORMAT,
                databaseCredentials=databaseCredentials
            )
            factEventCSV = dataframeToCSV(event.factEvent)
        except:
            st.write(NODATAMESSAGE)

        st.title('Traffic Dashboard')
        eventDisplayer = EventDisplayer(event)
        
        try:
            eventDisplayer.displayOverallMetrics()
            eventDisplayer.displayEventCountByCameraID()
            eventDisplayer.displayTreemap()
            eventDisplayer.displayEventCountByLane()
            eventDisplayer.displayDetectionConfidenceByEventAndItemType()
            eventDisplayer.displayHourlyDetectionConfidence()
            eventDisplayer.displayHourlyEventCount(selectedDestinations, eventCountString)
            displayStreetsAndCameras(
                dfHotspotStreets, 
                dfInOutKL, 
                event.dimCamera
            )
            st.header('Raw Event Data')
            st.write(event.factEvent)
            st.download_button(
                label="Download data as CSV",
                data=factEventCSV,
                file_name='event_raw_data.csv',
                mime='text/csv'
            )
        except:
            st.write(NODATAMESSAGE)
            
        # Use the below if-else block for a more personalized experience for different users (privilege based on username)
        # Commented out for now
        # if username == 'jsmith':
        #     st.write(f'Welcome *{name}*')
        #     st.title('Application 1')
        # elif username == 'rbriggs':
        #     st.write(f'Welcome *{name}*')
        #     st.title('Application 2')
    elif myAuthenticator.authenticationStatus == False:
        st.error('Username/password is incorrect')
    elif myAuthenticator.authenticationStatus == None:
        st.warning('Please enter your username and password')


if __name__ == '__main__':
    main()