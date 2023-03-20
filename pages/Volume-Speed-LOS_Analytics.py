import os

import pandas as pd

import streamlit as st

from authenticator import Authenticator
from displayMetrics import displayHeatMap, displayHourlyLOSInboundOutbound, displayHourlyVehicleCount, displayOverallVolumeSpeedMetrics, displayStreetsAndCameras, displayTimeseriesForecasting, displayTimeseriesTesting

from my_functions import displayVolumeSpeedLOSAnalytics, generateHourlyDatetime

from streamlit_authenticator import SafeLoader

from sidebar import Sidebar

from volume_speed_los import VolumeSpeedLOS

# import streamlit_authenticator as stauth


# hashedPasswords = stauth.Hasher(['senatraffic123']).generate()
HOURLYDATEFORMAT = '%Y-%m-%d %H:00:00'
NODATAMESSAGE = 'No data to display. Apply and submit slicers in sidebar first'
eventCountString = 'Event Counts'
hourlyDatetimeList, todayStr, todayMinus2Str = generateHourlyDatetime(HOURLYDATEFORMAT)

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

    sidebar = Sidebar(
            availableRoads, 
            hourlyDatetimeList, 
            todayMinus2Str, 
            todayStr, 
            databaseCredentials, 
            HOURLYDATEFORMAT
    )
    try:
        dimCamera, factVolumeSpeed, factVolumeSpeedCSV = sidebar.renderSidebar(option='volume-speed-LOS')
        volumeSpeedLOS = VolumeSpeedLOS(factVolumeSpeed, dimCamera)
    except:
        st.write(NODATAMESSAGE)

    DATANOTQUERIEDYET = 'Data not queried yet, nothing to display'

    st.title('Traffic Dashboard')
    
    st.header('Inbound')
    
    try:
        heatMapColumn11 ,heatMapColumn12 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn11:
            volumeSpeedLOS.displayOverallVolumeSpeedMetrics()
        with heatMapColumn12:
            volumeSpeedLOS.displayHeatMap()   
    except:
        st.write(DATANOTQUERIEDYET)
        
    st.header('Outbound')
    
    try:
        heatMapColumn21 , heatMapColumn22 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn21:
            volumeSpeedLOS.displayOverallVolumeSpeedMetrics()
        with heatMapColumn22:
            volumeSpeedLOS.displayHeatMap()
    except:
        st.write(DATANOTQUERIEDYET)
    
    try:    
        volumeSpeedLOS.displayHourlyVehicleCount()
    except:
        st.write(DATANOTQUERIEDYET)
        
    try:
        volumeSpeedLOS.generateTimeSeriesAnalytics()
        volumeSpeedLOS.displayHourlyLOSInboundOutbound()
    except:
        st.write(DATANOTQUERIEDYET)

    try:
        displayStreetsAndCameras(
            dfHotspotStreets,
            dfInOutKL,
            dimCamera
        )
    except:
        st.write(DATANOTQUERIEDYET)

    st.header('Raw Volume-Speed-LOS% Data')
    try:
        st.write(factVolumeSpeed)
        st.download_button(label="Download data as CSV",
                           data=factVolumeSpeedCSV,
                           file_name='volume_speed_los.csv',
                           mime='text/csv')
    except:
        st.write(DATANOTQUERIEDYET)

    try:
        volumeSpeedLOS.displayTimeseriesTesting(forecaster, metrics, y_list)
    except:
        st.write(DATANOTQUERIEDYET)

    try:
        volumeSpeedLOS.displayTimeseriesForecasting(y_list)
    except:
        st.write(DATANOTQUERIEDYET)

    ## Use the below if-else block for a more personalized experience for different users (privilege based on username)
    ## Commented out for now
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