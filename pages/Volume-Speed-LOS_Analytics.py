import os

import streamlit as st

from authenticator import Authenticator

from my_functions import displayVolumeSpeedLOSAnalytics, authentication

from streamlit_authenticator import SafeLoader

# import streamlit_authenticator as stauth


HOSTNAME = st.secrets.mysql.HOSTNAME
USERNAME = st.secrets.mysql.USERNAME
USERPASSWORD = st.secrets.mysql.USERPASSWORD
DATABASENAME = st.secrets.mysql.DATABASENAME

# hashedPasswords = stauth.Hasher(['senatraffic123']).generate()

myAuthenticator = Authenticator()
userLoginsYamlPath = os.path.join(os.getcwd(), 'user_logins.yaml')   
streamlitLoader=SafeLoader
myAuthenticator.authenticate(filePath=userLoginsYamlPath, fileLoader=streamlitLoader)

if myAuthenticator.authenticationStatus:
    displayVolumeSpeedLOSAnalytics(myAuthenticator, 
                                   HOSTNAME, 
                                   USERNAME, 
                                   USERPASSWORD, 
                                   DATABASENAME)

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