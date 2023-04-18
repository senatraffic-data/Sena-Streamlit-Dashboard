import mysql.connector
from mysql.connector import Error

import pandas as pd

from datetime import datetime, timedelta

import pytz

import streamlit as st

import yaml

from streamlit_authenticator import SafeLoader, Authenticate

from sktime.forecasting.model_selection import temporal_train_test_split

from sktime.forecasting.arima import AutoARIMA

from sktime.forecasting.base import ForecastingHorizon

from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

from sklearn.metrics import mean_squared_error


def _sqlToDataframe(databaseCredentials, query):
    connection = _createConnection(databaseCredentials)
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


def _createConnection(databaseCredentials):
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


# @st.experimental_memo(ttl=600)
@st.cache_data
def dataframeToCSV(df):
    dataframeCSV = df.to_csv()
    dataframeCSVEncoded = dataframeCSV.encode('utf-8')
    
    return dataframeCSVEncoded


def generateHourlyDatetime(dateFormat: str):
    timezone = pytz.timezone("Asia/Kuala_Lumpur")
    today = datetime.now(timezone)
    todayStr = today.strftime(dateFormat)
    todayMinus2 = today - timedelta(days=2)
    todayMinus2Str = todayMinus2.strftime(dateFormat)
    
    hourlyDateRange = pd.date_range(
        start=todayMinus2Str, 
        end=todayStr, 
        freq='H'
    )
    
    return hourlyDateRange, todayStr, todayMinus2Str


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


# @st.cache_data
def mySidebar(
    hourlyDatetimeList, 
    todayStr, 
    todayMinus2Str,
    availableRoads,
    databaseCredentials
):
    with st.sidebar:
        
        with st.form('form 20230322'):
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
            
            submitButton = st.form_submit_button("Submit")
        
            if submitButton:
                dimCamera = getFilteredCameras(selectedRoads, databaseCredentials)
    
    try:        
        return dimCamera, selectedDatetime, selectedRoads, selectedDestinations
    except:
        return None, None, None, None
    
    
@st.cache_data
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
    
    return _sqlToDataframe(databaseCredentials, query1)


def authenticate(filePath='user_logins.yaml', fileLoader=SafeLoader):
    config = _loadConfig(filePath, fileLoader)
    
    streamlitAuthenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    
    name, authenticationStatus, username = streamlitAuthenticator.login('Login', 'main')
    
    return name, authenticationStatus, streamlitAuthenticator


def _loadConfig(filePath, fileLoader):
    with open(filePath) as file:
        config = yaml.load(file, Loader=fileLoader)
        
    return config
    

def renderEventSidebar(temporalSpatialInfo):
    with st.sidebar:
            
        with st.form(key='slicer'):
            hourlyDateRangeLongForm = temporalSpatialInfo['hourlyDatetime'].strftime('%Y-%m-%d %H:00:00')
            hourlyDateRangeShortForm = temporalSpatialInfo['hourlyDatetime'].strftime('%d %b %I %p')

            hourlyDateRangeLongForm = list(hourlyDateRangeLongForm)
            hourlyDateRangeShortForm = list(hourlyDateRangeShortForm)
            
            selectedDatetime = st.select_slider(
                'Timestamp', 
                hourlyDateRangeShortForm,
                value=(hourlyDateRangeShortForm[0], hourlyDateRangeShortForm[-1])
            )
            
            selectedRoads = st.multiselect(
                'Which road you want to view?',
                temporalSpatialInfo['roads'], 
                [temporalSpatialInfo['roads'][0]]
            )
            
            selectedDestinations = st.multiselect(
                'Inbound or Outbound of KL?',
                temporalSpatialInfo['destinations'],
                [temporalSpatialInfo['destinations'][0]]
            )
            
            submitButton = st.form_submit_button("Submit")

            if submitButton:
                return selectedDatetime, selectedRoads, selectedDestinations


