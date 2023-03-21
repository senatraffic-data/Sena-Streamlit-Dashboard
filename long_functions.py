import streamlit as st


@st.cache_data
def getMainEventQuery(selected_dest, selected_road, hourly_datetime_tuple):
    if len(selected_dest) == 1:
                    
        if len(selected_road) == 1:
            event_query = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                 t2.address,
                                                 t2.camera_id,
                                                 t1.direction,
                                                 t1.zone, 
                                                 t1.event_type,
                                                 t1.item_type, 
                                                 AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                          WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                          ELSE NULL END) AS confidence
                                          FROM dwd_tfc_event_rt AS t1
                                          RIGHT JOIN (SELECT address,
                                                             equipment_id,
                                                             camera_id
                                                      FROM dim_camera_states
                                                      WHERE address = '{selected_road[0]}') AS t2
                                          ON t1.camera_id = t2.camera_id
                                          WHERE t1.direction = '{selected_dest[0]}'
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                                          GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                   t2.address,
                                                   t2.camera_id,
                                                   t1.direction,
                                                   t1.zone, 
                                                   t1.event_type,
                                                   t1.item_type
                                          ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                          ;'''
        elif len(selected_road) != 1:
            event_query = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                 t2.address,
                                                 t2.camera_id,
                                                 t1.direction,
                                                 t1.zone, 
                                                 t1.event_type,
                                                 t1.item_type, 
                                                 AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                          WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                          ELSE NULL END) AS confidence
                                          FROM dwd_tfc_event_rt AS t1
                                          RIGHT JOIN (SELECT address,
                                                             equipment_id,
                                                             camera_id
                                                      FROM dim_camera_states
                                                      WHERE address IN {tuple(selected_road)}) AS t2
                                          ON t1.camera_id = t2.camera_id
                                          WHERE t1.direction = '{selected_dest[0]}'
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                                          GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                   t2.address,
                                                   t2.camera_id,
                                                   t1.direction,
                                                   t1.zone, 
                                                   t1.event_type,
                                                   t1.item_type
                                          ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                          ;'''
        else:
            print('Error in road length')
                        
    elif len(selected_dest) == 2:
                    
        if len(selected_road) == 1:
            event_query = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                 t2.address,
                                                 t2.camera_id,
                                                 t1.direction,
                                                 t1.zone, 
                                                 t1.event_type,
                                                 t1.item_type, 
                                                 AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                          WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                          ELSE NULL END) AS confidence
                                          FROM dwd_tfc_event_rt AS t1
                                          RIGHT JOIN (SELECT address,
                                                             equipment_id,
                                                             camera_id
                                                      FROM dim_camera_states
                                                      WHERE address = '{selected_road[0]}') AS t2
                                          ON t1.camera_id = t2.camera_id
                                          WHERE t1.direction IN {tuple(selected_dest)}
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                                          GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                   t2.address,
                                                   t2.camera_id,
                                                   t1.direction,
                                                   t1.zone, 
                                                   t1.event_type,
                                                   t1.item_type
                                          ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                          ;'''
        elif len(selected_road) != 1:
            event_query = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                                 t2.address,
                                                 t2.camera_id,
                                                 t1.direction,
                                                 t1.zone, 
                                                 t1.event_type,
                                                 t1.item_type, 
                                                 AVG(CASE WHEN t1.event_type = 'person_on_lane' THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"conf":', -1), ',', 1) AS DECIMAL(5, 4))
                                                          WHEN t1.event_type IN ('illegal_stop', 'accident') THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t1.description, '"confidence":', -1), ',', 1) AS DECIMAL(5,                                           4))
                                                          ELSE NULL END) AS confidence
                                          FROM dwd_tfc_event_rt AS t1
                                          RIGHT JOIN (SELECT address,
                                                             equipment_id,
                                                             camera_id
                                                      FROM dim_camera_states
                                                      WHERE address IN {tuple(selected_road)}) AS t2
                                          ON t1.camera_id = t2.camera_id
                                          WHERE t1.direction IN {tuple(selected_dest)}
                                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                                          GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                   t2.address,
                                                   t2.camera_id,
                                                   t1.direction,
                                                   t1.zone, 
                                                   t1.event_type,
                                                   t1.item_type
                                          ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                          ;'''
        else:
            print('Error in road length')
                        
    else:
        print('Error in destination length')
    
    return event_query


