from matplotlib import pyplot as plt
import numpy as np

import pandas as pd

import streamlit as st

import plotly.express as px

from my_functions import dataframeToCSV


def displayOverallMetrics(factEvent):
        st.header('Overall Metrics')
        
        totalNumberOfEvents = factEvent.shape[0]
        eventCountByEventType = factEvent.groupby('event_type')['camera_id'].count()
        availableEvents = list(eventCountByEventType.index)
        numberOfAvailableEvents = len(availableEvents)
        eventCountValues = eventCountByEventType.values
        
        st.metric(label='Total Number of Events', value=totalNumberOfEvents)
        
        eventColumns = st.columns(numberOfAvailableEvents)

        for i, (eventName, eventCount) in enumerate(zip(availableEvents, eventCountValues)):
            eventColumns[i].metric(label=eventName, value=eventCount)

        confidenceByEventType = factEvent.groupby('event_type')['confidence'].mean().dropna()
        eventsWithConfidence = list(confidenceByEventType.index)
        confidenceValues = confidenceByEventType.values
        numberOfEventsWithConfidence = len(eventsWithConfidence)
        
        confidenceColumns = st.columns(numberOfEventsWithConfidence)

        for i, (eventName, event_confidence) in enumerate(zip(eventsWithConfidence, confidenceValues)):
            confidenceColumns[i].metric(
                label=f'**{eventName}** Detection Confidence', 
                value=f'{event_confidence * 100 : .2f} %'
            )
            

def displayEventCountByCameraID(factEvent):
    st.header('Event Counts per Camera ID')

    eventCountByCameraID = pd.crosstab(factEvent['camera_id'], factEvent['event_type'])

    leftColumn2, rightColumn2 = st.columns(2)

    with leftColumn2:
        st.bar_chart(factEvent['camera_id'].value_counts(dropna=False))

    with rightColumn2:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(1, 1)
        
        eventCountByCameraID.plot(
            kind='barh', 
            stacked=True, 
            ax=ax
        )
        
        st.pyplot(fig)

    eventCountString = 'Event Counts'

    plotlyFigEventCountByCameraID = px.bar(
        eventCountByCameraID, 
        orientation='v',
        labels={
            'index': 'Camera ID',
            'value': eventCountString
        }
    )

    st.plotly_chart(
        plotlyFigEventCountByCameraID, 
        use_container_width=True,
        sharing="streamlit", 
        theme=None
    )

    st.write(eventCountByCameraID)
    eventCountByCameraIDCSV = dataframeToCSV(eventCountByCameraID)

    st.download_button(
        label="Download data as CSV",
        data=eventCountByCameraIDCSV,
        file_name='event_count_by_camera_id.csv',
        mime='text/csv'
    )


def displayTreemap(factEvent):
    st.header('Event Count per Lane Treemap')
    
    eventCountByLane = factEvent.groupby(['event_type', 'zone'], as_index=False)\
                                .agg({'camera_id': 'count'})
                        
    eventCountByLaneCSV = dataframeToCSV(eventCountByLane)
    
    treemapFig = px.treemap(
        eventCountByLane,
        path=[eventCountByLane['event_type'], eventCountByLane['zone']],
        values=eventCountByLane['camera_id'],
        width=500,
        height=750
    )
    
    st.plotly_chart(treemapFig, use_container_width=True)
    st.write(eventCountByLane)
    
    st.download_button(
        label="Download data as CSV",
        data=eventCountByLaneCSV,
        file_name='event_count_by_zone_lane.csv',
        mime='text/csv'
    )
    

