import os

import pandas as pd

import streamlit as st

from my_functions import (
    authenticate,
    dataframeToCSV, 
    displayStreetsAndCameras,
    fitPredict, 
    generateHourlyDatetime,
    generateHourlyLOS,
    getFactVolumeSpeed,
    getFilteredCameras,
    getForecasts,
    getMetrics,
    renderVolumeSidebar,
    trainTestSplitData
)

from streamlit_authenticator import SafeLoader

from time_series_displayer_functions import (
    displayTimeseriesForecasting, 
    displayTimeseriesTesting
)

from volume_displayer_functions import (
    displayHeatMap, 
    displayHourlyLOSInboundOutbound, 
    displayHourlyVehicleCount, 
    displayOverallVolumeSpeedMetrics
)


USERS_YAML_PATH = 'user_logins.yaml'
userLoginsYamlPath = os.path.join(os.getcwd(), USERS_YAML_PATH)   
streamlitLoader=SafeLoader
name, authenticationStatus, streamlitAuthenticator = authenticate(
    filePath=userLoginsYamlPath, 
    fileLoader=streamlitLoader
)

if authenticationStatus:
    streamlitAuthenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}*')
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
    
    try:
        selectedDatetime, selectedRoads, selectedDestinations, hoursToForecast = renderVolumeSidebar(temporalSpatialInfo)
        
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
        factVolumeSpeed = getFactVolumeSpeed(userSlicerSelections, databaseCredentials)
        factVolumeSpeedCSV = dataframeToCSV(factVolumeSpeed)
    except:
        st.write(NO_DATA_MESSAGE)
    
    try:
        dfHourlyLOS = generateHourlyLOS(factVolumeSpeed, userSlicerSelections['destinations'])
    except:
        st.write(NO_DATA_MESSAGE)
    
    st.header('Inbound')

    try:
        heatMapColumn11 ,heatMapColumn12 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn11:
            displayOverallVolumeSpeedMetrics(factVolumeSpeed, destination='IN')
            
        with heatMapColumn12:
            displayHeatMap(factVolumeSpeed, dimCamera, destination='IN')   
    except:
        st.write(NO_DATA_MESSAGE)
        
    st.header('Outbound')
    
    try:
        heatMapColumn21 , heatMapColumn22 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn21:
            displayOverallVolumeSpeedMetrics(factVolumeSpeed, destination='OUT')
            
        with heatMapColumn22:
            displayHeatMap(factVolumeSpeed, dimCamera, destination='OUT')   
    except:
        st.write(NO_DATA_MESSAGE)
    
    try:    
        displayHourlyVehicleCount(factVolumeSpeed)
        displayHourlyLOSInboundOutbound(dfHourlyLOS)
       
        displayStreetsAndCameras(
            dfHotspotStreets,
            dfInOutKL,
            dimCamera
        )
        
        st.header('Raw Volume-Speed-LOS Data')
        st.write(factVolumeSpeed)
        
        st.download_button(
            label="Download data as CSV",
            data=factVolumeSpeedCSV,
            file_name='volume_speed_los.csv',
            mime='text/csv'
        )
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        yTrain, yTest, yEndogenous = trainTestSplitData(dfHourlyLOS)
        yPred, yCombined, predictionInterval, fittedForecaster = fitPredict(yTrain, yTest)
        yCombinedForecast, predictionIntevalForecast = getForecasts(hoursToForecast, fittedForecaster, yEndogenous)
        
        mape, mse = getMetrics(yTest, yPred)
        
        displayTimeseriesTesting(
            fittedForecaster, 
            yCombined,
            predictionInterval, 
            mape,
            mse
        )
        
        displayTimeseriesForecasting(
            yCombinedForecast,
            predictionIntevalForecast, 
            yEndogenous
        )
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
elif authenticationStatus == False:
    st.error('Username/password is incorrect')
elif authenticationStatus == None:
    st.warning('Please enter your username and password')