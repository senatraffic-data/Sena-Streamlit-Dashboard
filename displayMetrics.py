import streamlit as st

import matplotlib.pyplot as plt

import pandas as pd

import plotly.express as px

import numpy as np

import folium

from streamlit_folium import folium_static

from branca.colormap import LinearColormap


def display_overall_metrics(fact_events):
    st.header('Overall Metrics')

    total_num_events = fact_events.shape[0]
    event_count_by_event_type = fact_events.groupby('event_type')['camera_id'].count()
    available_events = list(event_count_by_event_type.index)
    num_of_available_events = len(available_events)
    event_count_values = event_count_by_event_type.values

    st.metric(label='Total Number of Events', value=total_num_events)

    event_columns = st.columns(num_of_available_events)

    for i, (event_name, event_count) in enumerate(zip(available_events, event_count_values)):
        event_columns[i].metric(label=event_name, value=event_count)

    confidence_by_event_type = fact_events.groupby('event_type')['confidence'].mean().dropna()
    event_with_confidence = list(confidence_by_event_type.index)
    confidence_values = confidence_by_event_type.values
    num_of_events_with_confidence = len(event_with_confidence)

    confidence_columns = st.columns(num_of_events_with_confidence)

    for i, (event_name, event_confidence) in enumerate(zip(event_with_confidence, confidence_values)):
        confidence_columns[i].metric(label=f'**{event_name}** Detection Confidence', 
                                     value=f'{event_confidence * 100 : .2f} %')


def display_streets_and_cameras(df_hotspot_streets, df_in_out_kl, dim_camera):
    st.header('Important Streets')

    left_column_1, right_column_1 = st.columns(2)

    with left_column_1:
        st.subheader('Hot-Spot Streets')
        st.write(df_hotspot_streets)

    with right_column_1:
        st.subheader('In-Out KL Streets')
        st.write(df_in_out_kl)

    st.header('Cameras In Selected Road')

    st.write(dim_camera)


def display_event_count_by_camera_id(fact_events):
    st.header('Event Counts per Camera ID')
    
    event_count_by_cam = pd.crosstab(fact_events['camera_id'], fact_events['event_type'])
    st.write(event_count_by_cam)
    
    left_column_2, right_column_2 = st.columns(2)
    
    with left_column_2:
        st.bar_chart(fact_events['camera_id'].value_counts(dropna=False))
        
    with right_column_2:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(1, 1)
        event_count_by_cam.plot(kind='barh', 
                                stacked=True, 
                                ax=ax)
        st.pyplot(fig)
    
    event_count_string = 'Event Counts'
    plotly_fig_event_count_by_cam = px.bar(fact_events['camera_id'].value_counts(dropna=False), 
                                            orientation='v',
                                            labels={'index': 'Camera ID',
                                                    'value': event_count_string})
    st.plotly_chart(plotly_fig_event_count_by_cam, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)
    
    
def display_treemap(fact_events):
    st.header('Event Counts per Lane/Zone Treemap')
    
    event_count_by_zone_lane = fact_events.groupby(['event_type', 'zone'], as_index=False).agg({'camera_id': 'count'})
    treemap_fig = px.treemap(event_count_by_zone_lane,
                                path=[event_count_by_zone_lane['event_type'], event_count_by_zone_lane['zone']],
                                values=event_count_by_zone_lane['camera_id'],
                                width=500,
                                height=750)
    st.plotly_chart(treemap_fig, use_container_width=True)
    st.write(event_count_by_zone_lane)
    
    
def display_event_count_by_lane(fact_events):
    st.header('Event Count By Lanes')
    
    b2t_lane_filter = fact_events['zone'].str.startswith('b2t')
    t2b_lane_filter = fact_events['zone'].str.startswith('t2b')
    
    b2t_events  =fact_events.loc[b2t_lane_filter]
    t2b_events = fact_events.loc[t2b_lane_filter]
    
    b2t_event_count_by_lane = pd.crosstab(b2t_events['zone'], b2t_events['event_type'])
    t2b_event_count_by_lane = pd.crosstab(t2b_events['zone'], t2b_events['event_type'])
    
    fig_event_count_by_lane, ax_event_count_by_lane = plt.subplots(1, 2)
    
    b2t_event_count_by_lane.plot(kind='bar', 
                                    stacked=True, 
                                    ax=ax_event_count_by_lane[0])
    t2b_event_count_by_lane.plot(kind='bar', 
                                    stacked=True, 
                                    ax=ax_event_count_by_lane[1])
    plt.tight_layout()
    st.pyplot(fig_event_count_by_lane)
    
    by_lane_1, by_lane_2 = st.columns(2)
        
    with by_lane_1:
        plotly_fig_event_count_by_lane_b2t = px.bar(b2t_event_count_by_lane, 
                                                orientation='v')
        st.plotly_chart(plotly_fig_event_count_by_lane_b2t, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)
        
    with by_lane_2:
        plotly_fig_event_count_by_lane_t2b = px.bar(t2b_event_count_by_lane, 
                                                orientation='v')
        st.plotly_chart(plotly_fig_event_count_by_lane_t2b, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)


