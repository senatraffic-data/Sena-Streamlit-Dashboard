import pandas as pd

import streamlit as st

from my_functions import sqlToDataframe


@st.cache_resource
class VolumeSpeedLOS:
    def __init__(self) -> None:
        self.factVolumeSpeed = None
        self.dimCamera = None
        
    def getFilteredCameras(self, selectedRoad, databaseCredentials):
        if len(selectedRoad) != 1:
            query1 = f'''
                SELECT *
                FROM dim_camera_states AS t1
                WHERE address IN {tuple(selectedRoad)}
                ;
            '''
        elif len(selectedRoad) == 1:
            query1 = f'''
                SELECT *
                FROM dim_camera_states AS t1
                WHERE address = '{selectedRoad[0]}'
                ;
            '''
        else:
            raise ValueError

        self.dimCamera = sqlToDataframe(databaseCredentials, query1)
    
    @st.cache_data
    def getFactVolumeSpeed(_self, userSlicerSelections: dict, databaseCredentials: dict):
        dateFormat = '%Y-%m-%d %H:%M:%S'
        
        hourlyDatetime = pd.date_range(
            start=userSlicerSelections['hourlyDatetime'][0], 
            end=userSlicerSelections['hourlyDatetime'][-1], 
            freq='H'
        ).strftime(dateFormat)
        
        hourlyDatetimeTuple = tuple(hourlyDatetime)
        query = _self.getVolumeSpeedLOSQuery(hourlyDatetimeTuple, userSlicerSelections) 
        _self.factVolumeSpeed = sqlToDataframe(databaseCredentials, query)
        _self.factVolumeSpeed['datetime'] = pd.to_datetime(_self.factVolumeSpeed['datetime'])
        
    def getVolumeSpeedLOSQuery(self, hourlyDatetimeTuple, userSlicerSelections) -> str:
        if len(userSlicerSelections['roads']) == 1:
            
            if len(userSlicerSelections['destinations']) == 1:
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
                                    WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                        ON t1.camera_id = t2.camera_id
                        WHERE t1.destination = '{userSlicerSelections['destinations'][0]}'
                                AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                        GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                t2.address,
                                t2.equipment_id,
                                t2.camera_id,
                                t1.destination,
                                LEFT(t1.zone, 3)
                        ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                        ;
                '''
            elif len(userSlicerSelections['destinations']) != 1:
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
                                            WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                                ON t1.camera_id = t2.camera_id
                                WHERE t1.destination IN {tuple(userSlicerSelections['destinations'])}
                                        AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
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
            
        elif len(userSlicerSelections['roads']) != 1:
            
            if len(userSlicerSelections['destinations']) == 1:
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
                                            WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                ON t1.camera_id = t2.camera_id
                                WHERE t1.destination = '{userSlicerSelections['destinations'][0]}'
                                        AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                        t2.address,
                                        t2.equipment_id,
                                        t2.camera_id,
                                        t1.destination,
                                        LEFT(t1.zone, 3)
                                ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC) AS metrics
                            ;'''
            elif len(userSlicerSelections['destinations']) != 1:
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
                                            WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                ON t1.camera_id = t2.camera_id
                                WHERE t1.destination IN {tuple(userSlicerSelections['destinations'])}
                                        AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
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
        
    def generateHourlyLOS(self, selectedDestinations):
        dfHourlyLOS = self.factVolumeSpeed.pivot_table(
            values=['LOS'],
            index=['datetime'],
            columns=['destination']
        )
        
        dfHourlyLOS = dfHourlyLOS.asfreq('H').ffill()
        dfHourlyLOSConditioned = self.hourlyLOSConditional(dfHourlyLOS, selectedDestinations)
        
        return dfHourlyLOSConditioned
        
    def hourlyLOSConditional(self, dfHourlyLOS, selectedDestinations):
        if len(selectedDestinations) == 1:

            if dfHourlyLOS.shape[-1] == 1:
                dfHourlyLOS.columns = [selectedDestinations[0]]
            elif dfHourlyLOS.shape[-1] == 2:
                dfHourlyLOS.columns = ['TEST', selectedDestinations[0]]
                dfHourlyLOS = dfHourlyLOS.drop(columns=['TEST'])
            else:
                st.write('ERROR IN LENGTH 1')

        elif len(selectedDestinations) != 1:

            if dfHourlyLOS.shape[-1] == 2:
                dfHourlyLOS.columns = [selectedDestinations[0], selectedDestinations[-1]]
            elif dfHourlyLOS.shape[-1] == 3:
                dfHourlyLOS.columns = ['TEST', selectedDestinations[0], selectedDestinations[-1]]
                dfHourlyLOS = dfHourlyLOS.drop(columns=['TEST'])
            else:
                st.write('ERROR IN LENGTH 2')

        else:
            st.write('ERROR IN DESTINATION LENGTH')

        return dfHourlyLOS