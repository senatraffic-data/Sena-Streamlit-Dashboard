from matplotlib import pyplot as plt

import streamlit as st

import plotly.express as px


def displayTimeseriesTesting(
    forecaster, 
    yCombined,
    predictionInterval, 
    mape,
    mse
):
    st.header('Time-Series Model Testing')
    
    st.write(forecaster.summary())
    st.write(f'The testing MAPE is {mape}')
    st.write(f'The testing MSE is {mse}')
    st.write(yCombined['Prediction'])
    
    figForecast, axForecast = plt.subplots(1, 1)
    yCombined['Training Data'].plot(
        kind='line', 
        ax=axForecast,
        title=r'Hourly LOS% For Train, Testing, and Prediction',
        ylabel='LOS %'
    )
    yCombined['Test Data'].plot(kind='line', ax=axForecast)
    yCombined['Prediction'].plot(kind='line', ax=axForecast)
    plt.fill_between(
        predictionInterval.index,
        predictionInterval.loc[: , ('Coverage', 0.9, 'lower')],
        predictionInterval.loc[: , ('Coverage', 0.9, 'upper')],
        alpha=0.25
    )
    axForecast.legend()
    plt.tight_layout()
    st.pyplot(figForecast)
    
    plotlyFigHourlyLOSTrainTest = px.line(
        yCombined,
        template="plotly_dark",
        title=r'Hourly LOS% For Train, Testing, and Prediction'
    )
    plotlyFigHourlyLOSTrainTest.update_layout(yaxis_title='LOS%')
    st.plotly_chart(
        plotlyFigHourlyLOSTrainTest,
        use_container_width=True,
        sharing="streamlit",
        theme=None
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write('Testing Data')
        st.write(yCombined['Test Data'])
        
    with col2:
        st.write('Predictions')
        st.write(yCombined['Prediction'])
        
    with col3:
        st.write('Confidence Interval')
        st.write(predictionInterval)


def displayTimeseriesForecasting(
    yCombinedForecast,
    predictionIntevalForecast, 
    yEndogenous
):
    st.header('Forecasting')
    
    figForecastAlt, axForecastAlt = plt.subplots(1, 1)
    
    yEndogenous.plot(
        kind='line',
        ax=axForecastAlt,
        title=r'Hourly LOS% For Observed Data & Forecast',
        ylabel='LOS %'
    )
    
    yCombinedForecast['Forecast'].plot(kind='line', ax=axForecastAlt)
    
    plt.fill_between(
        predictionIntevalForecast.index,
        predictionIntevalForecast.loc[: , ('Coverage', 0.9, 'lower')],
        predictionIntevalForecast.loc[: , ('Coverage', 0.9, 'upper')],
        alpha=0.25
    )
    
    axForecastAlt.legend()
    plt.tight_layout()
    st.pyplot(figForecastAlt)
    
    plotlyFigHourlyLOSForecast = px.line(
        yCombinedForecast, 
        template="plotly_dark",
        title=r'Hourly LOS% For Observed Data & Forecast'
    )
    
    plotlyFigHourlyLOSForecast.update_layout(yaxis_title='LOS%')
    
    st.plotly_chart(
        plotlyFigHourlyLOSForecast,
        use_container_width=True,
        sharing="streamlit",
        theme=None
    )
    
    col1Alt, col2Alt, col3Alt = st.columns(3)
    
    with col1Alt:
        st.write('All Observed Data')
        st.write(yEndogenous)
        
    with col2Alt:
        st.write('Forecasted Values')
        st.write(yCombinedForecast['Forecast'])
        
    with col3Alt:
        st.write('Confidence Interval')
        st.write(predictionIntevalForecast)