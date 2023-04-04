import os

import pandas as pd

import streamlit as st

from authenticator import Authenticator

from my_functions import dataframeToCSV, displayStreetsAndCameras, generateHourlyDatetime

from streamlit_authenticator import SafeLoader

from sidebar import VolumeSidebar

from timeseries_displayer import TimeSeriesDisplayer
from timeseries_forecaster import TimeSeriesForecaster
from volume_displayer import VolumeDisplayer

from volume_speed_los import VolumeSpeedLOS

# import streamlit_authenticator as stauth


myAuthenticator = Authenticator()
USERS_YAML_PATH = 'user_logins.yaml'
userLoginsYamlPath = os.path.join(os.getcwd(), USERS_YAML_PATH)   
streamlitLoader=SafeLoader
myAuthenticator.authenticate(filePath=userLoginsYamlPath, fileLoader=streamlitLoader)

if myAuthenticator.authenticationStatus:
    myAuthenticator.streamlitAuthenticator.logout('Logout', 'main')
    st.write(f'Welcome *{myAuthenticator.name}*')
    st.title('Traffic Dashboard')
    
    st.header('Quick Links')
    st.markdown("[Inbound Metrics](#inbound)")
    st.markdown("[Outbound Metrics](#outbound)")
    st.markdown("[Hourly Vehicle Count](#hourly-vehicle-count)")
    st.markdown("[Hourly LOS % Plot](#hourly-los-plot)")
    st.markdown("[Important Streets](#important-streets)")
    st.markdown("[Cameras In Selected Road](#cameras-in-selected-road)")
    st.markdown("[Raw Volume-Speed-LOS% Data](#raw-volume-speed-los-data)")
    st.markdown("[Time-Series Model Testing](#time-series-model-testing)")
    st.markdown("[Forecasting](#forecasting)")
    
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
    hourlyDateRange, todayStr, todayMinus2Str = generateHourlyDatetime(HOURLY_DATETIME_FORMAT)
    
    temporalSpatialInfo = {
        'hourlyDatetime': hourlyDateRange, 
        'roads': availableRoads, 
        'destinations': availableDestinations, 
        'today': todayStr, 
        'todayMinus2': todayMinus2Str, 
        'hourlyDatetimeFormat': HOURLY_DATETIME_FORMAT
    }
    
    sidebar = VolumeSidebar(temporalSpatialInfo)
    
    try:
        selectedDatetime, selectedRoads, selectedDestinations, hoursToForecast = sidebar.renderSidebar()
        
        userSlicerSelections = {
            'hourlyDatetime': selectedDatetime, 
            'roads': selectedRoads, 
            'destinations': selectedDestinations,
            'hourlyDatetimeFormat': HOURLY_DATETIME_FORMAT,
        }
    except:
        st.write(NO_DATA_MESSAGE)
    
    volumeSpeedLOS = VolumeSpeedLOS()
    
    try:
        volumeSpeedLOS.getFilteredCameras(userSlicerSelections['roads'], databaseCredentials)
        volumeSpeedLOS.getFactVolumeSpeed(userSlicerSelections, databaseCredentials)
        factVolumeSpeedCSV = dataframeToCSV(volumeSpeedLOS.factVolumeSpeed)
    except:
        st.write(NO_DATA_MESSAGE)
    
    try:
        dfHourlyLOS = volumeSpeedLOS.generateHourlyLOS(userSlicerSelections['destinations'])
    except:
        st.write(NO_DATA_MESSAGE)
    
    volumeDisplayer = VolumeDisplayer(volumeSpeedLOS)
    
    st.header('Inbound')

    try:
        heatMapColumn11 ,heatMapColumn12 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn11:
            volumeDisplayer.displayOverallVolumeSpeedMetrics(destination='IN')
            
        with heatMapColumn12:
            volumeDisplayer.displayHeatMap(destination='IN')   
    except:
        st.write(NO_DATA_MESSAGE)
        
    st.header('Outbound')
    
    try:
        heatMapColumn21 , heatMapColumn22 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn21:
            volumeDisplayer.displayOverallVolumeSpeedMetrics(destination='OUT')
            
        with heatMapColumn22:
            volumeDisplayer.displayHeatMap(destination='OUT')
    except:
        st.write(NO_DATA_MESSAGE)
    
    try:    
        volumeDisplayer.displayHourlyVehicleCount()
        volumeDisplayer.displayHourlyLOSInboundOutbound(dfHourlyLOS)
       
        displayStreetsAndCameras(
            dfHotspotStreets,
            dfInOutKL,
            volumeSpeedLOS.dimCamera
        )
        
        st.header('Raw Volume-Speed-LOS Data')
        st.write(volumeSpeedLOS.factVolumeSpeed)
        
        st.download_button(
            label="Download data as CSV",
            data=factVolumeSpeedCSV,
            file_name='volume_speed_los.csv',
            mime='text/csv'
        )
    except:
        st.write(NO_DATA_MESSAGE)
    
    timeSeriesForecaster = TimeSeriesForecaster()
    
    try:
        timeSeriesForecaster.trainTestSplitData(dfHourlyLOS)
        timeSeriesForecaster.fitPredict()
        timeSeriesForecaster.getForecasts(hoursToForecast)
        timeSeriesForecaster.getMetrics()
        
        timeSeriesDisplayer = TimeSeriesDisplayer(timeSeriesForecaster)
        timeSeriesDisplayer.displayTimeseriesTesting()
        timeSeriesDisplayer.displayTimeseriesForecasting()
    except:
        st.write(NO_DATA_MESSAGE)

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