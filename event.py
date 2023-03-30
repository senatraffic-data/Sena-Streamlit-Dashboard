import pandas as pd

from my_functions import sqlToDataframe

import streamlit as st


class Event:
    def __init__(self) -> None:
        self.factEvent = None
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
    
    def getfactEventDataframe(self, userSlicerSelections, databaseCredentials):
        hourlyDatetime = pd.date_range(
            start=userSlicerSelections['hourlyDatetime'][0],
            end=userSlicerSelections['hourlyDatetime'][-1],
            freq='H'
        ).strftime(userSlicerSelections['hourlyDatetimeFormat'])
        
        hourlyDatetimeTuple = tuple(hourlyDatetime)
        eventQuery = self.getMainEventQuery(hourlyDatetimeTuple, userSlicerSelections)
        self.factEvent = sqlToDataframe(databaseCredentials, eventQuery)
    
    def getMainEventQuery(self, hourlyDatetimeTuple, userSlicerSelections) -> str:
        if len(userSlicerSelections['destinations']) == 1:
                        
            if len(userSlicerSelections['roads']) == 1:
                eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
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
                                                        WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                                            ON t1.camera_id = t2.camera_id
                                            WHERE t1.direction = '{userSlicerSelections['destinations'][0]}'
                                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                            GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                    t2.address,
                                                    t2.camera_id,
                                                    t1.direction,
                                                    t1.zone, 
                                                    t1.event_type,
                                                    t1.item_type
                                            ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                            ;'''
            elif len(userSlicerSelections['roads']) != 1:
                eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
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
                                                        WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                            ON t1.camera_id = t2.camera_id
                                            WHERE t1.direction = '{userSlicerSelections['destinations'][0]}'
                                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
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
                            
        elif len(userSlicerSelections['destinations']) == 2:
                        
            if len(userSlicerSelections['roads']) == 1:
                eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
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
                                                        WHERE address = '{userSlicerSelections['roads'][0]}') AS t2
                                            ON t1.camera_id = t2.camera_id
                                            WHERE t1.direction IN {tuple(userSlicerSelections['destinations'])}
                                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
                                            GROUP BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00'),
                                                    t2.address,
                                                    t2.camera_id,
                                                    t1.direction,
                                                    t1.zone, 
                                                    t1.event_type,
                                                    t1.item_type
                                            ORDER BY DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') DESC
                                            ;'''
            elif len(userSlicerSelections['roads']) != 1:
                eventQuery = f'''SELECT DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') AS datetime,
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
                                                        WHERE address IN {tuple(userSlicerSelections['roads'])}) AS t2
                                            ON t1.camera_id = t2.camera_id
                                            WHERE t1.direction IN {tuple(userSlicerSelections['destinations'])}
                                                    AND DATE_FORMAT(t1.time, '%Y-%m-%d %H:00:00') IN {hourlyDatetimeTuple}
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
        
        return eventQuery