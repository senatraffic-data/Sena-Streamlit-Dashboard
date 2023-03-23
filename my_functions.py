import mysql.connector
from mysql.connector import Error

import pandas as pd

from datetime import datetime, timedelta

import pytz

import streamlit as st

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


# @st.experimental_memo(ttl=600)
@st.cache_data
def dataframeToCSV(df):
    return df.to_csv().encode('utf-8')


def generateHourlyDatetime(dateFormat: str):
    timezone = pytz.timezone("Asia/Kuala_Lumpur")
    today = datetime.now(timezone)
    todayStr = today.strftime(dateFormat)
    todayMinus2 = today - timedelta(days=2)
    todayMinus2Str = todayMinus2.strftime(dateFormat)
    hourlyDateRange = pd.date_range(start=todayMinus2Str, end=todayStr, freq='H').strftime(dateFormat)
    hourlyDatetimeList = list(hourlyDateRange)
    return hourlyDatetimeList, todayStr, todayMinus2Str


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
    databaseCredentials, 
    option: str
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