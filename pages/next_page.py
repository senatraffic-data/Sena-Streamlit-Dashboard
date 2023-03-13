import streamlit as st

from my_functions import show_content_second_page, authentication

import streamlit_authenticator as stauth


HOST_NAME = st.secrets.mysql.HOST_NAME
USER_NAME = st.secrets.mysql.USER_NAME
USER_PASSWORD = st.secrets.mysql.USER_PASSWORD
DB_NAME = st.secrets.mysql.DB_NAME

hashed_passwords = stauth.Hasher(['senatraffic123']).generate()

authenticator, name, authentication_status, username = authentication()

if authentication_status:
    show_content_second_page(authenticator, HOST_NAME, USER_NAME, USER_PASSWORD, DB_NAME)

    ## Use the below if-else block for a more personalized experience for different users (privilege based on username)
    ## Commented out for now
    # if username == 'jsmith':
    #     st.write(f'Welcome *{name}*')
    #     st.title('Application 1')
    # elif username == 'rbriggs':
    #     st.write(f'Welcome *{name}*')
    #     st.title('Application 2')
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')