def displayEventCountByLane(factEvent):
    st.header('Event Count By Lanes')
    
    b2tLaneFilter = factEvent['zone'].str.startswith('b2t')
    t2bLaneFilter = factEvent['zone'].str.startswith('t2b')
    
    b2tEvents  = factEvent.loc[b2tLaneFilter]
    t2bEvents = factEvent.loc[t2bLaneFilter]
    
    b2tEventCountByLane = pd.crosstab(
        b2tEvents['zone'], 
        b2tEvents['event_type']
    ).sort_values(by='zone', ascending=False)
    
    t2bEventCountByLane = pd.crosstab(t2bEvents['zone'], t2bEvents['event_type'])
    
    figEventCountByLane, axEventCountByLane = plt.subplots(1, 2)
    
    b2tEventCountByLane.plot(
        kind='bar', 
        stacked=True, 
        ax=axEventCountByLane[0]
    )
    
    t2bEventCountByLane.plot(
        kind='bar', 
        stacked=True, 
        ax=axEventCountByLane[1]
    )
    
    plt.tight_layout()
    st.pyplot(figEventCountByLane)
    
    byLane1, byLane2 = st.columns(2)
        
    with byLane1:
        b2tPlotlyFigEventCountByLane = px.bar(b2tEventCountByLane, orientation='v')
        
        st.plotly_chart(
            b2tPlotlyFigEventCountByLane, 
            use_container_width=True,
            sharing="streamlit", 
            theme=None
        )
        
    with byLane2:
        t2bPlotlyFigEventCountByLane = px.bar(t2bEventCountByLane, orientation='v')
        
        st.plotly_chart(
            t2bPlotlyFigEventCountByLane, 
            use_container_width=True,
            sharing="streamlit", 
            theme=None
        )


def displayDetectionConfidenceByEventAndItemType(factEvent):
    st.header('Event Detection Confidence by Event Type and Item Type')
    
    confidence = pd.crosstab(
        factEvent['event_type'], 
        factEvent['item_type'], 
        factEvent['confidence'], 
        aggfunc=np.mean
    )
    
    figConfidence, axConfidence = plt.subplots(1, 1)
    
    confidencePlot = confidence.plot(
        kind='barh', 
        stacked=False, 
        ax=axConfidence
    )
    
    axConfidence.set_yticklabels(confidence.index, rotation=0)
    axConfidence.legend(loc="upper left")
    axConfidence.set_ylabel('Event Type')
    axConfidence.set_xlabel('Detection Confidence')
    
    for i in confidencePlot.containers:
        labels = [f'{val * 100 :.2f} %' if val > 0 else '' for val in i.datavalues]
        
        axConfidence.bar_label(
            i,
            label_type='edge',
            labels=labels,
            fontsize=10,
            padding=3
        )

    plt.tight_layout()
    st.pyplot(figConfidence)
    confidenceIndexResetted = confidence.reset_index()
    
    plotlyFigEventConfidence = px.bar(
        confidenceIndexResetted, 
        x='event_type',
        y=confidenceIndexResetted.columns[1: ],
        barmode='group',
        orientation='v'
    )
    
    st.plotly_chart(
        plotlyFigEventConfidence, 
        use_container_width=True,
        sharing="streamlit", 
        theme=None
    )


def displayHourlyDetectionConfidence(factEvent):
    st.header('Hourly Detection Confidence')
    
    factEvent['datetime'] = pd.to_datetime(factEvent['datetime'])
    
    dfHourlyConfidence = factEvent.pivot_table(
        values=['confidence'],
        index=['datetime'],
        columns=['event_type'],
        aggfunc={'confidence': np.mean}
    )
    
    dfHourlyConfidence = dfHourlyConfidence.asfreq('H')
    dfHourlyConfidence = dfHourlyConfidence.ffill().rolling(3).mean()
    
    previousColumns = list(dfHourlyConfidence.columns)
    newColumns = [multi_column[-1] for multi_column in previousColumns]
    
    dfHourlyConfidence.columns = newColumns
    dfHourlyConfidence.index.name = ""
    
    figHourlyConfidence, axHourlyConfidence = plt.subplots(1, 1)
    
    dfHourlyConfidence.plot(
        kind='line',
        title=r'Hourly Detection Confidence by Event Type',
        ax=axHourlyConfidence,
        ylabel='Confidence'
    )
    
    st.pyplot(figHourlyConfidence)
    plotlyFigHourlyConfidence = px.line(dfHourlyConfidence)
    plotlyFigHourlyConfidence.update_layout(yaxis_title="Confidence")
    
    st.plotly_chart(
        plotlyFigHourlyConfidence, 
        use_container_width=True,
        sharing="streamlit", 
        theme=None
    )