def display_detection_confidence_by_event_and_item_type(fact_events):
    st.header('Event Detection Confidence by Event Type and Item Type')
    
    confidence = pd.crosstab(fact_events['event_type'], 
                                fact_events['item_type'], 
                                fact_events['confidence'], 
                                aggfunc=np.mean)
    
    fig_confidence, ax_confidence = plt.subplots(1, 1)
    confidence_plot = confidence.plot(kind='barh', 
                                        stacked=False, 
                                        ax=ax_confidence)
    ax_confidence.set_yticklabels(confidence.index, rotation=0)
    ax_confidence.legend(loc="upper left")
    
    for i in confidence_plot.containers:
        labels = [f'{val:.2f}' if val > 0 else '' for val in i.datavalues]
        ax_confidence.bar_label(i, 
                                label_type='edge', 
                                labels=labels, 
                                fontsize=10, 
                                padding=3)
        
    plt.tight_layout()
    st.pyplot(fig_confidence)
    
    confidence_index_resetted = confidence.reset_index()
    plotly_fig_event_confidence = px.bar(confidence_index_resetted, 
                                            x='event_type',
                                            y=confidence_index_resetted.columns[1: ],
                                            barmode='group',
                                            orientation='v')
    st.plotly_chart(plotly_fig_event_confidence, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)


def display_hourly_detection_confidence(fact_events):
    st.header('Hourly Detection Confidence')
    
    fact_events['datetime'] = pd.to_datetime(fact_events['datetime'])
    df_hourly_confidence = fact_events.pivot_table(values=['confidence'],
                                                    index=['datetime'],
                                                    columns=['event_type'],
                                                    aggfunc={'confidence': np.mean})
    df_hourly_confidence = df_hourly_confidence.asfreq('H')
    df_hourly_confidence = df_hourly_confidence.ffill().rolling(3).mean()
    
    previous_columns = list(df_hourly_confidence.columns)
    new_columns = [multi_column[-1] for multi_column in previous_columns]
    df_hourly_confidence.columns = new_columns
    df_hourly_confidence.index.name = ""
    
    fig_hourly_confidence, ax_hourly_confidence = plt.subplots(1, 1)
    df_hourly_confidence.plot(kind='line',
                                title=r'Hourly Detection Confidence by Event Type',
                                ax=ax_hourly_confidence,
                                ylabel='Confidence')
    st.pyplot(fig_hourly_confidence)
    
    plotly_fig_hourly_confidence = px.line(df_hourly_confidence)
    plotly_fig_hourly_confidence.update_layout(yaxis_title="Confidence")
    st.plotly_chart(plotly_fig_hourly_confidence, 
                    use_container_width=True,
                    sharing="streamlit", 
                    theme=None)


def display_hourly_event_count(fact_events, selected_dest, event_count_string):
    st.header('Hourly Event Count by Event Type')
    
    fact_events_in = fact_events[fact_events['direction']=='IN']
    fact_events_out = fact_events[fact_events['direction']=='OUT']
    
    df_hourly_event_count_in = pd.crosstab(index=fact_events_in['datetime'], 
                                            columns=fact_events_in['event_type'])
    df_hourly_event_count_in = df_hourly_event_count_in.asfreq('H')
    df_hourly_event_count_in = df_hourly_event_count_in.ffill()
    df_hourly_event_count_in.index.name = ''
        
    df_hourly_event_count_out = pd.crosstab(index=fact_events_out['datetime'], 
                                            columns=fact_events_out['event_type'])
    df_hourly_event_count_out = df_hourly_event_count_out.asfreq('H')
    df_hourly_event_count_out = df_hourly_event_count_out.ffill()
    df_hourly_event_count_out.index.name = ''
        
    single_or_double_destinations(selected_dest,
                                    df_hourly_event_count_in,
                                    df_hourly_event_count_out,
                                    event_count_string)
    
    
