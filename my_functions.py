import os

import mysql.connector
from mysql.connector import Error

import pandas as pd

from datetime import datetime, timedelta

import math

import pytz

import streamlit as st

from streamlit_authenticator import SafeLoader, Authenticate

from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.arima import AutoARIMA
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

import yaml

from sklearn.metrics import mean_squared_error

from long_functions import get_volume_speed_los_query, get_main_event_query

from displayMetrics import *


def getData(hostName, databaseName, userName, userPassword, query, trueness=True):
    mydb = mysql.connector.connect(host=hostName,
                                   database=databaseName,
                                   user=userName,
                                   password=userPassword,
                                   use_pure=trueness)

    return pd.read_sql(query, mydb)


# @st.cache_resource
def createConnection(hostName, userName, userPassword, databaseName):
    connection = None

    try:
        connection = mysql.connector.connect(host=hostName,
                                             user=userName,
                                             passwd=userPassword,
                                             database=databaseName)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def sqlToDataframe(hostName, userName, userPassword, databaseName, query):
    connection = createConnection(hostName, userName, userPassword, databaseName)
    cursor = connection.cursor()
    result = None
    columnNames = None

    try:
        cursor.execute(query)
        result = cursor.fetchall()
        columnNames = [description[0] for description in cursor.description]
        connection.close()
        print("Data queried")
    except Error as e:
        connection.close()
        print(f"The error '{e}' occurred")

    df = pd.DataFrame(result, columns=columnNames)

    return df


def fiveMinLy(time):
    minutePart = str(math.floor(time.minute / 5) * 5).zfill(2)
    hourPart = str(time.hour).zfill(2)
    modifiedTime = datetime.strptime(f'{hourPart}:{minutePart}', '%H:%M').time()

    return modifiedTime


def extractHour(time):
    return time.hour


def distinctNonNullCount(x):
    pandasUnique = pd.unique(x)
    uniqueValues = [element for element in pandasUnique if element != 'null']

    return len(uniqueValues)


@st.cache_data
def getFactVolumeSpeed(roadSelections, 
                       destinationSelections, 
                       hostName, 
                       userName, 
                       userPassword, 
                       databaseName, 
                       selectedDatetime):
    dateFormat = '%Y-%m-%d %H:%M:%S'
    hourlyDatetime = pd.date_range(start=selectedDatetime[0], 
                                   end=selectedDatetime[-1], 
                                   freq='H').strftime(dateFormat)
    hourlyDatetimeTuple = tuple(hourlyDatetime)

    query = get_volume_speed_los_query(roadSelections, 
                                       destinationSelections, 
                                       hourlyDatetimeTuple) 
    factVolumeSpeed = sqlToDataframe(hostName, 
                                     userName,
                                     userPassword, 
                                     databaseName, 
                                     query)
    factVolumeSpeed['datetime'] = pd.to_datetime(factVolumeSpeed['datetime'])

    return factVolumeSpeed


# @st.experimental_memo(ttl=600)
@st.cache_data
def dataframeToCSV(df):
    return df.to_csv().encode('utf-8')


def authentication():

    with open('user_logins.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = Authenticate(config['credentials'],
                                 config['cookie']['name'],
                                 config['cookie']['key'],
                                 config['cookie']['expiry_days'],
                                 config['preauthorized'])

    name, authenticationStatus, username = authenticator.login('Login', 'main')

    return authenticator, name, authenticationStatus, username


def generateHourlyDatetime(dateFormat):
    HOURLYDATEFORMAT = '%Y-%m-%d %H:00:00'
    timezone = pytz.timezone("Asia/Kuala_Lumpur")
    today = datetime.now(timezone)
    todayStr = today.strftime(HOURLYDATEFORMAT)
    todayMinus2 = today - timedelta(days=2)
    todayMinus2Str = todayMinus2.strftime(HOURLYDATEFORMAT)
    hourlyDateRange = pd.date_range(start=todayMinus2Str, end=todayStr, freq='H').strftime(dateFormat)
    hourlyDatetimeList = list(hourlyDateRange)

    return hourlyDatetimeList, todayStr, todayMinus2Str


