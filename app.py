import streamlit as st

import streamlit_authenticator as stauth

from my_functions import authentication, show_content


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

hashed_passwords = stauth.Hasher(['senatraffic123']).generate()

authenticator, name, authentication_status, username = authentication()

if authentication_status:
    show_content(authenticator, name, DATE_FORMAT)
    
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