def displayHourlyEventCount(factEvent, selectedDestinations, eventCountString):
    st.header('Hourly Event Count by Event Type')
    
    factEventInbound = factEvent[factEvent['direction']=='IN']
    factEventOutbound = factEvent[factEvent['direction']=='OUT']
    
    dfHourlyEventCountInbound = pd.crosstab(
        index=factEventInbound['datetime'], 
        columns=factEventInbound['event_type']
    )
    
    dfHourlyEventCountInbound = dfHourlyEventCountInbound.asfreq('H')
    dfHourlyEventCountInbound = dfHourlyEventCountInbound.ffill()
    dfHourlyEventCountInbound.index.name = ''
    
    dfHourlyEventCountOutbound = pd.crosstab(
        index=factEventOutbound['datetime'], 
        columns=factEventOutbound['event_type']
    )
    
    dfHourlyEventCountOutbound = dfHourlyEventCountOutbound.asfreq('H')
    dfHourlyEventCountOutbound = dfHourlyEventCountOutbound.ffill()
    dfHourlyEventCountOutbound.index.name = ''
    
    _singleOrDoubleDestinationPlotting(
        selectedDestinations,
        dfHourlyEventCountInbound,
        dfHourlyEventCountOutbound,
        eventCountString
    )


def _singleOrDoubleDestinationPlotting(
    selectedDestinations, 
    dfHourlyEventCountInbound, 
    dfHourlyEventCountOutbound,
    eventCountString
):
    if ( selectedDestinations == ['IN', 'OUT'] ) or ( selectedDestinations == ['OUT', 'IN'] ):
        inColumn, outColumn = st.columns(2)
            
        with inColumn:
            figHourlyInbound, axHourlyInbound = plt.subplots(1, 1)
            
            dfHourlyEventCountInbound.plot(
                kind='line',
                title='Inbound',
                ax=axHourlyInbound,
                ylabel=eventCountString
            )
            
            st.pyplot(figHourlyInbound)
            
            plotlyFigHourlyCountInbound = px.line(
                dfHourlyEventCountInbound, 
                template="plotly_dark", 
                title='IN-bound'
            )
            
            plotlyFigHourlyCountInbound.update_layout(yaxis_title=eventCountString)
            
            st.plotly_chart(
                plotlyFigHourlyCountInbound, 
                use_container_width=True,
                sharing="streamlit", 
                theme=None
            )
        
        with outColumn:
            figHourlyOutbound, axHourlyOutbound = plt.subplots(1, 1)
            
            dfHourlyEventCountOutbound.plot(
                kind='line',
                title='Outbound',
                ax=axHourlyOutbound
            )
            
            st.pyplot(figHourlyOutbound)
            
            plotlyFigHourlyCountOutbound = px.line(
                dfHourlyEventCountOutbound,
                template="plotly_dark",
                title='OUT-bound'
            )
            
            plotlyFigHourlyCountOutbound.update_layout(yaxis_title='')
            
            st.plotly_chart(
                plotlyFigHourlyCountOutbound,
                use_container_width=True,
                sharing="streamlit",
                theme=None
            )
    elif selectedDestinations == ['IN']:
        figHourlyInbound, axHourlyInbound = plt.subplots(1, 1)
        
        dfHourlyEventCountInbound.plot(
            kind='line',
            title='Inbound',
            ax=axHourlyInbound,
            ylabel=eventCountString
        )
        
        st.pyplot(figHourlyInbound)
        
        plotlyFigHourlyCountInbound = px.line(
            dfHourlyEventCountInbound, 
            template="plotly_dark", 
            title='IN-bound'
        )
        
        plotlyFigHourlyCountInbound.update_layout(yaxis_title=eventCountString)
        
        st.plotly_chart(
            plotlyFigHourlyCountInbound, 
            use_container_width=True,
            sharing="streamlit", 
            theme=None
        )
    elif selectedDestinations == ['OUT']:
        figHourlyOutbound, axHourlyOutbound = plt.subplots(1, 1)
        
        dfHourlyEventCountOutbound.plot(
            kind='line',
            title='Outbound',
            ax=axHourlyOutbound
        )
        
        st.pyplot(figHourlyOutbound)
        
        plotlyFigHourlyCountOutbound = px.line(
            dfHourlyEventCountOutbound,
            template="plotly_dark",
            title='OUT-bound'
        )
        
        plotlyFigHourlyCountOutbound.update_layout(yaxis_title='')
        
        st.plotly_chart(
            plotlyFigHourlyCountOutbound,
            use_container_width=True,
            sharing="streamlit",
            theme=None
        )
    else:
        st.write('ERROR')