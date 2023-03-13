from my_functions import sql_to_df

import streamlit as st

HOST_NAME = st.secrets.mysql.HOST_NAME
USER_NAME = st.secrets.mysql.USER_NAME
USER_PASSWORD = st.secrets.mysql.USER_PASSWORD
DB_NAME = st.secrets.mysql.DB_NAME

my_query = f'''SELECT *
               FROM dim_camera_states
               LIMIT 10
               ;'''

df = sql_to_df(HOST_NAME, USER_NAME, USER_PASSWORD, DB_NAME, my_query)

print(df)