def single_or_double_destinations(selected_dest, 
                                  df_hourly_event_count_in, 
                                  df_hourly_event_count_out,
                                  event_count_string):
    if ( selected_dest == ['IN', 'OUT'] ) or ( selected_dest == ['OUT', 'IN'] ):
        in_column, out_column = st.columns(2)
            
        with in_column:
            fig_hourly_in, ax_hourly_in = plt.subplots(1, 1)
            df_hourly_event_count_in.plot(kind='line',
                                        title='Inbound',
                                        ax=ax_hourly_in,
                                        ylabel=event_count_string)
            st.pyplot(fig_hourly_in)
            
            plotly_fig_hourly_count_in = px.line(df_hourly_event_count_in, 
                                                template="plotly_dark", 
                                                title='IN-bound')
            plotly_fig_hourly_count_in.update_layout(yaxis_title=event_count_string)
            st.plotly_chart(plotly_fig_hourly_count_in, 
                            use_container_width=True,
                            sharing="streamlit", 
                            theme=None)
        
        with out_column:
            fig_hourly_out, ax_hourly_out = plt.subplots(1, 1)
            df_hourly_event_count_out.plot(kind='line',
                                        title='Outbound',
                                        ax=ax_hourly_out)
            st.pyplot(fig_hourly_out)
            
            plotly_fig_hourly_count_out = px.line(df_hourly_event_count_out,
                                                template="plotly_dark",
                                                title='OUT-bound')
            plotly_fig_hourly_count_out.update_layout(yaxis_title='')
            st.plotly_chart(plotly_fig_hourly_count_out,
                            use_container_width=True,
                            sharing="streamlit",
                            theme=None)
    elif selected_dest == ['IN']:
        fig_hourly_in, ax_hourly_in = plt.subplots(1, 1)
        df_hourly_event_count_in.plot(kind='line',
                                        title='Inbound',
                                        ax=ax_hourly_in,
                                        ylabel=event_count_string)
        st.pyplot(fig_hourly_in)
        
        plotly_fig_hourly_count_in = px.line(df_hourly_event_count_in, 
                                                template="plotly_dark", 
                                                title='IN-bound')
        plotly_fig_hourly_count_in.update_layout(yaxis_title=event_count_string)
        st.plotly_chart(plotly_fig_hourly_count_in, 
                        use_container_width=True,
                        sharing="streamlit", 
                        theme=None)
    elif selected_dest == ['OUT']:
        fig_hourly_out, ax_hourly_out = plt.subplots(1, 1)
        df_hourly_event_count_out.plot(kind='line',
                                    title='Outbound',
                                    ax=ax_hourly_out)
        st.pyplot(fig_hourly_out)
        
        plotly_fig_hourly_count_out = px.line(df_hourly_event_count_out,
                                            template="plotly_dark",
                                            title='OUT-bound')
        plotly_fig_hourly_count_out.update_layout(yaxis_title='')
        st.plotly_chart(plotly_fig_hourly_count_out,
                        use_container_width=True,
                        sharing="streamlit",
                        theme=None)
    else:
        st.write('ERROR')
        

