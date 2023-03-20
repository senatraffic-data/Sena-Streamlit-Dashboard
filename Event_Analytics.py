import streamlit as st

import streamlit_authenticator as stauth

from my_functions import authentication, displayEventAnalytics

from authenticator import Authenticator

from streamlit_authenticator import SafeLoader

import os


def main():
    # hashedPasswords = stauth.Hasher(['senatraffic123']).generate()
    
    DATEFORMAT = '%Y-%m-%d %H:%M:%S'
    
    myAuthenticator = Authenticator()
    userLoginsYamlPath = os.path.join(os.getcwd(), 'user_logins.yaml')   
    streamlitLoader=SafeLoader
    myAuthenticator.authenticate(filePath=userLoginsYamlPath, fileLoader=streamlitLoader)
    
    if myAuthenticator.authenticationStatus:
        displayEventAnalytics(myAuthenticator, 
                              DATEFORMAT)
        
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


if __name__ == '__main__':
    main()