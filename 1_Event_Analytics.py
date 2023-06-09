import pandas as pd

import streamlit as st

from streamlit_authenticator import SafeLoader

import os

from my_functions import (
    dataframeToCSV, 
    displayStreetsAndCameras, 
    generateHourlyDatetime,
    authenticate,
    renderEventSidebar,
    getFilteredCameras,
    getfactEventDataframe
)

from event_displayer_functions import (
    displayDetectionConfidenceByEventAndItemType,
    displayEventCountByCameraID,
    displayEventCountByLane,
    displayHourlyDetectionConfidence,
    displayHourlyEventCount,
    displayOverallMetrics,
    displayTreemap
)


def main() -> None:
    USERS_YAML_PATH = 'user_logins.yaml'
    userLoginsYamlPath = os.path.join(os.getcwd(), USERS_YAML_PATH)   
    streamlitLoader = SafeLoader
    name, authenticationStatus, streamlitAuthenticator = authenticate(
        filePath=userLoginsYamlPath, 
        fileLoader=streamlitLoader
    )
    
    if authenticationStatus:
        streamlitAuthenticator.logout('Logout', 'main')
        st.write(f'Welcome *{name}*')
        st.title('Traffic Dashboard')
        
        st.header('Quick Links')
        st.markdown("[Overall Metrics](#overall-metrics)")
        st.markdown("[Event Count per Camera ID](#event-counts-per-camera-id)")
        st.markdown("[Event Count per Lane Treemap](#event-count-per-lane-treemap)")
        st.markdown("[Event Count By Lanes](#event-count-by-lanes)")
        st.markdown("[Event Detection Confidence by Event Type and Item Type](#event-detection-confidence-by-event-type-and-item-type)")
        st.markdown("[Hourly Detection Confidence](#hourly-detection-confidence)")
        st.markdown("[Hourly Event Count by Event Type](#hourly-event-count-by-event-type)")
        st.markdown("[Important Streets](#important-streets)")
        st.markdown("[Cameras In Selected Road](#cameras-in-selected-road)")
        st.markdown("[Raw Event Data](#raw-event-data)")
        
        databaseCredentials = {
            'HOSTNAME': st.secrets.mysql.HOSTNAME,
            'USERNAME': st.secrets.mysql.USERNAME,
            'USERPASSWORD': st.secrets.mysql.USERPASSWORD,
            'DATABASENAME': st.secrets.mysql.DATABASENAME
        }
        
        IMPORTANT_ROADS_PATH1 = 'data'
        IMPORTANT_ROADS_PATH2 = 'Important_Roads.xlsx'
        
        DATAPATH = os.path.join(
            os.getcwd(),
            IMPORTANT_ROADS_PATH1,
            IMPORTANT_ROADS_PATH2
        )
        
        HOTSPOT_CONGESTION = 'Hotspot Congestion'
        dfHotspotStreets = pd.read_excel(DATAPATH, sheet_name=HOTSPOT_CONGESTION)
        
        INOUT_KL = 'InOut KL Traffic'
        dfInOutKL = pd.read_excel(DATAPATH, sheet_name=INOUT_KL)
        
        availableRoads = tuple(dfHotspotStreets['road'].values)
        availableDestinations = ['IN', 'OUT']
        
        # hashedPasswords = stauth.Hasher(['senatraffic123']).generate()
        HOURLY_DATETIME_FORMAT = '%Y-%m-%d %H:00:00'
        NO_DATA_MESSAGE = 'No data to display. Apply and submit slicers in sidebar first'
        eventCountString = 'Event Counts'
        hourlyDateRange, todayStr, todayMinus2Str = generateHourlyDatetime(HOURLY_DATETIME_FORMAT)
        
        temporalSpatialInfo = {
            'hourlyDatetime': hourlyDateRange, 
            'roads': availableRoads, 
            'destinations': availableDestinations, 
            'today': todayStr, 
            'todayMinus2': todayMinus2Str, 
            'hourlyDatetimeFormat': HOURLY_DATETIME_FORMAT
        }
        
        try:
            selectedDatetime, selectedRoads, selectedDestinations = renderEventSidebar(temporalSpatialInfo)
            
            userSlicerSelections = {
                'hourlyDatetime': selectedDatetime, 
                'roads': selectedRoads, 
                'destinations': selectedDestinations,
                'hourlyDatetimeFormat': HOURLY_DATETIME_FORMAT,
            }
        except:
            st.write(NO_DATA_MESSAGE)
        
        try:
            dimCamera = getFilteredCameras(userSlicerSelections['roads'], databaseCredentials)
            factEvent = getfactEventDataframe(userSlicerSelections, databaseCredentials)
            factEventCSV = dataframeToCSV(factEvent)
        except:
            st.write(NO_DATA_MESSAGE)

        try:
            displayOverallMetrics(factEvent)
            displayEventCountByCameraID(factEvent)
            displayTreemap(factEvent)
            displayEventCountByLane(factEvent)
            displayDetectionConfidenceByEventAndItemType(factEvent)
            displayHourlyDetectionConfidence(factEvent)
            displayHourlyEventCount(factEvent, userSlicerSelections['destinations'], eventCountString)
            
            displayStreetsAndCameras(
                dfHotspotStreets, 
                dfInOutKL, 
                dimCamera
            )
            
            st.header('Raw Event Data')
            st.write(factEvent)
            
            st.download_button(
                label="Download data as CSV",
                data=factEventCSV,
                file_name='event_raw_data.csv',
                mime='text/csv'
            )
        except:
            st.write(NO_DATA_MESSAGE)
            
        # Use the below if-else block for a more personalized experience for different users (privilege based on username)
        # Commented out for now
        # if username == 'jsmith':
        #     st.write(f'Welcome *{name}*')
        #     st.title('Application 1')
        # elif username == 'rbriggs':
        #     st.write(f'Welcome *{name}*')
        #     st.title('Application 2')
    elif authenticationStatus == False:
        st.error('Username/password is incorrect')
    elif authenticationStatus == None:
        st.warning('Please enter your username and password')


if __name__ == '__main__':
    main()