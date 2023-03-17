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


def get_data(host_name, db_name, user_name, user_password, query, trueness=True):
    mydb = mysql.connector.connect(host=host_name,
                                   database=db_name,
                                   user=user_name,
                                   password=user_password,
                                   use_pure=trueness)

    return pd.read_sql(query, mydb)


# @st.cache_resource
def create_connection(host_name, user_name, user_password, db_name):
    connection = None

    try:
        connection = mysql.connector.connect(host=host_name,
                                             user=user_name,
                                             passwd=user_password,
                                             database=db_name)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def sql_to_df(host_name, user_name, user_password, db_name, query):
    connection = create_connection(host_name, user_name, user_password, db_name)
    cursor = connection.cursor()
    result = None
    column_names = None

    try:
        cursor.execute(query)
        result = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        connection.close()
        print("Data queried")
    except Error as e:
        connection.close()
        print(f"The error '{e}' occurred")

    df = pd.DataFrame(result, columns=column_names)

    return df


def five_min_ly(time):
    minute_part = str(math.floor(time.minute / 5) * 5).zfill(2)
    hour_part = str(time.hour).zfill(2)
    modified_time = datetime.strptime(f'{hour_part}:{minute_part}', '%H:%M').time()

    return modified_time


def extract_hour(time):
    return time.hour


def distinct_non_null_count(x):
    pandas_unique = pd.unique(x)
    unique_values = [element for element in pandas_unique if element != 'null']

    return len(unique_values)


@st.cache_data
def get_fact_volume_speed(road_selections, 
                          destination_selections, 
                          host_name_main, 
                          user_name_main, 
                          user_password_main, 
                          db_name_main, 
                          selected_datetime_main):
    date_format = '%Y-%m-%d %H:%M:%S'
    hourly_datetime = pd.date_range(start=selected_datetime_main[0], 
                                    end=selected_datetime_main[-1], 
                                    freq='H').strftime(date_format)
    hourly_datetime_tuple = tuple(hourly_datetime)

    query = get_volume_speed_los_query(road_selections, 
                                       destination_selections, 
                                       hourly_datetime_tuple) 
    fact_volume_speed = sql_to_df(host_name_main, 
                                  user_name_main,
                                  user_password_main, 
                                  db_name_main, 
                                  query)
    fact_volume_speed['datetime'] = pd.to_datetime(fact_volume_speed['datetime'])

    return fact_volume_speed


# @st.experimental_memo(ttl=600)
@st.cache_data
def df_to_csv(df):
    return df.to_csv().encode('utf-8')


def authentication():

    with open('user_logins.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = Authenticate(config['credentials'],
                                 config['cookie']['name'],
                                 config['cookie']['key'],
                                 config['cookie']['expiry_days'],
                                 config['preauthorized'])

    name, authentication_status, username = authenticator.login('Login', 'main')

    return authenticator, name, authentication_status, username


def generate_hourly_datetime(date_format):
    HOURLY_DATE_FORMAT = '%Y-%m-%d %H:00:00'
    timezone = pytz.timezone("Asia/Kuala_Lumpur")
    today = datetime.now(timezone)
    today_str = today.strftime(HOURLY_DATE_FORMAT)
    today_minus_2 = today - timedelta(days=2)
    today_minus_2_str = today_minus_2.strftime(HOURLY_DATE_FORMAT)
    hourly_date_range = pd.date_range(start=today_minus_2_str, end=today_str, freq='H').strftime(date_format)
    hourly_datetime_list = list(hourly_date_range)

    return hourly_datetime_list, today_str, today_minus_2_str


def get_filtered_cameras(selected_road,
                         host_name,
                         user_name,
                         user_password,
                         database_name):

    if len(selected_road) != 1:
        query_1 = f'''SELECT *
                      FROM dim_camera_states AS t1
                      WHERE address IN {tuple(selected_road)}
                      ;'''
    elif len(selected_road) == 1:
        query_1 = f'''SELECT *
                      FROM dim_camera_states AS t1
                      WHERE address = '{selected_road[0]}'
                      ;'''
    else:
        raise ValueError

    dim_camera = sql_to_df(host_name,
                           user_name,
                           user_password,
                           database_name,
                           query_1)

    return dim_camera


def get_fact_events_df(date_format,
                       selected_datetime,
                       selected_road,
                       selected_dest,
                       host_name,
                       user_name,
                       user_password,
                       database_name):
    hourly_datetime = pd.date_range(start=selected_datetime[0],
                                    end=selected_datetime[-1],
                                    freq='H').strftime(date_format)
    hourly_datetime_tuple = tuple(hourly_datetime)

    event_query = get_main_event_query(selected_dest, 
                                       selected_road, 
                                       hourly_datetime_tuple)
    fact_events = sql_to_df(host_name,
                            user_name,
                            user_password,
                            database_name,
                            event_query)

    return fact_events


