import mysql.connector
from mysql.connector import Error

import pandas as pd

from datetime import datetime, timedelta

import pytz

import streamlit as st

from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.arima import AutoARIMA
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

from sklearn.metrics import mean_squared_error

from long_functions import getVolumeSpeedLOSQuery, getMainEventQuery


# @st.cache_resource
def createConnection(databaseCredentials):
    connection = None
    
    try:
        connection = mysql.connector.connect(
            host=databaseCredentials['HOSTNAME'],
            user=databaseCredentials['USERNAME'],
            passwd=databaseCredentials['USERPASSWORD'],
            database=databaseCredentials['DATABASENAME']
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
        
    return connection


def sqlToDataframe(databaseCredentials, query):
    connection = createConnection(databaseCredentials)
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


@st.cache_data
def getFactVolumeSpeed(
    roadSelections, 
    destinationSelections, 
    databaseCredentials, 
    selectedDatetime
):
    dateFormat = '%Y-%m-%d %H:%M:%S'
    
    hourlyDatetime = pd.date_range(
        start=selectedDatetime[0], 
        end=selectedDatetime[-1], 
        freq='H'
    ).strftime(dateFormat)
    
    hourlyDatetimeTuple = tuple(hourlyDatetime)

    query = getVolumeSpeedLOSQuery(
        roadSelections, 
        destinationSelections, 
        hourlyDatetimeTuple
    ) 
    
    factVolumeSpeed = sqlToDataframe(databaseCredentials, query)
    factVolumeSpeed['datetime'] = pd.to_datetime(factVolumeSpeed['datetime'])

    return factVolumeSpeed


# @st.experimental_memo(ttl=600)
@st.cache_data
def dataframeToCSV(df):
    return df.to_csv().encode('utf-8')


def generateHourlyDatetime(dateFormat):
    timezone = pytz.timezone("Asia/Kuala_Lumpur")
    
    today = datetime.now(timezone)
    todayStr = today.strftime(dateFormat)
    todayMinus2 = today - timedelta(days=2)
    todayMinus2Str = todayMinus2.strftime(dateFormat)
    
    hourlyDateRange = pd.date_range(start=todayMinus2Str, end=todayStr, freq='H').strftime(dateFormat)
    hourlyDatetimeList = list(hourlyDateRange)

    return hourlyDatetimeList, todayStr, todayMinus2Str


def getFilteredCameras(selectedRoad, databaseCredentials):
    if len(selectedRoad) != 1:
        query1 = f'''
            SELECT *
            FROM dim_camera_states AS t1
            WHERE address IN {tuple(selectedRoad)}
            ;
        '''
    elif len(selectedRoad) == 1:
        query1 = f'''
            SELECT *
            FROM dim_camera_states AS t1
            WHERE address = '{selectedRoad[0]}'
            ;
        '''
    else:
        raise ValueError

    dimCamera = sqlToDataframe(databaseCredentials, query1)

    return dimCamera


def getfactEventDataframe(
    dateFormat,
    selectedDatetime,
    selectedRoad,
    selectedDestinations,
    databaseCredentials
):
    hourlyDatetime = pd.date_range(
        start=selectedDatetime[0],
        end=selectedDatetime[-1],
        freq='H'
    ).strftime(dateFormat)
    
    hourlyDatetimeTuple = tuple(hourlyDatetime)

    eventQuery = getMainEventQuery(
        selectedDestinations, 
        selectedRoad, 
        hourlyDatetimeTuple
    )
    
    factEvent = sqlToDataframe(databaseCredentials, eventQuery)

    return factEvent


def getHourlyLOS(factVolumeSpeed, selectedDestinations):
    dfHourlyLOS = factVolumeSpeed.pivot_table(
        values=['LOS'],
        index=['datetime'],
        columns=['destination']
    )
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
    mape = mean_absolute_percentage_error(
        yTest,
        yPred,
        symmetric=False
    )
    
    mse = mean_squared_error(
        yTest,
        yPred,
        squared=False
    )

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


def displayStreetsAndCameras(dfHotspotStreets, dfInOutKL, dimCamera):
    st.header('Important Streets')
    leftColumn1, rightColumn1 = st.columns(2)

    with leftColumn1:
        st.subheader('Hot-Spot Streets')
        st.write(dfHotspotStreets)

    with rightColumn1:
        st.subheader('In-Out KL Streets')
        st.write(dfInOutKL)

    st.header('Cameras In Selected Road')
    st.write(dimCamera)
    
    
@st.cache_data
def mySidebar(
    hourlyDatetimeList, 
    todayStr, 
    todayMinus2Str,
    availableRoads,
    databaseCredentials, 
    option: str
):
    if option == 'event':
        
        with st.sidebar:
            
            with st.form('testing form'):
                selectedDatetime = st.select_slider(
                    'Timestamp', 
                    hourlyDatetimeList,
                    value=(todayMinus2Str, todayStr)
                )
                
                selectedRoads = st.multiselect(
                    'Which road you want to view?',
                    availableRoads, 
                    [availableRoads[0]]
                )
                
                selectedDestinations = st.multiselect(
                    'Inbound or Outbound of KL?',
                    ['IN', 'OUT'],
                    ['IN']
                )
        
                submitButton = st.form_submit_button("Submit", use_container_width=True)
                
                if submitButton:
                    dimCamera = getFilteredCameras(selectedRoads, databaseCredentials)
                    
                    return dimCamera, selectedDatetime, selectedRoads, selectedDestinations