@st.cache_data
def getVolumeSpeedLOSQuery(
    road_selections, 
    destination_selections, 
    hourly_datetime_tuple
):
    if len(road_selections) == 1:
        
        if len(destination_selections) == 1:
            query = f'''
                SELECT *,
                       (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                             t2.address,
                             t2.equipment_id,
                             t2.camera_id,
                             t1.destination,
                             LEFT(t1.zone, 3) AS POV,
                             SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                      ELSE 0 END) AS bus_count,
                             SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                      ELSE 0 END) AS car_count,
                             SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                      ELSE 0 END) AS lorry_count,
                             SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                      ELSE 0 END) AS truck_count,
                             SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                      ELSE 0 END) AS van_count,
                             SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                      ELSE 0 END) AS motorbike_count,
                             SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                      ELSE 0 END) AS total_count,
                             AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed ELSE NULL END) AS lane_speed,
                             AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                      ELSE NULL END) AS motor_speed,
                             COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL ELSE t1.zone END)) AS indicator
                      FROM dws_tfc_state_volume_speed_tp AS t1
                      RIGHT JOIN (SELECT address,
                                         equipment_id,
                                         camera_id
                                  FROM dim_camera_states
                                  WHERE address = '{road_selections[0]}') AS t2
                      ON t1.camera_id = t2.camera_id
                      WHERE t1.destination = '{destination_selections[0]}'
                            AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                      GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                            t2.address,
                            t2.equipment_id,
                            t2.camera_id,
                            t1.destination,
                            LEFT(t1.zone, 3)
                      ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                      ;
            '''
        elif len(destination_selections) != 1:
            query = f'''SELECT *,
                               (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                     t2.address,
                                     t2.equipment_id,
                                     t2.camera_id,
                                     t1.destination,
                                     LEFT(t1.zone, 3) AS POV,
                                     SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                              ELSE 0 END) AS bus_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                              ELSE 0 END) AS car_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                              ELSE 0 END) AS lorry_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                              ELSE 0 END) AS truck_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                              ELSE 0 END) AS van_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                              ELSE 0 END) AS motorbike_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                              ELSE 0 END) AS total_count,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS lane_speed,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS motor_speed,
                                     COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                         ELSE t1.zone END)) AS indicator
                              FROM dws_tfc_state_volume_speed_tp AS t1
                              RIGHT JOIN (SELECT address,
                                                 equipment_id,
                                                 camera_id
                                          FROM dim_camera_states
                                          WHERE address = '{road_selections[0]}') AS t2
                              ON t1.camera_id = t2.camera_id
                              WHERE t1.destination IN {tuple(destination_selections)}
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                              GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                              ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        else:
            print('ERROR IN DESTINATION')
        
    elif len(road_selections) != 1:
        
        if len(destination_selections) == 1:
            query = f'''SELECT *,
                               (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                     t2.address,
                                     t2.equipment_id,
                                     t2.camera_id,
                                     t1.destination,
                                     LEFT(t1.zone, 3) AS POV,
                                     SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                              ELSE 0 END) AS bus_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                              ELSE 0 END) AS car_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                              ELSE 0 END) AS lorry_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                              ELSE 0 END) AS truck_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                              ELSE 0 END) AS van_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                              ELSE 0 END) AS motorbike_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                              ELSE 0 END) AS total_count,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS lane_speed,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS motor_speed,
                                     COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                         ELSE t1.zone END)) AS indicator
                              FROM dws_tfc_state_volume_speed_tp AS t1
                              RIGHT JOIN (SELECT address,
                                                 equipment_id,
                                                 camera_id
                                          FROM dim_camera_states
                                          WHERE address IN {tuple(road_selections)}) AS t2
                              ON t1.camera_id = t2.camera_id
                              WHERE t1.destination = '{destination_selections[0]}'
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                              GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                              ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        elif len(destination_selections) != 1:
            query = f'''SELECT *,
                               (total_count - motorbike_count) / (lane_speed * indicator) AS LOS
                        FROM (SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
                                     t2.address,
                                     t2.equipment_id,
                                     t2.camera_id,
                                     t1.destination,
                                     LEFT(t1.zone, 3) AS POV,
                                     SUM(CASE WHEN t1.vehicle_type = 'bus' THEN t1.agg_count 
                                              ELSE 0 END) AS bus_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'car' THEN t1.agg_count 
                                              ELSE 0 END) AS car_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'lorry' THEN t1.agg_count 
                                              ELSE 0 END) AS lorry_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'truck' THEN t1.agg_count 
                                              ELSE 0 END) AS truck_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'van' THEN t1.agg_count 
                                              ELSE 0 END) AS van_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'motorbike' THEN t1.agg_count 
                                              ELSE 0 END) AS motorbike_count,
                                     SUM(CASE WHEN t1.vehicle_type = 'ALL' THEN t1.agg_count 
                                              ELSE 0 END) AS total_count,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type NOT IN ('ALL', 'motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS lane_speed,
                                     AVG(CASE WHEN t1.avg_speed > 0 AND t1.vehicle_type IN ('motorbike') THEN t1.avg_speed 
                                              ELSE NULL END) AS motor_speed,
                                     COUNT(DISTINCT(CASE WHEN t1.avg_speed < 0 AND t1.vehicle_type IN ('ALL', 'motorbike') THEN NULL
                                                         ELSE t1.zone END)) AS indicator
                              FROM dws_tfc_state_volume_speed_tp AS t1
                              RIGHT JOIN (SELECT address,
                                                 equipment_id,
                                                 camera_id
                                          FROM dim_camera_states
                                          WHERE address IN {tuple(road_selections)}) AS t2
                              ON t1.camera_id = t2.camera_id
                              WHERE t1.destination IN {tuple(destination_selections)}
                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourly_datetime_tuple}
                              GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                    t2.address,
                                    t2.equipment_id,
                                    t2.camera_id,
                                    t1.destination,
                                    LEFT(t1.zone, 3)
                              ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;'''
        else:
            print('ERROR IN DESTINATION')
        
    else:
        print('ERROR IN ROAD')
    
    return query