def display_event_analytics(authenticator, name, date_format):
    authenticator.logout('Logout', 'main')

    NO_DATA_MESSAGE = 'No data to display. Apply and submit slicers in sidebar first'

    hourly_datetime_list, today_str, today_minus_2_str = generate_hourly_datetime(date_format)

    st.write(f'Welcome *{name}*')

    HOST_NAME = st.secrets.mysql.HOST_NAME
    USER_NAME = st.secrets.mysql.USER_NAME
    USER_PASSWORD = st.secrets.mysql.USER_PASSWORD
    DB_NAME = st.secrets.mysql.DB_NAME
    DATA_PATH = os.path.join(os.getcwd(),
                             'data',
                             'Important_Roads.xlsx')

    df_hotspot_streets = pd.read_excel(DATA_PATH, sheet_name='Hotspot Congestion')
    df_in_out_kl = pd.read_excel(DATA_PATH, sheet_name='InOut KL Traffic')
    available_roads = tuple(df_hotspot_streets['road'].values)

    event_count_string = 'Event Counts'

    with st.sidebar:

        with st.form(key='slicer'):
            selected_road = st.multiselect('Which road you want to view?',
                                            available_roads, 
                                            [available_roads[0]])
            selected_datetime = st.select_slider('Timestamp', 
                                                  hourly_datetime_list,
                                                  value=(today_minus_2_str, today_str))
            selected_dest = st.multiselect('Inbound or Outbound of KL?',
                                           ['IN', 'OUT'],
                                           ['IN'])
            submit_button = st.form_submit_button("Submit")

            if submit_button:
                dim_camera = get_filtered_cameras(selected_road,
                                                  HOST_NAME,
                                                  USER_NAME,
                                                  USER_PASSWORD,
                                                  DB_NAME)

                fact_events = get_fact_events_df(date_format,
                                                 selected_datetime,
                                                 selected_road,
                                                 selected_dest,
                                                 HOST_NAME,
                                                 USER_NAME,
                                                 USER_PASSWORD,
                                                 DB_NAME)
                fact_events_csv = df_to_csv(fact_events)

    st.write("Streamlit version:", st.__version__)

    st.title('Traffic Dashboard')

    try:
        display_overall_metrics(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_streets_and_cameras(df_hotspot_streets,
                                    df_in_out_kl,
                                    dim_camera)
    except:
        st.write(NO_DATA_MESSAGE)

    st.header('Raw Event Data')
    try:
        st.write(fact_events)
        st.download_button(label="Download data as CSV",
                           data=fact_events_csv,
                           file_name='event_raw_data.csv',
                           mime='text/csv')
    except NameError:
        st.write(NO_DATA_MESSAGE)

    try:
        display_event_count_by_camera_id(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_treemap(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_event_count_by_lane(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_detection_confidence_by_event_and_item_type(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_hourly_detection_confidence(fact_events)
    except:
        st.write(NO_DATA_MESSAGE)

    try:
        display_hourly_event_count(fact_events, selected_dest, event_count_string)
    except:
        st.write(NO_DATA_MESSAGE)


def display_volume_speed_los_analytics(authenticator,
                                       host_name,
                                       user_name,
                                       user_password,
                                       db_name):
    authenticator.logout('Logout', 'main')

    HOURLY_DATE_FORMAT = '%Y-%m-%d %H:00:00'
    hourly_datetime_list, today_str, today_minus_2_str = generate_hourly_datetime(HOURLY_DATE_FORMAT)

    DATA_PATH = os.path.join(os.getcwd(), 'data', 'Important_Roads.xlsx')
    df_hotspot_streets = pd.read_excel(DATA_PATH, sheet_name='Hotspot Congestion')
    df_in_out_kl = pd.read_excel(DATA_PATH, sheet_name='InOut KL Traffic')
    available_roads = tuple(df_hotspot_streets['road'].values)

    with st.sidebar:

        with st.form(key='queryDataKey'):
            st.write('Choose your relevant filters below then click "Submit". Will take some time...')

            selected_road = st.multiselect('Which road you want to view?', available_roads, [available_roads[0]])
            selected_datetime = st.select_slider('Timestamp', hourly_datetime_list, value=(today_minus_2_str, today_str))
            selected_dest = st.multiselect('Inbound or Outbound of KL?', ['IN', 'OUT'], ['IN'])

            day_to_forecast = st.slider('How many days you want to forecast ahead?', 1, 7, 1)
            hour_to_forecast = day_to_forecast*24

            submit_button = st.form_submit_button("Submit")

            if submit_button:
                dim_camera = get_filtered_cameras(selected_road,
                                                  host_name,
                                                  user_name,
                                                  user_password,
                                                  db_name)

                fact_volume_speed = get_fact_volume_speed(selected_road, 
                                                selected_dest,
                                                host_name, 
                                                user_name, 
                                                user_password, 
                                                db_name, 
                                                selected_datetime)
                fact_volume_speed_csv = df_to_csv(fact_volume_speed)

                df_hourly_los = get_hourly_los(fact_volume_speed, selected_dest)

                y_endogenous = df_hourly_los.loc[: , ['IN']]
                y_endogenous.index.name = ""
                y_endogenous.columns = ['Latest Observed Data']

                y_train, y_test = temporal_train_test_split(y_endogenous, test_size=0.3)

                y_train.index.name = ""
                y_train.columns = ['Training Data']
                y_test.index.name = ""
                y_test.columns = ['Test Data']

                y_pred, prediction_interval, y_combined, forecaster = get_predictions(y_train, y_test)

                last_observed_datetime = y_endogenous.index[-1]
                offset_datetime = last_observed_datetime + timedelta(hours=1) 
                date_range = pd.date_range(start=offset_datetime, 
                                           periods=hour_to_forecast, 
                                           freq='H')

                y_forecast, pred_int_forecast, y_combined_forecast = get_forecasts(forecaster, 
                                                                                   y_endogenous, 
                                                                                   date_range)

                y_s = [y_train, y_test,
                       y_pred, prediction_interval, y_combined,
                       y_forecast, pred_int_forecast, y_combined_forecast,
                       y_endogenous]

                metrics = get_metrics(y_test, y_pred)

    DATA_NOT_QUERIED_YET = 'Data not queried yet, nothing to display'

    st.title('Traffic Dashboard')

    try:
        display_overall_volume_speed_metrics(fact_volume_speed)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_streets_and_cameras(df_hotspot_streets,
                                    df_in_out_kl,
                                    dim_camera)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    st.header('Raw Volume-Speed-LOS% Data')
    try:
        st.write(fact_volume_speed)
        st.download_button(label="Download data as CSV",
                           data=fact_volume_speed_csv,
                           file_name='volume_speed_los.csv',
                           mime='text/csv')
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_hourly_vehicle_count(fact_volume_speed)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_hourly_los_inbound_outbound(df_hourly_los)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_timeseries_testing(forecaster, metrics, y_s)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_timeseries_forecasting(y_s)
    except:
        st.write(DATA_NOT_QUERIED_YET)

    try:
        display_heatmap(fact_volume_speed, dim_camera)
    except:
        st.write(DATA_NOT_QUERIED_YET)


def get_hourly_los(fact_volume_speed, selected_dest):
    df_hourly_los = fact_volume_speed.pivot_table(values=['LOS'],
                                                  index=['datetime'],
                                                  columns=['destination'])
    df_hourly_los = df_hourly_los.asfreq('H')
    df_hourly_los = df_hourly_los.ffill()

    df_hourly_los_conditioned = hourly_los_conditional(df_hourly_los, selected_dest)

    return df_hourly_los_conditioned


def hourly_los_conditional(df_hourly_los, selected_dest):

    if len(selected_dest) == 1:

        if df_hourly_los.shape[-1] == 1:
            df_hourly_los.columns = [selected_dest[0]]
        elif df_hourly_los.shape[-1] == 2:
            df_hourly_los.columns = ['TEST', selected_dest[0]]
            df_hourly_los = df_hourly_los.drop(columns=['TEST'])
        else:
            st.write('ERROR IN LENGTH 1')

    elif len(selected_dest) != 1:

        if df_hourly_los.shape[-1] == 2:
            df_hourly_los.columns = [selected_dest[0], selected_dest[-1]]
        elif df_hourly_los.shape[-1] == 3:
            df_hourly_los.columns = ['TEST', selected_dest[0], selected_dest[-1]]
            df_hourly_los = df_hourly_los.drop(columns=['TEST'])
        else:
            st.write('ERROR IN LENGTH 2')

    else:
        st.write('ERROR IN DESTINATION LENGTH')

    return df_hourly_los


def get_metrics(y_test, y_pred):
    mape = mean_absolute_percentage_error(y_test,
                                          y_pred,
                                          symmetric=False)
    mse = mean_squared_error(y_test,
                             y_pred,
                             squared=False)

    return [mape, mse]


def get_predictions(y_train, y_test):
    fh = ForecastingHorizon(y_test.index, is_relative=False)

    forecaster = AutoARIMA()
    forecaster.fit(y_train)

    y_pred = forecaster.predict(fh=fh)
    y_pred.index.name = ""
    y_pred.columns = ['Prediction']

    prediction_interval = forecaster.predict_interval(fh=fh)

    y_combined = pd.concat([y_train, y_test, y_pred], axis=1)

    return y_pred, prediction_interval, y_combined, forecaster


def get_forecasts(forecaster, y_endogenous, date_range):
    fh_1 = ForecastingHorizon(date_range, is_relative=False)

    y_forecast = forecaster.predict(fh=fh_1)
    y_forecast.index.name = ''
    y_forecast.columns = ['Forecast']

    pred_int_forecast = forecaster.predict_interval(fh=fh_1)

    y_combined_forecast = pd.concat([y_endogenous, y_forecast], axis=1)

    return y_forecast, pred_int_forecast, y_combined_forecast