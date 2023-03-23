import os

import pandas as pd

import streamlit as st

from authenticator import Authenticator

from my_functions import dataframeToCSV, displayStreetsAndCameras, generateHourlyDatetime

from streamlit_authenticator import SafeLoader

from sidebar import Sidebar
from timeseries_displayer import TimeSeriesDisplayer
from timeseries_forecaster import TimeSeriesForecaster
from volume_displayer import VolumeDisplayer

from volume_speed_los import VolumeSpeedLOS

# import streamlit_authenticator as stauth


# hashedPasswords = stauth.Hasher(['senatraffic123']).generate()
HOURLYDATEFORMAT = '%Y-%m-%d %H:00:00'
NODATAMESSAGE = 'No data to display. Apply and submit slicers in sidebar first'
DATANOTQUERIEDYET = 'Data not queried yet, nothing to display'
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
    availableDestinations = ['IN', 'OUT']
    sidebar = Sidebar(
        hourlyDatetimeList,
        availableRoads, 
        availableDestinations, 
        todayStr, 
        todayMinus2Str, 
        databaseCredentials, 
        HOURLYDATEFORMAT 
    )
    
    try:
        selectedDatetime, selectedRoads, selectedDestinations, hoursToForecast = sidebar.renderSidebar(option='volume-speed-LOS')
    except:
        st.write(NODATAMESSAGE)
    
    volumeSpeedLOS = VolumeSpeedLOS()
    
    try:
        volumeSpeedLOS.getFilteredCameras(selectedRoad=selectedRoads, databaseCredentials=databaseCredentials)
        volumeSpeedLOS.getFactVolumeSpeed(
            selectedDatetime=selectedDatetime,
            roadSelections=selectedRoads, 
            destinationSelections=selectedDestinations, 
            databaseCredentials=databaseCredentials
        )
        factVolumeSpeedCSV = dataframeToCSV(volumeSpeedLOS.factVolumeSpeed)
    except:
        st.write(NODATAMESSAGE)
    
    volumeDisplayer = VolumeDisplayer(volumeSpeedLOS)
    
    try:
        dfHourlyLOS = volumeSpeedLOS.generateHourlyLOS(selectedDestinations=selectedDestinations)
    except:
        st.write(DATANOTQUERIEDYET)
        
    timeSeriesForecaster = TimeSeriesForecaster(volumeSpeedLOS)
    st.title('Traffic Dashboard')
    st.header('Inbound')

    try:
        heatMapColumn11 ,heatMapColumn12 = st.columns([1, 1.5], gap='large')
        with heatMapColumn11:
            volumeDisplayer.displayOverallVolumeSpeedMetrics(destination='IN')
        with heatMapColumn12:
            volumeDisplayer.displayHeatMap(destination='IN')   
    except:
        st.write(DATANOTQUERIEDYET)
        
    st.header('Outbound')
    
    try:
        heatMapColumn21 , heatMapColumn22 = st.columns([1, 1.5], gap='large')
        with heatMapColumn21:
            volumeDisplayer.displayOverallVolumeSpeedMetrics(destination='OUT')
        with heatMapColumn22:
            volumeDisplayer.displayHeatMap(destination='OUT')
    except:
        st.write(DATANOTQUERIEDYET)
    
    try:    
        volumeDisplayer.displayHourlyVehicleCount()
        volumeDisplayer.displayHourlyLOSInboundOutbound(dfHourlyLOS)
        displayStreetsAndCameras(
            dfHotspotStreets,
            dfInOutKL,
            volumeSpeedLOS.dimCamera
        )
        st.header('Raw Volume-Speed-LOS% Data')
        st.write(volumeSpeedLOS.factVolumeSpeed)
        st.download_button(
            label="Download data as CSV",
            data=factVolumeSpeedCSV,
            file_name='volume_speed_los.csv',
            mime='text/csv'
        )
    except:
        st.write(DATANOTQUERIEDYET)
        
    try:
        timeSeriesForecaster.trainTestSplitData(dfHourlyLOS)
        timeSeriesForecaster.fitPredict()
        timeSeriesForecaster.getForecasts(hoursToForecast=hoursToForecast)
        timeSeriesForecaster.getMetrics()
        timeSeriesDisplayer = TimeSeriesDisplayer(timeSeriesForecaster)
        timeSeriesDisplayer.displayTimeseriesTesting()
        timeSeriesDisplayer.displayTimeseriesForecasting()
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