def display_overall_volume_speed_metrics(fact_volume_speed):
    st.header('Overall Metrics')
    
    st.subheader('Vehicle Count')
    
    minimum_car_count = int(fact_volume_speed['car_count'].min())
    average_car_count = int(fact_volume_speed['car_count'].mean())
    maximum_car_count = int(fact_volume_speed['car_count'].max())
    
    car_column_1, car_column_2 , car_column_3 = st.columns(3)
    
    with car_column_1:
        st.metric(label='Minimum Car Count', value=minimum_car_count)
        
    with car_column_2:
        st.metric(label='Average Car Count', value=average_car_count)
        
    with car_column_3:
        st.metric(label='Maximum Car Count', value=maximum_car_count)
    
    st.subheader('Lane Speed (km/h)')
    
    descriptions = fact_volume_speed.describe()
    minimum_lane_speed  = round(descriptions.loc['min', 'lane_speed'], 2)
    average_lane_speed = round(descriptions.loc['mean', 'lane_speed'], 2)
    max_lane_speed = round(descriptions.loc['max', 'lane_speed'], 2)
    
    minimum_lane_speed_column, mean_lane_speed_column, max_lane_speed_column = st.columns(3)
    
    with minimum_lane_speed_column:
        st.metric(label='Minimum Lane Speed', value=minimum_lane_speed)
    
    with mean_lane_speed_column:
        st.metric(label='Average Lane Speed', value=average_lane_speed)
    
    with max_lane_speed_column:
        st.metric(label='Maximum Lane Speed', value=max_lane_speed)
    
    st.subheader('LOS (%)')
    
    minimum_los = round(descriptions.loc['min', 'LOS'], 4)
    average_los = round(descriptions.loc['mean', 'LOS'], 4)
    max_los = round(descriptions.loc['max', 'LOS'], 4)
    
    minimum_los_column, mean_los_column, max_los_column = st.columns(3)
    
    with minimum_los_column:
        st.metric(label='Minimum LOS', value=minimum_los)
    
    with mean_los_column:
        st.metric(label='Average LOS', value=average_los)

    with max_los_column:
        st.metric(label='Maximum LOS', value=max_los)
    
    
def display_hourly_vehicle_count(fact_volume_speed):
    st.header('Hourly Vehicle Count')
    
    df_hourly_car_count = fact_volume_speed.pivot_table(values=['car_count'],
                                                        index=['datetime'],
                                                        columns=['POV'])
    df_hourly_car_count.index.name = ""
    df_hourly_car_count.columns = ['b2t', 't2b']
    
    fig_car_count, ax_car_count = plt.subplots(1, 1)
    df_hourly_car_count.plot(kind='line',
                            title=r'Hourly Car Count (b2t & t2b)',
                            ax=ax_car_count,
                            ylabel='Count')
    plt.style.use('dark_background')
    st.pyplot(fig_car_count)
        
    plotly_fig_hourly_car_count = px.line(df_hourly_car_count, 
                                            template="plotly_dark", 
                                            title='Hourly Car Count')
    plotly_fig_hourly_car_count.update_layout(yaxis_title='Car Count')
    st.plotly_chart(plotly_fig_hourly_car_count, 
                    use_container_width=True,   
                    sharing="streamlit", 
                    theme=None)
    
    
def display_hourly_los_inbound_outbound(df_hourly_los):
    st.header('Hourly LOS% Plot for Inbound & Outbound')
    
    df_hourly_los.index.name = ""
    
    fig_time_plot, ax_time_plot = plt.subplots(1, 1)
    df_hourly_los.plot(kind='line',
                    title=r'Hourly LOS% For Inbound & Outbound',
                    ax=ax_time_plot,
                    ylabel='LOS %')
    plt.style.use('dark_background')
    st.pyplot(fig_time_plot)
    
    plotly_fig_hourly_los = px.line(df_hourly_los, 
                                    template="plotly_dark", 
                                    title='Hourly LOS')
    plotly_fig_hourly_los.update_layout(yaxis_title='LOS')
    st.plotly_chart(plotly_fig_hourly_los, 
                    use_container_width=True,   
                    sharing="streamlit", 
                    theme=None)
    
    
def display_timeseries_testing(forecaster, metrics, y_s):
    st.header('Time-Series Model Testing')

    st.write(forecaster.summary())
    st.write(f'The testing MAPE is {metrics[0]}')
    st.write(f'The testing MSE is {metrics[1]}')
    st.write(y_s[2])

    fig_forecast, ax_forecast = plt.subplots(1, 1)
    y_s[0].plot(kind='line', 
                ax=ax_forecast,
                title=r'Hourly LOS% For Train, Testing, and Prediction',
                ylabel='LOS %')
    y_s[1].plot(kind='line', 
                ax=ax_forecast)
    y_s[2].plot(kind='line', 
                ax=ax_forecast)
    plt.fill_between(y_s[3].index,
                        y_s[3].loc[: , ('Coverage', 0.9, 'lower')],
                        y_s[3].loc[: , ('Coverage', 0.9, 'upper')],
                        alpha=0.25)
    ax_forecast.legend()
    plt.tight_layout()
    st.pyplot(fig_forecast)
        
    plotly_fig_hourly_los_train_test = px.line(y_s[4],
                                                template="plotly_dark",
                                                title=r'Hourly LOS% For Train, Testing, and Prediction')
    plotly_fig_hourly_los_train_test.update_layout(yaxis_title='LOS%')
    st.plotly_chart(plotly_fig_hourly_los_train_test,
                    use_container_width=True,
                    sharing="streamlit",
                    theme=None)
        
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write('Testing Data')
        st.write(y_s[1])
        
    with col2:
        st.write('Predictions')
        st.write(y_s[2])
        
    with col3:
        st.write('Confidence Interval')
        st.write(y_s[3])
    
     
