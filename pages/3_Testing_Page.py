import os

import pandas as pd

import streamlit as st

from authenticator import Authenticator

from my_functions import mySidebar

from my_functions import generateHourlyDatetime

from streamlit_authenticator import SafeLoader


HOURLYDATEFORMAT = '%Y-%m-%d %H:00:00'
NODATAMESSAGE = 'No data to display. Apply and submit slicers in sidebar first'
DATANOTQUERIEDYET = 'Data not queried yet, nothing to display'
eventCountString = 'Event Counts'
hourlyDatetimeList, todayStr, todayMinus2Str = generateHourlyDatetime(HOURLYDATEFORMAT)

myAuthenticator = Authenticator()
userLoginsYamlPath = os.path.join(os.getcwd(), 'user_logins.yaml')   
streamlitLoader=SafeLoader
myAuthenticator.authenticate(filePath=userLoginsYamlPath, fileLoader=streamlitLoader)

if myAuthenticator.authenticationStatus:
    myAuthenticator.streamlitAuthenticator.logout('Logout', 'main')
    st.write(f'Welcome *{myAuthenticator.name}*')

    databaseCredentials = {
        'HOSTNAME': st.secrets.mysql.HOSTNAME,
        'USERNAME': st.secrets.mysql.USERNAME,
        'USERPASSWORD': st.secrets.mysql.USERPASSWORD,
        'DATABASENAME': st.secrets.mysql.DATABASENAME
    }
    
    DATAPATH = os.path.join(
        os.getcwd(), 
        'data', 
        'Important_Roads.xlsx'
    )
    
    dfHotspotStreets = pd.read_excel(DATAPATH, sheet_name='Hotspot Congestion')
    dfInOutKL = pd.read_excel(DATAPATH, sheet_name='InOut KL Traffic')
    availableRoads = tuple(dfHotspotStreets['road'].values)

    dimCamera, selectedDatetime, selectedRoads, selectedDestinations = mySidebar(
        hourlyDatetimeList, 
        todayStr, 
        todayMinus2Str,
        availableRoads,
        databaseCredentials, 
        option='event'
    )
        
    st.title('Traffic Dashboard')
    
    leftColumn, rightColumn = st.columns([1, 1.5], gap='medium')
    
    with leftColumn:
        
        with st.form(key='testing slicer'):
            
            try:
                cameraIDs = dimCamera['camera_id']
                firstAvailableCamera = cameraIDs[0]
                    
                userSelectedCameras = st.multiselect(
                    'Available Camera ID in This Address',
                    cameraIDs, 
                    [firstAvailableCamera]
                )
            except:
                st.write(NODATAMESSAGE)
        
            submitButton = st.form_submit_button("Submit")

            if submitButton:
                cameraCondition = dimCamera['address'].isin(userSelectedCameras)
                filteredDimCamera = dimCamera.loc[cameraCondition]

    with rightColumn:
        
        try:
            st.write(filteredDimCamera)
        except:
            st.write(NODATAMESSAGE)