def getFilteredCameras(selectedRoad,
                       hostName,
                       userName,
                       userPassword,
                       databaseName):
    if len(selectedRoad) != 1:
        query1 = f'''SELECT *
                      FROM dim_camera_states AS t1
                      WHERE address IN {tuple(selectedRoad)}
                      ;'''
    elif len(selectedRoad) == 1:
        query1 = f'''SELECT *
                      FROM dim_camera_states AS t1
                      WHERE address = '{selectedRoad[0]}'
                      ;'''
    else:
        raise ValueError

    dimCamera = sqlToDataframe(hostName,
                           userName,
                           userPassword,
                           databaseName,
                           query1)

    return dimCamera


def getfactEventDataframe(dateFormat,
                          selectedDatetime,
                          selectedRoad,
                          selectedDestinations,
                          hostName,
                          userName,
                          userPassword,
                          databaseName):
    hourlyDatetime = pd.date_range(start=selectedDatetime[0],
                                    end=selectedDatetime[-1],
                                    freq='H').strftime(dateFormat)
    hourlyDatetimeTuple = tuple(hourlyDatetime)

    eventQuery = get_main_event_query(selectedDestinations, 
                                       selectedRoad, 
                                       hourlyDatetimeTuple)
    factEvent = sqlToDataframe(hostName,
                                userName,
                                userPassword,
                                databaseName,
                                eventQuery)

    return factEvent