@st.cache_data
def getfactEventDataframe(userSlicerSelections, databaseCredentials):
    startTime = datetime.strptime(userSlicerSelections['hourlyDatetime'][0] + ' 2023', '%d %b %I %p %Y')
    endTime = datetime.strptime(userSlicerSelections['hourlyDatetime'][-1] + ' 2023', '%d %b %I %p %Y')

    hourlyList = []
    currentTime = startTime

    while currentTime <= endTime:
        currentTimeString = currentTime.strftime('%Y-%m-%d %H:00:00')
        hourlyList.append(currentTimeString)
        currentTime += timedelta(hours=1)
    
    hourlyDatetimeTuple = tuple(hourlyList)
    eventQuery = _getMainEventQuery(hourlyDatetimeTuple, userSlicerSelections)
    factEvent = _sqlToDataframe(databaseCredentials, eventQuery)
    
    return factEvent


def _getMainEventQuery(hourlyDatetimeTuple, userSlicerSelections) -> str:
    if len(userSlicerSelections['destinations']) == 1:
                    
        if len(userSlicerSelections['roads']) == 1:
            eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type, 
                                                AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                        WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                        ELSE NULL END) AS confidence
                                        FROM dwd_tfc_event_rt AS t1
                                        RIGHT JOIN (SELECT address,
                                                            equipment_id,
                                                            camera_id
                                                    FROM dim_camera_states
                                                    WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                                        ON t1.camera_id = t2.camera_id
                                        WHERE t1.direction = '{userSlicerSelections['destinations'][0]}'
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                        GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type
                                        ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                        ;'''
        elif len(userSlicerSelections['roads']) != 1:
            eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type, 
                                                AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                        WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                        ELSE NULL END) AS confidence
                                        FROM dwd_tfc_event_rt AS t1
                                        RIGHT JOIN (SELECT address,
                                                            equipment_id,
                                                            camera_id
                                                    FROM dim_camera_states
                                                    WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                        ON t1.camera_id = t2.camera_id
                                        WHERE t1.direction = '{userSlicerSelections['destinations'][0]}'
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                        GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type
                                        ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                        ;'''
        else:
            print('Error in road length')
                        
    elif len(userSlicerSelections['destinations']) == 2:
                    
        if len(userSlicerSelections['roads']) == 1:
            eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type, 
                                                AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                        WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                        ELSE NULL END) AS confidence
                                        FROM dwd_tfc_event_rt AS t1
                                        RIGHT JOIN (SELECT address,
                                                            equipment_id,
                                                            camera_id
                                                    FROM dim_camera_states
                                                    WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                                        ON t1.camera_id = t2.camera_id
                                        WHERE t1.direction IN {tuple(userSlicerSelections['destinations'])}
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                        GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type
                                        ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                        ;'''
        elif len(userSlicerSelections['roads']) != 1:
            eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type, 
                                                AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                        WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                        ELSE NULL END) AS confidence
                                        FROM dwd_tfc_event_rt AS t1
                                        RIGHT JOIN (SELECT address,
                                                            equipment_id,
                                                            camera_id
                                                    FROM dim_camera_states
                                                    WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                        ON t1.camera_id = t2.camera_id
                                        WHERE t1.direction IN {tuple(userSlicerSelections['destinations'])}
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                        GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                t2.address,
                                                t2.camera_id,
                                                t1.direction,
                                                t1.zone, 
                                                t1.event_type,
                                                t1.item_type
                                        ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                        ;'''
        else:
            print('Error in road length')
                        
    else:
        print('Error in destination length')
    
    return eventQuery


def renderVolumeSidebar(temporalSpatialInfo):
    with st.sidebar:
            
        with st.form(key='queryDataKey'):
            st.write('Choose your relevant filters below then click "Submit". Will take some time...')
            
            hourlyDateRangeLongForm = temporalSpatialInfo['hourlyDatetime'].strftime('%Y-%m-%d %H:00:00')
            hourlyDateRangeShortForm = temporalSpatialInfo['hourlyDatetime'].strftime('%d %b %I %p')

            hourlyDateRangeLongForm = list(hourlyDateRangeLongForm)
            hourlyDateRangeShortForm = list(hourlyDateRangeShortForm)
            
            selectedDatetime = st.select_slider(
                'Timestamp', 
                hourlyDateRangeShortForm,
                value=(hourlyDateRangeShortForm[0], hourlyDateRangeShortForm[-1])
            )
            
            selectedRoads = st.multiselect(
                'Which road you want to view?', 
                temporalSpatialInfo['roads'], 
                [temporalSpatialInfo['roads'][0]]
            )
            
            selectedDestinations = st.multiselect(
                'Inbound or Outbound of KL?', 
                temporalSpatialInfo['destinations'], 
                [temporalSpatialInfo['destinations'][0]]
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


@st.cache_data
def getFactVolumeSpeed(userSlicerSelections, databaseCredentials):
    startTime = datetime.strptime(userSlicerSelections['hourlyDatetime'][0] + ' 2023', '%d %b %I %p %Y')
    endTime = datetime.strptime(userSlicerSelections['hourlyDatetime'][-1] + ' 2023', '%d %b %I %p %Y')

    hourlyList = []
    currentTime = startTime

    while currentTime <= endTime:
        currentTimeString = currentTime.strftime('%Y-%m-%d %H:00:00')
        hourlyList.append(currentTimeString)
        currentTime += timedelta(hours=1)
        
    hourlyDatetimeTuple = tuple(hourlyList)
    query = _getVolumeSpeedLOSQuery(hourlyDatetimeTuple, userSlicerSelections) 
    factVolumeSpeed = _sqlToDataframe(databaseCredentials, query)
    factVolumeSpeed['datetime'] = pd.to_datetime(factVolumeSpeed['datetime'])
    
    return factVolumeSpeed


def _getVolumeSpeedLOSQuery(hourlyDatetimeTuple, userSlicerSelections) -> str:
    if len(userSlicerSelections['roads']) == 1:
        
        if len(userSlicerSelections['destinations']) == 1:
            query = f'''
                SELECT *,
                    (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                            t2.address,
                            t2.equipment_id,
                            t2.camera_id,
                            t1.destination,
                            LEFT(t1.zone, 3) AS POV,
                            SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                    ELSE 0 END) AS bus_count,
                            SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                    ELSE 0 END) AS car_count,
                            SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                    ELSE 0 END) AS lorry_count,
                            SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                    ELSE 0 END) AS truck_count,
                            SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                    ELSE 0 END) AS van_count,
                            SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                    ELSE 0 END) AS motorbike_count,
                            SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                    ELSE 0 END) AS total_count,
                            AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed ELSE NULL END) AS lane_speed,
                            AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                    ELSE NULL END) AS motor_speed,
                            COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL ELSE t1.zone END)) AS indicator
                    FROM dws_tfc_state_volume_speed_tp AS t1
                    RIGHT JOIN (SELECT address,
                                        equipment_id,
                                        camera_id
                                FROM dim_camera_states
                                WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                    ON t1.camera_id = t2.camera_id
                    WHERE t1.destination = '{userSlicerSelections['destinations'][0]}'
                            AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                    GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                            t2.address,
                            t2.equipment_id,
                            t2.camera_id,
                            t1.destination,
                            LEFT(t1.zone, 3)
                    ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                    ;
            '''
        elif len(userSlicerSelections['destinations']) != 1:
            query = f'''SELECT *,
                            (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3) AS POV,
                                    SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                            ELSE 0 END) AS bus_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                            ELSE 0 END) AS car_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                            ELSE 0 END) AS lorry_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                            ELSE 0 END) AS truck_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                            ELSE 0 END) AS van_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                            ELSE 0 END) AS motorbike_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                            ELSE 0 END) AS total_count,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS lane_speed,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS motor_speed,
                                    COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                        ELSE t1.zone END)) AS indicator
                            FROM dws_tfc_state_volume_speed_tp AS t1
                            RIGHT JOIN (SELECT address,
                                                equipment_id,
                                                camera_id
                                        FROM dim_camera_states
                                        WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                            ON t1.camera_id = t2.camera_id
                            WHERE t1.destination IN {tuple(userSlicerSelections['destinations'])}
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                            GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                            ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        else:
            print('ERROR IN DESTINATION')
        
    elif len(userSlicerSelections['roads']) != 1:
        
        if len(userSlicerSelections['destinations']) == 1:
            query = f'''SELECT *,
                            (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3) AS POV,
                                    SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                            ELSE 0 END) AS bus_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                            ELSE 0 END) AS car_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                            ELSE 0 END) AS lorry_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                            ELSE 0 END) AS truck_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                            ELSE 0 END) AS van_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                            ELSE 0 END) AS motorbike_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                            ELSE 0 END) AS total_count,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS lane_speed,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS motor_speed,
                                    COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                        ELSE t1.zone END)) AS indicator
                            FROM dws_tfc_state_volume_speed_tp AS t1
                            RIGHT JOIN (SELECT address,
                                                equipment_id,
                                                camera_id
                                        FROM dim_camera_states
                                        WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                            ON t1.camera_id = t2.camera_id
                            WHERE t1.destination = '{userSlicerSelections['destinations'][0]}'
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                            GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                            ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        elif len(userSlicerSelections['destinations']) != 1:
            query = f'''SELECT *,
                            (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3) AS POV,
                                    SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                            ELSE 0 END) AS bus_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                            ELSE 0 END) AS car_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                            ELSE 0 END) AS lorry_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                            ELSE 0 END) AS truck_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                            ELSE 0 END) AS van_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                            ELSE 0 END) AS motorbike_count,
                                    SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                            ELSE 0 END) AS total_count,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS lane_speed,
                                    AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                            ELSE NULL END) AS motor_speed,
                                    COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                        ELSE t1.zone END)) AS indicator
                            FROM dws_tfc_state_volume_speed_tp AS t1
                            RIGHT JOIN (SELECT address,
                                                equipment_id,
                                                camera_id
                                        FROM dim_camera_states
                                        WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                            ON t1.camera_id = t2.camera_id
                            WHERE t1.destination IN {tuple(userSlicerSelections['destinations'])}
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                            GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                            ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        else:
            print('ERROR IN DESTINATION')
        
    else:
        print('ERROR IN ROAD')

    return query


def generateHourlyLOS(factVolumeSpeed, selectedDestinations):
    dfHourlyLOS = factVolumeSpeed.pivot_table(
        values=['LOS'],
        index=['datetime'],
        columns=['destination']
    )
    
    dfHourlyLOS = dfHourlyLOS.asfreq('H').ffill()
    dfHourlyLOSConditioned = _hourlyLOSConditional(dfHourlyLOS, selectedDestinations)
    
    return dfHourlyLOSConditioned


def _hourlyLOSConditional(dfHourlyLOS, selectedDestinations):
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


def trainTestSplitData(dfHourlyLOS):
    yEndogenous = dfHourlyLOS.loc[: , ['IN']]
    yEndogenous.index.name = ""
    yEndogenous.columns = ['Latest Observed Data']
    
    yTrain, yTest = temporal_train_test_split(yEndogenous, test_size=0.3)
    
    yTrain.index.name = ""
    yTrain.columns = ['Training Data']
    
    yTest.index.name = ""
    yTest.columns = ['Test Data']
    
    return yTrain, yTest, yEndogenous


def fitPredict(yTrain, yTest):
    fh = ForecastingHorizon(yTest.index, is_relative=False)
    
    forecaster = AutoARIMA()
    forecaster.fit(yTrain)
    
    yPred = forecaster.predict(fh=fh)
    yPred.index.name = ""
    yPred.columns = ['Prediction']
    
    predictionInterval = forecaster.predict_interval(fh=fh)
    
    yCombined = pd.concat([yTrain, yTest, yPred], axis=1)
    
    return yPred, yCombined, predictionInterval, forecaster


def getForecasts(hoursToForecast, fittedForecaster, yEndogenous):
    lastObservedDatetime = yEndogenous.index[-1]
    offsetDatetime = lastObservedDatetime + timedelta(hours=1) 
    
    dateRange = pd.date_range(
        start=offsetDatetime, 
        periods=hoursToForecast, 
        freq='H'
    )
    
    fh1 = ForecastingHorizon(dateRange, is_relative=False)
    
    yForecast = fittedForecaster.predict(fh=fh1)
    yForecast.index.name = ''
    yForecast.columns = ['Forecast']
    
    predictionIntevalForecast = fittedForecaster.predict_interval(fh=fh1)
    
    yCombinedForecast = pd.concat([yEndogenous, yForecast], axis=1)
    
    return yCombinedForecast, predictionIntevalForecast


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
    
    return mape, mse