def display_timeseries_forecasting(y_s):
    st.header('Forecasting')

    fig_forecast_alt, ax_forecast_alt = plt.subplots(1, 1)
    y_s[-1].plot(kind='line',
                    ax=ax_forecast_alt,
                    title=r'Hourly LOS% For Observed Data & Forecast',
                    ylabel='LOS %')
    y_s[5].plot(kind='line',
                ax=ax_forecast_alt)
    plt.fill_between(y_s[6].index,
                        y_s[6].loc[: , ('Coverage', 0.9, 'lower')],
                        y_s[6].loc[: , ('Coverage', 0.9, 'upper')],
                        alpha=0.25)
    ax_forecast_alt.legend()
    plt.tight_layout()
    st.pyplot(fig_forecast_alt)
    
    plotly_fig_hourly_los_forecast = px.line(y_s[7], 
                                                template="plotly_dark",
                                                title=r'Hourly LOS% For Observed Data & Forecast')
    plotly_fig_hourly_los_forecast.update_layout(yaxis_title='LOS%')
    st.plotly_chart(plotly_fig_hourly_los_forecast,
                    use_container_width=True,
                    sharing="streamlit",
                    theme=None)
    
    col1_alt, col2_alt, col3_alt = st.columns(3)
    
    with col1_alt:
        st.write('All Observed Data')
        st.write(y_s[-1])
        
    with col2_alt:
        st.write('Forecasted Values')
        st.write(y_s[5])
        
    with col3_alt:
        st.write('Confidence Interval')
        st.write(y_s[6])
    
    
def display_heatmap(fact_volume_speed, dim_camera):
    st.header('Heat Map')
    
    merged_metrics_camera = fact_volume_speed.merge(dim_camera, 
                                                    how='left', 
                                                    on='camera_id')
    groupby_cameras = merged_metrics_camera\
                    .groupby(['camera_id', 'latitude', 'longitude'])\
                    .agg({'LOS': np.mean})
    groupby_cameras_index_resetted = groupby_cameras.reset_index()
    subsetted_1 = groupby_cameras_index_resetted[['camera_id', 'latitude', 'longitude', 'LOS']].dropna()
    subsetted = subsetted_1[['latitude', 'longitude', 'LOS']]
    camera_ids = subsetted_1['camera_id'].values
    
    # Define the center of the map
    center = subsetted.values[0, 0: 2]

    # Create a folium map
    m = folium.Map(location=center, 
                zoom_start=12, 
                tiles='OpenStreetMap')
    # Add the updated layer to the map
    layer = folium.FeatureGroup(name='Updated Layer')

    # Add coordinates to the layer
    coordinates = np.array(subsetted.values, dtype=np.float64)
    
    # Define a color map
    min_los = np.nanmin(coordinates[: , -1])
    median_los = np.nanmedian(coordinates[: , -1])
    max_los = np.nanmax(coordinates[: , -1])
    index = [min_los, median_los, max_los]
    index_sorted = sorted(index)
    colormap = LinearColormap(colors=['green', 'yellow', 'red'], 
                            index=index_sorted, 
                            vmin=0.0, 
                            vmax=150.0)
        
    # Add bubbles to the layer with color based on value
    for cam_id, coord in zip(camera_ids, coordinates):
        radius = coord[-1] # Use the value as the radius
        folium.CircleMarker(location=coord[0: 2], 
                            radius=radius, 
                            color=colormap(coord[-1]),
                            fill=True, 
                            fill_color=colormap(coord[-1]),
                            tooltip=f'<b>Camera ID: {cam_id} | LOS %: {coord[-1]: .2f}</b>').add_to(layer)

    # Add the layer to the map
    layer.add_to(m)

    # Display the map in Streamlit
    folium_static(m)