def displayEventAnalytics(myAuthenticator, dateFormat):
    myAuthenticator.streamlitAuthenticator.logout('Logout', 'main')
    
    st.write(f'Welcome *{myAuthenticator.name}*')
    
    NODATAMESSAGE = 'No data to display. Apply and submit slicers in sidebar first'

    hourlyDatetimeList, todayStr, todayMinus2Str = generateHourlyDatetime(dateFormat)

    HOSTNAME = st.secrets.mysql.HOSTNAME
    USERNAME = st.secrets.mysql.USERNAME
    USERPASSWORD = st.secrets.mysql.USERPASSWORD
    DATABASENAME = st.secrets.mysql.DATABASENAME
    DATAPATH = os.path.join(os.getcwd(),
                            'data',
                            'Important_Roads.xlsx')

    dfHotspotStreets = pd.read_excel(DATAPATH, sheet_name='Hotspot Congestion')
    dfInOutKL = pd.read_excel(DATAPATH, sheet_name='InOut KL Traffic')
    availableRoads = tuple(dfHotspotStreets['road'].values)

    eventCountString = 'Event Counts'

    with st.sidebar:

        with st.form(key='slicer'):
            selectedRoads = st.multiselect('Which road you want to view?',
                                            availableRoads, 
                                            [availableRoads[0]])
            selectedDatetime = st.select_slider('Timestamp', 
                                                  hourlyDatetimeList,
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

    st.write("Streamlit version:", st.__version__)

    st.title('Traffic Dashboard')

    try:
        displayOverallMetrics(factEvent)
    except:
        st.write(NODATAMESSAGE)
        
    try:
        displayEventCountByCameraID(factEvent)
    except:
        st.write(NODATAMESSAGE)

    try:
        displayTreemap(factEvent)
    except:
        st.write(NODATAMESSAGE)

    try:
        displayEventCountByLane(factEvent)
    except:
        st.write(NODATAMESSAGE)

    try:
        displayDetectionConfidenceByEventAndItemType(factEvent)
    except:
        st.write(NODATAMESSAGE)

    try:
        displayHourlyDetectionConfidence(factEvent)
    except:
        st.write(NODATAMESSAGE)

    try:
        displayHourlyEventCount(factEvent, selectedDestinations, eventCountString)
    except:
        st.write(NODATAMESSAGE)
    
    try:
        displayStreetsAndCameras(dfHotspotStreets,
                                    dfInOutKL,
                                    dimCamera)
    except:
        st.write(NODATAMESSAGE)

    st.header('Raw Event Data')
    try:
        st.write(factEvent)
        st.download_button(label="Download data as CSV",
                           data=factEventCSV,
                           file_name='event_raw_data.csv',
                           mime='text/csv')
    except NameError:
        st.write(NODATAMESSAGE)


def displayVolumeSpeedLOSAnalytics(myAuthenticator,
                                   hostName,
                                   userName,
                                   userPassword,
                                   databaseName):
    myAuthenticator.streamlitAuthenticator.logout('Logout', 'main')
    
    st.write(f'Welcome *{myAuthenticator.name}*')

    HOURLYDATEFORMAT = '%Y-%m-%d %H:00:00'
    hourlyDatetimeList, todayStr, todayMinus2Str = generateHourlyDatetime(HOURLYDATEFORMAT)

    DATAPATH = os.path.join(os.getcwd(), 'data', 'Important_Roads.xlsx')
    dfHotspotStreets = pd.read_excel(DATAPATH, sheet_name='Hotspot Congestion')
    dfInOutKL = pd.read_excel(DATAPATH, sheet_name='InOut KL Traffic')
    availableRoads = tuple(dfHotspotStreets['road'].values)

    with st.sidebar:

        with st.form(key='queryDataKey'):
            st.write('Choose your relevant filters below then click "Submit". Will take some time...')

            selectedRoads = st.multiselect('Which road you want to view?', availableRoads, [availableRoads[0]])
            selectedDatetime = st.select_slider('Timestamp', hourlyDatetimeList, value=(todayMinus2Str, todayStr))
            selectedDestinations = st.multiselect('Inbound or Outbound of KL?', ['IN', 'OUT'], ['IN'])

            daysToForecast = st.slider('How many days you want to forecast ahead?', 1, 7, 1)
            hoursToForecast = daysToForecast * 24

            submitButton = st.form_submit_button("Submit")

            if submitButton:
                dimCamera = getFilteredCameras(selectedRoads,
                                                  hostName,
                                                  userName,
                                                  userPassword,
                                                  databaseName)

                factVolumeSpeed = getFactVolumeSpeed(selectedRoads, 
                                                selectedDestinations,
                                                hostName, 
                                                userName, 
                                                userPassword, 
                                                databaseName, 
                                                selectedDatetime)
                factVolumeSpeedCSV = dataframeToCSV(factVolumeSpeed)

                dfHourlyLOS = getHourlyLOS(factVolumeSpeed, selectedDestinations)

                yEndogenous = dfHourlyLOS.loc[: , ['IN']]
                yEndogenous.index.name = ""
                yEndogenous.columns = ['Latest Observed Data']

                yTrain, yTest = temporal_train_test_split(yEndogenous, test_size=0.3)

                yTrain.index.name = ""
                yTrain.columns = ['Training Data']
                yTest.index.name = ""
                yTest.columns = ['Test Data']

                yPred, predictionInterval, yCombined, forecaster = getPredictions(yTrain, yTest)

                lastObservedDatetime = yEndogenous.index[-1]
                offsetDatetime = lastObservedDatetime + timedelta(hours=1) 
                dateRange = pd.date_range(start=offsetDatetime, 
                                           periods=hoursToForecast, 
                                           freq='H')

                yForecast, predictionIntervalForecast, yCombinedForecast = getForecasts(forecaster, 
                                                                                   yEndogenous, 
                                                                                   dateRange)

                y_list = [yTrain, yTest,
                          yPred, predictionInterval, yCombined,
                          yForecast, predictionIntervalForecast, yCombinedForecast,
                          yEndogenous]

                metrics = getMetrics(yTest, yPred)

    DATANOTQUERIEDYET = 'Data not queried yet, nothing to display'

    st.title('Traffic Dashboard')
    
    st.header('Inbound')
    
    try:
        heatMapColumn11 ,heatMapColumn12 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn11:
            displayOverallVolumeSpeedMetrics(factVolumeSpeed)
        with heatMapColumn12:
            displayHeatMap(factVolumeSpeed, dimCamera)   
    except:
        st.write(DATANOTQUERIEDYET)
        
    st.header('Outbound')
    
    try:
        heatMapColumn21 , heatMapColumn22 = st.columns([1, 1.5], gap='large')
        
        with heatMapColumn21:
            displayOverallVolumeSpeedMetrics(factVolumeSpeed)
        with heatMapColumn22:
            displayHeatMap(factVolumeSpeed, dimCamera)
    except:
        st.write(DATANOTQUERIEDYET)
    
    try:    
        displayHourlyVehicleCount(factVolumeSpeed)
    except:
        st.write(DATANOTQUERIEDYET)
        
    try:
        displayHourlyLOSInboundOutbound(dfHourlyLOS)
    except:
        st.write(DATANOTQUERIEDYET)

    try:
        displayStreetsAndCameras(dfHotspotStreets,
                                    dfInOutKL,
                                    dimCamera)
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
        displayTimeseriesTesting(forecaster, metrics, y_list)
    except:
        st.write(DATANOTQUERIEDYET)

    try:
        displayTimeseriesForecasting(y_list)
    except:
        st.write(DATANOTQUERIEDYET)


def getHourlyLOS(factVolumeSpeed, selectedDestinations):
    dfHourlyLOS = factVolumeSpeed.pivot_table(values=['LOS'],
                                                  index=['datetime'],
                                                  columns=['destination'])
    dfHourlyLOS = dfHourlyLOS.asfreq('H')
    dfHourlyLOS = dfHourlyLOS.ffill()

    dfHourlyLOSConditioned = hourlyLOSConditional(dfHourlyLOS, selectedDestinations)

    return dfHourlyLOSConditioned


def hourlyLOSConditional(dfHourlyLOS, selectedDestinations):

    if len(selectedDestinations) == 1:

        if dfHourlyLOS.shape[-1] == 1:
            dfHourlyLOS.columns = [selectedDestinations[0]]
        elif dfHourlyLOS.shape[-1] == 2:
            dfHourlyLOS.columns = ['TEST', selectedDestinations[0]]
            dfHourlyLOS = dfHourlyLOS.drop(columns=['TEST'])
        else:
            st.write('ERROR IN LENGTH 1')

    elif len(selectedDestinations) != 1:

        if dfHourlyLOS.shape[-1] == 2:
            dfHourlyLOS.columns = [selectedDestinations[0], selectedDestinations[-1]]
        elif dfHourlyLOS.shape[-1] == 3:
            dfHourlyLOS.columns = ['TEST', selectedDestinations[0], selectedDestinations[-1]]
            dfHourlyLOS = dfHourlyLOS.drop(columns=['TEST'])
        else:
            st.write('ERROR IN LENGTH 2')

    else:
        st.write('ERROR IN DESTINATION LENGTH')

    return dfHourlyLOS


def getMetrics(yTest, yPred):
    mape = mean_absolute_percentage_error(yTest,
                                          yPred,
                                          symmetric=False)
    mse = mean_squared_error(yTest,
                             yPred,
                             squared=False)

    return [mape, mse]


def getPredictions(yTrain, yTest):
    fh = ForecastingHorizon(yTest.index, is_relative=False)

    forecaster = AutoARIMA()
    forecaster.fit(yTrain)

    yPred = forecaster.predict(fh=fh)
    yPred.index.name = ""
    yPred.columns = ['Prediction']

    predictionInterval = forecaster.predict_interval(fh=fh)

    yCombined = pd.concat([yTrain, yTest, yPred], axis=1)

    return yPred, predictionInterval, yCombined, forecaster


def getForecasts(forecaster, yEndogenous, dateRange):
    fh1 = ForecastingHorizon(dateRange, is_relative=False)

    yForecast = forecaster.predict(fh=fh1)
    yForecast.index.name = ''
    yForecast.columns = ['Forecast']

    predictionIntevalForecast = forecaster.predict_interval(fh=fh1)

    yCombinedForecast = pd.concat([yEndogenous, yForecast], axis=1)

    return yForecast, predictionIntevalForecast, yCombinedForecast