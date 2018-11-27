/*_____get datalog program_______
?- drone_charge_targets(UAV_ID,STATION_ID,NODE_ID,CHARGING_CAP,QUEUE_CAP,DOCK_CAP,IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,W,POS_X,POS_Y).

drone_charge_targets(DRONE_CHARGE_TARGETS_A13_UAV_ID,DRONE_CHARGE_TARGETS_A13_STATION_ID,DRONE_CHARGE_TARGETS_A13_NODE_ID,DRONE_CHARGE_TARGETS_A13_CHARGING_CAP,DRONE_CHARGE_TARGETS_A13_QUEUE_CAP,DRONE_CHARGE_TARGETS_A13_DOCK_CAP,DRONE_CHARGE_TARGETS_A13_IS_INSERVICE,DRONE_CHARGE_TARGETS_A13_CUR_UTILIZATION,DRONE_CHARGE_TARGETS_A13_QUEUE_LENGTH,DRONE_CHARGE_TARGETS_A13_DOCK_NUM,DRONE_CHARGE_TARGETS_A13_W,DRONE_CHARGE_TARGETS_A13_POS_X,DRONE_CHARGE_TARGETS_A13_POS_Y) :- drone_charge_targets_med(DRONE_CHARGE_TARGETS_A13_UAV_ID,DRONE_CHARGE_TARGETS_A13_STATION_ID,DRONE_CHARGE_TARGETS_A13_NODE_ID,DRONE_CHARGE_TARGETS_A13_CHARGING_CAP,DRONE_CHARGE_TARGETS_A13_QUEUE_CAP,DRONE_CHARGE_TARGETS_A13_DOCK_CAP,DRONE_CHARGE_TARGETS_A13_IS_INSERVICE,DRONE_CHARGE_TARGETS_A13_CUR_UTILIZATION,DRONE_CHARGE_TARGETS_A13_QUEUE_LENGTH,DRONE_CHARGE_TARGETS_A13_DOCK_NUM,DRONE_CHARGE_TARGETS_A13_W,DRONE_CHARGE_TARGETS_A13_POS_X,DRONE_CHARGE_TARGETS_A13_POS_Y) , not __dummy__delta__insert__drones_cur_charging_targets(_,DRONE_CHARGE_TARGETS_A13_STATION_ID,DRONE_CHARGE_TARGETS_A13_UAV_ID,DRONE_CHARGE_TARGETS_A13_W) , not __dummy__delta__insert__charging_stations_cur_state(DRONE_CHARGE_TARGETS_A13_STATION_ID,DRONE_CHARGE_TARGETS_A13_IS_INSERVICE,DRONE_CHARGE_TARGETS_A13_CUR_UTILIZATION,DRONE_CHARGE_TARGETS_A13_QUEUE_LENGTH,DRONE_CHARGE_TARGETS_A13_DOCK_NUM,_).

__dummy__delta__insert__charging_stations_cur_state(SID,II,CU,QL,DN,CT) :- cur_processes(_,PID,UID,_,_) , PID = 0 , drones_cur_charging_targets(_,SID,UID,W) , charging_stations_config(SID,NID,CC,QC,DC) , nodes_config(NID,PX,PY,_) , drone_charge_targets_med(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY) , charging_stations_cur_state(SID,_,_,_,_,CT) , not charging_stations_cur_state(SID,II,CU,QL,DN,CT).

drone_charge_targets_med(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY) :- cur_processes(_,PID,UID,_,_) , PID = 0 , drones_cur_charging_targets(_,SID,UID,W) , charging_stations_config(SID,NID,CC,QC,DC) , nodes_config(NID,PX,PY,_) , charging_stations_cur_state(SID,II,CU,QL,DN,CT).

__dummy__delta__insert__drones_cur_charging_targets(CT,SID,UID,W) :- cur_processes(_,PID,UID,_,_) , PID = 0 , drone_charge_targets_med(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY) , charging_stations_config(SID,NID,CC,QC,DC) , charging_stations_cur_state(SID,II,CU,QL,DN,_) , nodes_config(NID,PX,PY,_) , drones_cur_charging_targets(CT,SID,UID,_) , not drones_cur_charging_targets(CT,SID,UID,W).

drone_charge_targets_med(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY) :- cur_processes(_,PID,UID,_,_) , PID = 0 , drones_cur_charging_targets(CT,SID,UID,W) , charging_stations_config(SID,NID,CC,QC,DC) , charging_stations_cur_state(SID,II,CU,QL,DN,_) , nodes_config(NID,PX,PY,_).

______________*/

CREATE OR REPLACE VIEW public.drone_charge_targets AS 
SELECT __dummy__.col0 AS UAV_ID,__dummy__.col1 AS STATION_ID,__dummy__.col2 AS NODE_ID,__dummy__.col3 AS CHARGING_CAP,__dummy__.col4 AS QUEUE_CAP,__dummy__.col5 AS DOCK_CAP,__dummy__.col6 AS IS_INSERVICE,__dummy__.col7 AS CUR_UTILIZATION,__dummy__.col8 AS QUEUE_LENGTH,__dummy__.col9 AS DOCK_NUM,__dummy__.col10 AS W,__dummy__.col11 AS POS_X,__dummy__.col12 AS POS_Y 
FROM (SELECT DISTINCT drone_charge_targets_a13_0.col0 AS col0, drone_charge_targets_a13_0.col1 AS col1, drone_charge_targets_a13_0.col2 AS col2, drone_charge_targets_a13_0.col3 AS col3, drone_charge_targets_a13_0.col4 AS col4, drone_charge_targets_a13_0.col5 AS col5, drone_charge_targets_a13_0.col6 AS col6, drone_charge_targets_a13_0.col7 AS col7, drone_charge_targets_a13_0.col8 AS col8, drone_charge_targets_a13_0.col9 AS col9, drone_charge_targets_a13_0.col10 AS col10, drone_charge_targets_a13_0.col11 AS col11, drone_charge_targets_a13_0.col12 AS col12 
FROM (SELECT DISTINCT drone_charge_targets_med_a13_0.col0 AS col0, drone_charge_targets_med_a13_0.col1 AS col1, drone_charge_targets_med_a13_0.col2 AS col2, drone_charge_targets_med_a13_0.col3 AS col3, drone_charge_targets_med_a13_0.col4 AS col4, drone_charge_targets_med_a13_0.col5 AS col5, drone_charge_targets_med_a13_0.col6 AS col6, drone_charge_targets_med_a13_0.col7 AS col7, drone_charge_targets_med_a13_0.col8 AS col8, drone_charge_targets_med_a13_0.col9 AS col9, drone_charge_targets_med_a13_0.col10 AS col10, drone_charge_targets_med_a13_0.col11 AS col11, drone_charge_targets_med_a13_0.col12 AS col12 
FROM (SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_4.STATION_ID AS col1, nodes_config_a4_3.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_4.IS_INSERVICE AS col6, charging_stations_cur_state_a6_4.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_4.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_4.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_3.POS_X AS col11, nodes_config_a4_3.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, public.charging_stations_cur_state AS charging_stations_cur_state_a6_4 
WHERE charging_stations_cur_state_a6_4.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_4.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_3.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0  UNION SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_3.STATION_ID AS col1, nodes_config_a4_4.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_3.IS_INSERVICE AS col6, charging_stations_cur_state_a6_3.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_3.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_3.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_4.POS_X AS col11, nodes_config_a4_4.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4 
WHERE charging_stations_cur_state_a6_3.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_3.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0 ) AS drone_charge_targets_med_a13_0 
WHERE NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT drones_cur_charging_targets_a4_5.CUR_TIMESTAMP AS col0, drones_cur_charging_targets_a4_5.STATION_ID AS col1, drones_cur_charging_targets_a4_5.UAV_ID AS col2, drone_charge_targets_med_a13_1.col10 AS col3 
FROM public.cur_processes AS cur_processes_a5_0, (SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_4.STATION_ID AS col1, nodes_config_a4_3.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_4.IS_INSERVICE AS col6, charging_stations_cur_state_a6_4.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_4.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_4.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_3.POS_X AS col11, nodes_config_a4_3.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, public.charging_stations_cur_state AS charging_stations_cur_state_a6_4 
WHERE charging_stations_cur_state_a6_4.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_4.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_3.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0  UNION SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_3.STATION_ID AS col1, nodes_config_a4_4.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_3.IS_INSERVICE AS col6, charging_stations_cur_state_a6_3.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_3.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_3.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_4.POS_X AS col11, nodes_config_a4_4.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4 
WHERE charging_stations_cur_state_a6_3.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_3.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0 ) AS drone_charge_targets_med_a13_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_5 
WHERE charging_stations_config_a5_2.QUEUE_CAP = drone_charge_targets_med_a13_1.col4 AND drones_cur_charging_targets_a4_5.STATION_ID = charging_stations_cur_state_a6_3.STATION_ID AND drones_cur_charging_targets_a4_5.STATION_ID = charging_stations_config_a5_2.STATION_ID AND drones_cur_charging_targets_a4_5.STATION_ID = drone_charge_targets_med_a13_1.col1 AND nodes_config_a4_4.POS_X = drone_charge_targets_med_a13_1.col11 AND charging_stations_config_a5_2.DOCK_CAP = drone_charge_targets_med_a13_1.col5 AND charging_stations_cur_state_a6_3.DOCK_NUM = drone_charge_targets_med_a13_1.col9 AND charging_stations_config_a5_2.CHARGING_CAP = drone_charge_targets_med_a13_1.col3 AND charging_stations_cur_state_a6_3.CUR_UTILIZATION = drone_charge_targets_med_a13_1.col7 AND nodes_config_a4_4.POS_Y = drone_charge_targets_med_a13_1.col12 AND charging_stations_cur_state_a6_3.QUEUE_LENGTH = drone_charge_targets_med_a13_1.col8 AND drones_cur_charging_targets_a4_5.UAV_ID = drone_charge_targets_med_a13_1.col0 AND drones_cur_charging_targets_a4_5.UAV_ID = cur_processes_a5_0.UAV_ID AND charging_stations_cur_state_a6_3.IS_INSERVICE = drone_charge_targets_med_a13_1.col6 AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND nodes_config_a4_4.NODE_ID = drone_charge_targets_med_a13_1.col2 AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.drones_cur_charging_targets AS drones_cur_charging_targets_a4 
WHERE drones_cur_charging_targets_a4.WEIGHT IS NOT DISTINCT FROM drone_charge_targets_med_a13_1.col10 AND drones_cur_charging_targets_a4.UAV_ID IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.UAV_ID AND drones_cur_charging_targets_a4.STATION_ID IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.STATION_ID AND drones_cur_charging_targets_a4.CUR_TIMESTAMP IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.CUR_TIMESTAMP ) ) AS __dummy__delta__insert__drones_cur_charging_targets_a4 
WHERE __dummy__delta__insert__drones_cur_charging_targets_a4.col3 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col10 AND __dummy__delta__insert__drones_cur_charging_targets_a4.col2 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col0 AND __dummy__delta__insert__drones_cur_charging_targets_a4.col1 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col1 ) AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT charging_stations_cur_state_a6_5.STATION_ID AS col0, drone_charge_targets_med_a13_4.col6 AS col1, drone_charge_targets_med_a13_4.col7 AS col2, drone_charge_targets_med_a13_4.col8 AS col3, drone_charge_targets_med_a13_4.col9 AS col4, charging_stations_cur_state_a6_5.CUR_TIMESTAMP AS col5 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, (SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_4.STATION_ID AS col1, nodes_config_a4_3.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_4.IS_INSERVICE AS col6, charging_stations_cur_state_a6_4.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_4.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_4.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_3.POS_X AS col11, nodes_config_a4_3.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, public.charging_stations_cur_state AS charging_stations_cur_state_a6_4 
WHERE charging_stations_cur_state_a6_4.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_4.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_3.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0  UNION SELECT DISTINCT drones_cur_charging_targets_a4_1.UAV_ID AS col0, charging_stations_cur_state_a6_3.STATION_ID AS col1, nodes_config_a4_4.NODE_ID AS col2, charging_stations_config_a5_2.CHARGING_CAP AS col3, charging_stations_config_a5_2.QUEUE_CAP AS col4, charging_stations_config_a5_2.DOCK_CAP AS col5, charging_stations_cur_state_a6_3.IS_INSERVICE AS col6, charging_stations_cur_state_a6_3.CUR_UTILIZATION AS col7, charging_stations_cur_state_a6_3.QUEUE_LENGTH AS col8, charging_stations_cur_state_a6_3.DOCK_NUM AS col9, drones_cur_charging_targets_a4_1.WEIGHT AS col10, nodes_config_a4_4.POS_X AS col11, nodes_config_a4_4.POS_Y AS col12 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4 
WHERE charging_stations_cur_state_a6_3.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_3.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0 ) AS drone_charge_targets_med_a13_4, public.charging_stations_cur_state AS charging_stations_cur_state_a6_5 
WHERE drone_charge_targets_med_a13_4.col4 = charging_stations_config_a5_2.QUEUE_CAP AND charging_stations_cur_state_a6_5.STATION_ID = drone_charge_targets_med_a13_4.col1 AND charging_stations_cur_state_a6_5.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_5.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drone_charge_targets_med_a13_4.col11 = nodes_config_a4_3.POS_X AND drone_charge_targets_med_a13_4.col5 = charging_stations_config_a5_2.DOCK_CAP AND drone_charge_targets_med_a13_4.col3 = charging_stations_config_a5_2.CHARGING_CAP AND drone_charge_targets_med_a13_4.col12 = nodes_config_a4_3.POS_Y AND drone_charge_targets_med_a13_4.col0 = drones_cur_charging_targets_a4_1.UAV_ID AND drone_charge_targets_med_a13_4.col0 = cur_processes_a5_0.UAV_ID AND drone_charge_targets_med_a13_4.col2 = nodes_config_a4_3.NODE_ID AND drone_charge_targets_med_a13_4.col2 = charging_stations_config_a5_2.NODE_ID AND drone_charge_targets_med_a13_4.col10 = drones_cur_charging_targets_a4_1.WEIGHT AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.charging_stations_cur_state AS charging_stations_cur_state_a6 
WHERE charging_stations_cur_state_a6.CUR_TIMESTAMP IS NOT DISTINCT FROM charging_stations_cur_state_a6_5.CUR_TIMESTAMP AND charging_stations_cur_state_a6.DOCK_NUM IS NOT DISTINCT FROM drone_charge_targets_med_a13_4.col9 AND charging_stations_cur_state_a6.QUEUE_LENGTH IS NOT DISTINCT FROM drone_charge_targets_med_a13_4.col8 AND charging_stations_cur_state_a6.CUR_UTILIZATION IS NOT DISTINCT FROM drone_charge_targets_med_a13_4.col7 AND charging_stations_cur_state_a6.IS_INSERVICE IS NOT DISTINCT FROM drone_charge_targets_med_a13_4.col6 AND charging_stations_cur_state_a6.STATION_ID IS NOT DISTINCT FROM charging_stations_cur_state_a6_5.STATION_ID ) ) AS __dummy__delta__insert__charging_stations_cur_state_a6 
WHERE __dummy__delta__insert__charging_stations_cur_state_a6.col4 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col9 AND __dummy__delta__insert__charging_stations_cur_state_a6.col3 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col8 AND __dummy__delta__insert__charging_stations_cur_state_a6.col2 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col7 AND __dummy__delta__insert__charging_stations_cur_state_a6.col1 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col6 AND __dummy__delta__insert__charging_stations_cur_state_a6.col0 IS NOT DISTINCT FROM drone_charge_targets_med_a13_0.col1 ) ) AS drone_charge_targets_a13_0  ) AS __dummy__;

CREATE OR REPLACE FUNCTION public.drone_charge_targets_delta_action()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  temprec__dummy__delta__delete__charging_stations_cur_state public.charging_stations_cur_state%ROWTYPE;
temprec__dummy__delta__delete__drones_cur_charging_targets public.drones_cur_charging_targets%ROWTYPE;
temprec__dummy__delta__insert__charging_stations_cur_state public.charging_stations_cur_state%ROWTYPE;
temprec__dummy__delta__insert__drones_cur_charging_targets public.drones_cur_charging_targets%ROWTYPE;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'drone_charge_targets_delta_action_flag') THEN
        -- RAISE NOTICE 'execute procedure drone_charge_targets_delta_action';
        CREATE TEMPORARY TABLE drone_charge_targets_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        CREATE TEMPORARY TABLE __dummy__delta__delete__charging_stations_cur_state WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5) :: public.charging_stations_cur_state).* 
            FROM (SELECT DISTINCT __dummy__delta__delete__charging_stations_cur_state_a6_0.col0 AS col0, __dummy__delta__delete__charging_stations_cur_state_a6_0.col1 AS col1, __dummy__delta__delete__charging_stations_cur_state_a6_0.col2 AS col2, __dummy__delta__delete__charging_stations_cur_state_a6_0.col3 AS col3, __dummy__delta__delete__charging_stations_cur_state_a6_0.col4 AS col4, __dummy__delta__delete__charging_stations_cur_state_a6_0.col5 AS col5 
FROM (SELECT DISTINCT charging_stations_cur_state_a6_4.STATION_ID AS col0, charging_stations_cur_state_a6_4.IS_INSERVICE AS col1, charging_stations_cur_state_a6_4.CUR_UTILIZATION AS col2, charging_stations_cur_state_a6_4.QUEUE_LENGTH AS col3, charging_stations_cur_state_a6_4.DOCK_NUM AS col4, charging_stations_cur_state_a6_4.CUR_TIMESTAMP AS col5 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, public.charging_stations_cur_state AS charging_stations_cur_state_a6_4 
WHERE charging_stations_cur_state_a6_4.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_4.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_3.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT __temp__drone_charge_targets_a13_0.UAV_ID AS col0, __temp__drone_charge_targets_a13_0.STATION_ID AS col1, __temp__drone_charge_targets_a13_0.NODE_ID AS col2, __temp__drone_charge_targets_a13_0.CHARGING_CAP AS col3, __temp__drone_charge_targets_a13_0.QUEUE_CAP AS col4, __temp__drone_charge_targets_a13_0.DOCK_CAP AS col5, __temp__drone_charge_targets_a13_0.IS_INSERVICE AS col6, __temp__drone_charge_targets_a13_0.CUR_UTILIZATION AS col7, __temp__drone_charge_targets_a13_0.QUEUE_LENGTH AS col8, __temp__drone_charge_targets_a13_0.DOCK_NUM AS col9, __temp__drone_charge_targets_a13_0.W AS col10, __temp__drone_charge_targets_a13_0.POS_X AS col11, __temp__drone_charge_targets_a13_0.POS_Y AS col12 
FROM __temp__drone_charge_targets AS __temp__drone_charge_targets_a13_0  ) AS drone_charge_targets_a13 
WHERE drone_charge_targets_a13.col12 IS NOT DISTINCT FROM nodes_config_a4_3.POS_Y AND drone_charge_targets_a13.col11 IS NOT DISTINCT FROM nodes_config_a4_3.POS_X AND drone_charge_targets_a13.col10 IS NOT DISTINCT FROM drones_cur_charging_targets_a4_1.WEIGHT AND drone_charge_targets_a13.col9 IS NOT DISTINCT FROM charging_stations_cur_state_a6_4.DOCK_NUM AND drone_charge_targets_a13.col8 IS NOT DISTINCT FROM charging_stations_cur_state_a6_4.QUEUE_LENGTH AND drone_charge_targets_a13.col7 IS NOT DISTINCT FROM charging_stations_cur_state_a6_4.CUR_UTILIZATION AND drone_charge_targets_a13.col6 IS NOT DISTINCT FROM charging_stations_cur_state_a6_4.IS_INSERVICE AND drone_charge_targets_a13.col5 IS NOT DISTINCT FROM charging_stations_config_a5_2.DOCK_CAP AND drone_charge_targets_a13.col4 IS NOT DISTINCT FROM charging_stations_config_a5_2.QUEUE_CAP AND drone_charge_targets_a13.col3 IS NOT DISTINCT FROM charging_stations_config_a5_2.CHARGING_CAP AND drone_charge_targets_a13.col2 IS NOT DISTINCT FROM nodes_config_a4_3.NODE_ID AND drone_charge_targets_a13.col1 IS NOT DISTINCT FROM charging_stations_cur_state_a6_4.STATION_ID AND drone_charge_targets_a13.col0 IS NOT DISTINCT FROM drones_cur_charging_targets_a4_1.UAV_ID ) ) AS __dummy__delta__delete__charging_stations_cur_state_a6_0  ) AS __dummy__delta__delete__charging_stations_cur_state_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__delete__drones_cur_charging_targets WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3) :: public.drones_cur_charging_targets).* 
            FROM (SELECT DISTINCT __dummy__delta__delete__drones_cur_charging_targets_a4_0.col0 AS col0, __dummy__delta__delete__drones_cur_charging_targets_a4_0.col1 AS col1, __dummy__delta__delete__drones_cur_charging_targets_a4_0.col2 AS col2, __dummy__delta__delete__drones_cur_charging_targets_a4_0.col3 AS col3 
FROM (SELECT DISTINCT drones_cur_charging_targets_a4_1.CUR_TIMESTAMP AS col0, charging_stations_cur_state_a6_3.STATION_ID AS col1, drones_cur_charging_targets_a4_1.UAV_ID AS col2, drones_cur_charging_targets_a4_1.WEIGHT AS col3 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4 
WHERE charging_stations_cur_state_a6_3.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_3.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drones_cur_charging_targets_a4_1.UAV_ID = cur_processes_a5_0.UAV_ID AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT __temp__drone_charge_targets_a13_0.UAV_ID AS col0, __temp__drone_charge_targets_a13_0.STATION_ID AS col1, __temp__drone_charge_targets_a13_0.NODE_ID AS col2, __temp__drone_charge_targets_a13_0.CHARGING_CAP AS col3, __temp__drone_charge_targets_a13_0.QUEUE_CAP AS col4, __temp__drone_charge_targets_a13_0.DOCK_CAP AS col5, __temp__drone_charge_targets_a13_0.IS_INSERVICE AS col6, __temp__drone_charge_targets_a13_0.CUR_UTILIZATION AS col7, __temp__drone_charge_targets_a13_0.QUEUE_LENGTH AS col8, __temp__drone_charge_targets_a13_0.DOCK_NUM AS col9, __temp__drone_charge_targets_a13_0.W AS col10, __temp__drone_charge_targets_a13_0.POS_X AS col11, __temp__drone_charge_targets_a13_0.POS_Y AS col12 
FROM __temp__drone_charge_targets AS __temp__drone_charge_targets_a13_0  ) AS drone_charge_targets_a13 
WHERE drone_charge_targets_a13.col12 IS NOT DISTINCT FROM nodes_config_a4_4.POS_Y AND drone_charge_targets_a13.col11 IS NOT DISTINCT FROM nodes_config_a4_4.POS_X AND drone_charge_targets_a13.col10 IS NOT DISTINCT FROM drones_cur_charging_targets_a4_1.WEIGHT AND drone_charge_targets_a13.col9 IS NOT DISTINCT FROM charging_stations_cur_state_a6_3.DOCK_NUM AND drone_charge_targets_a13.col8 IS NOT DISTINCT FROM charging_stations_cur_state_a6_3.QUEUE_LENGTH AND drone_charge_targets_a13.col7 IS NOT DISTINCT FROM charging_stations_cur_state_a6_3.CUR_UTILIZATION AND drone_charge_targets_a13.col6 IS NOT DISTINCT FROM charging_stations_cur_state_a6_3.IS_INSERVICE AND drone_charge_targets_a13.col5 IS NOT DISTINCT FROM charging_stations_config_a5_2.DOCK_CAP AND drone_charge_targets_a13.col4 IS NOT DISTINCT FROM charging_stations_config_a5_2.QUEUE_CAP AND drone_charge_targets_a13.col3 IS NOT DISTINCT FROM charging_stations_config_a5_2.CHARGING_CAP AND drone_charge_targets_a13.col2 IS NOT DISTINCT FROM nodes_config_a4_4.NODE_ID AND drone_charge_targets_a13.col1 IS NOT DISTINCT FROM charging_stations_cur_state_a6_3.STATION_ID AND drone_charge_targets_a13.col0 IS NOT DISTINCT FROM drones_cur_charging_targets_a4_1.UAV_ID ) ) AS __dummy__delta__delete__drones_cur_charging_targets_a4_0  ) AS __dummy__delta__delete__drones_cur_charging_targets_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__insert__charging_stations_cur_state WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5) :: public.charging_stations_cur_state).* 
            FROM (SELECT DISTINCT __dummy__delta__insert__charging_stations_cur_state_a6_0.col0 AS col0, __dummy__delta__insert__charging_stations_cur_state_a6_0.col1 AS col1, __dummy__delta__insert__charging_stations_cur_state_a6_0.col2 AS col2, __dummy__delta__insert__charging_stations_cur_state_a6_0.col3 AS col3, __dummy__delta__insert__charging_stations_cur_state_a6_0.col4 AS col4, __dummy__delta__insert__charging_stations_cur_state_a6_0.col5 AS col5 
FROM (SELECT DISTINCT charging_stations_cur_state_a6_5.STATION_ID AS col0, drone_charge_targets_a13_4.col6 AS col1, drone_charge_targets_a13_4.col7 AS col2, drone_charge_targets_a13_4.col8 AS col3, drone_charge_targets_a13_4.col9 AS col4, charging_stations_cur_state_a6_5.CUR_TIMESTAMP AS col5 
FROM public.cur_processes AS cur_processes_a5_0, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_1, public.charging_stations_config AS charging_stations_config_a5_2, public.nodes_config AS nodes_config_a4_3, (SELECT DISTINCT __temp__drone_charge_targets_a13_0.UAV_ID AS col0, __temp__drone_charge_targets_a13_0.STATION_ID AS col1, __temp__drone_charge_targets_a13_0.NODE_ID AS col2, __temp__drone_charge_targets_a13_0.CHARGING_CAP AS col3, __temp__drone_charge_targets_a13_0.QUEUE_CAP AS col4, __temp__drone_charge_targets_a13_0.DOCK_CAP AS col5, __temp__drone_charge_targets_a13_0.IS_INSERVICE AS col6, __temp__drone_charge_targets_a13_0.CUR_UTILIZATION AS col7, __temp__drone_charge_targets_a13_0.QUEUE_LENGTH AS col8, __temp__drone_charge_targets_a13_0.DOCK_NUM AS col9, __temp__drone_charge_targets_a13_0.W AS col10, __temp__drone_charge_targets_a13_0.POS_X AS col11, __temp__drone_charge_targets_a13_0.POS_Y AS col12 
FROM __temp__drone_charge_targets AS __temp__drone_charge_targets_a13_0  ) AS drone_charge_targets_a13_4, public.charging_stations_cur_state AS charging_stations_cur_state_a6_5 
WHERE drone_charge_targets_a13_4.col4 = charging_stations_config_a5_2.QUEUE_CAP AND charging_stations_cur_state_a6_5.STATION_ID = drone_charge_targets_a13_4.col1 AND charging_stations_cur_state_a6_5.STATION_ID = charging_stations_config_a5_2.STATION_ID AND charging_stations_cur_state_a6_5.STATION_ID = drones_cur_charging_targets_a4_1.STATION_ID AND drone_charge_targets_a13_4.col11 = nodes_config_a4_3.POS_X AND drone_charge_targets_a13_4.col5 = charging_stations_config_a5_2.DOCK_CAP AND drone_charge_targets_a13_4.col3 = charging_stations_config_a5_2.CHARGING_CAP AND drone_charge_targets_a13_4.col12 = nodes_config_a4_3.POS_Y AND drone_charge_targets_a13_4.col0 = drones_cur_charging_targets_a4_1.UAV_ID AND drone_charge_targets_a13_4.col0 = cur_processes_a5_0.UAV_ID AND drone_charge_targets_a13_4.col2 = nodes_config_a4_3.NODE_ID AND drone_charge_targets_a13_4.col2 = charging_stations_config_a5_2.NODE_ID AND drone_charge_targets_a13_4.col10 = drones_cur_charging_targets_a4_1.WEIGHT AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.charging_stations_cur_state AS charging_stations_cur_state_a6 
WHERE charging_stations_cur_state_a6.CUR_TIMESTAMP IS NOT DISTINCT FROM charging_stations_cur_state_a6_5.CUR_TIMESTAMP AND charging_stations_cur_state_a6.DOCK_NUM IS NOT DISTINCT FROM drone_charge_targets_a13_4.col9 AND charging_stations_cur_state_a6.QUEUE_LENGTH IS NOT DISTINCT FROM drone_charge_targets_a13_4.col8 AND charging_stations_cur_state_a6.CUR_UTILIZATION IS NOT DISTINCT FROM drone_charge_targets_a13_4.col7 AND charging_stations_cur_state_a6.IS_INSERVICE IS NOT DISTINCT FROM drone_charge_targets_a13_4.col6 AND charging_stations_cur_state_a6.STATION_ID IS NOT DISTINCT FROM charging_stations_cur_state_a6_5.STATION_ID ) ) AS __dummy__delta__insert__charging_stations_cur_state_a6_0  ) AS __dummy__delta__insert__charging_stations_cur_state_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__insert__drones_cur_charging_targets WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3) :: public.drones_cur_charging_targets).* 
            FROM (SELECT DISTINCT __dummy__delta__insert__drones_cur_charging_targets_a4_0.col0 AS col0, __dummy__delta__insert__drones_cur_charging_targets_a4_0.col1 AS col1, __dummy__delta__insert__drones_cur_charging_targets_a4_0.col2 AS col2, __dummy__delta__insert__drones_cur_charging_targets_a4_0.col3 AS col3 
FROM (SELECT DISTINCT drones_cur_charging_targets_a4_5.CUR_TIMESTAMP AS col0, drones_cur_charging_targets_a4_5.STATION_ID AS col1, drones_cur_charging_targets_a4_5.UAV_ID AS col2, drone_charge_targets_a13_1.col10 AS col3 
FROM public.cur_processes AS cur_processes_a5_0, (SELECT DISTINCT __temp__drone_charge_targets_a13_0.UAV_ID AS col0, __temp__drone_charge_targets_a13_0.STATION_ID AS col1, __temp__drone_charge_targets_a13_0.NODE_ID AS col2, __temp__drone_charge_targets_a13_0.CHARGING_CAP AS col3, __temp__drone_charge_targets_a13_0.QUEUE_CAP AS col4, __temp__drone_charge_targets_a13_0.DOCK_CAP AS col5, __temp__drone_charge_targets_a13_0.IS_INSERVICE AS col6, __temp__drone_charge_targets_a13_0.CUR_UTILIZATION AS col7, __temp__drone_charge_targets_a13_0.QUEUE_LENGTH AS col8, __temp__drone_charge_targets_a13_0.DOCK_NUM AS col9, __temp__drone_charge_targets_a13_0.W AS col10, __temp__drone_charge_targets_a13_0.POS_X AS col11, __temp__drone_charge_targets_a13_0.POS_Y AS col12 
FROM __temp__drone_charge_targets AS __temp__drone_charge_targets_a13_0  ) AS drone_charge_targets_a13_1, public.charging_stations_config AS charging_stations_config_a5_2, public.charging_stations_cur_state AS charging_stations_cur_state_a6_3, public.nodes_config AS nodes_config_a4_4, public.drones_cur_charging_targets AS drones_cur_charging_targets_a4_5 
WHERE charging_stations_config_a5_2.QUEUE_CAP = drone_charge_targets_a13_1.col4 AND drones_cur_charging_targets_a4_5.STATION_ID = charging_stations_cur_state_a6_3.STATION_ID AND drones_cur_charging_targets_a4_5.STATION_ID = charging_stations_config_a5_2.STATION_ID AND drones_cur_charging_targets_a4_5.STATION_ID = drone_charge_targets_a13_1.col1 AND nodes_config_a4_4.POS_X = drone_charge_targets_a13_1.col11 AND charging_stations_config_a5_2.DOCK_CAP = drone_charge_targets_a13_1.col5 AND charging_stations_cur_state_a6_3.DOCK_NUM = drone_charge_targets_a13_1.col9 AND charging_stations_config_a5_2.CHARGING_CAP = drone_charge_targets_a13_1.col3 AND charging_stations_cur_state_a6_3.CUR_UTILIZATION = drone_charge_targets_a13_1.col7 AND nodes_config_a4_4.POS_Y = drone_charge_targets_a13_1.col12 AND charging_stations_cur_state_a6_3.QUEUE_LENGTH = drone_charge_targets_a13_1.col8 AND drones_cur_charging_targets_a4_5.UAV_ID = drone_charge_targets_a13_1.col0 AND drones_cur_charging_targets_a4_5.UAV_ID = cur_processes_a5_0.UAV_ID AND charging_stations_cur_state_a6_3.IS_INSERVICE = drone_charge_targets_a13_1.col6 AND nodes_config_a4_4.NODE_ID = charging_stations_config_a5_2.NODE_ID AND nodes_config_a4_4.NODE_ID = drone_charge_targets_a13_1.col2 AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.drones_cur_charging_targets AS drones_cur_charging_targets_a4 
WHERE drones_cur_charging_targets_a4.WEIGHT IS NOT DISTINCT FROM drone_charge_targets_a13_1.col10 AND drones_cur_charging_targets_a4.UAV_ID IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.UAV_ID AND drones_cur_charging_targets_a4.STATION_ID IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.STATION_ID AND drones_cur_charging_targets_a4.CUR_TIMESTAMP IS NOT DISTINCT FROM drones_cur_charging_targets_a4_5.CUR_TIMESTAMP ) ) AS __dummy__delta__insert__drones_cur_charging_targets_a4_0  ) AS __dummy__delta__insert__drones_cur_charging_targets_extra_alias; 

FOR temprec__dummy__delta__delete__charging_stations_cur_state IN ( SELECT * FROM __dummy__delta__delete__charging_stations_cur_state) LOOP 
            DELETE FROM public.charging_stations_cur_state WHERE ROW(STATION_ID,IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,CUR_TIMESTAMP) IS NOT DISTINCT FROM  temprec__dummy__delta__delete__charging_stations_cur_state;
            END LOOP;
DROP TABLE __dummy__delta__delete__charging_stations_cur_state;

FOR temprec__dummy__delta__delete__drones_cur_charging_targets IN ( SELECT * FROM __dummy__delta__delete__drones_cur_charging_targets) LOOP 
            DELETE FROM public.drones_cur_charging_targets WHERE ROW(CUR_TIMESTAMP,STATION_ID,UAV_ID,WEIGHT) IS NOT DISTINCT FROM  temprec__dummy__delta__delete__drones_cur_charging_targets;
            END LOOP;
DROP TABLE __dummy__delta__delete__drones_cur_charging_targets;

INSERT INTO public.charging_stations_cur_state SELECT * FROM  __dummy__delta__insert__charging_stations_cur_state; 
DROP TABLE __dummy__delta__insert__charging_stations_cur_state;

INSERT INTO public.drones_cur_charging_targets SELECT * FROM  __dummy__delta__insert__drones_cur_charging_targets; 
DROP TABLE __dummy__delta__insert__drones_cur_charging_targets;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_charge_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_charge_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.drone_charge_targets_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__temp__drone_charge_targets')
    THEN
        -- RAISE NOTICE 'execute procedure drone_charge_targets_materialization';
        CREATE TEMPORARY TABLE __temp__drone_charge_targets WITH OIDS ON COMMIT DROP AS SELECT * FROM public.drone_charge_targets;
        CREATE CONSTRAINT TRIGGER __temp__peer1_public_trigger_delta_action
        AFTER INSERT OR UPDATE OR DELETE ON 
            __temp__drone_charge_targets DEFERRABLE INITIALLY DEFERRED 
            FOR EACH ROW EXECUTE PROCEDURE public.drone_charge_targets_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_charge_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_charge_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_charge_targets_trigger_materialization ON public.drone_charge_targets;
CREATE TRIGGER drone_charge_targets_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.drone_charge_targets FOR EACH STATEMENT EXECUTE PROCEDURE public.drone_charge_targets_materialization();

CREATE OR REPLACE FUNCTION public.drone_charge_targets_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE NOTICE 'execute procedure drone_charge_targets_update';
    IF TG_OP = 'INSERT' THEN
      INSERT INTO __temp__drone_charge_targets SELECT (NEW).*; 
    ELSIF TG_OP = 'UPDATE' THEN
      DELETE FROM __temp__drone_charge_targets WHERE ROW(UAV_ID,STATION_ID,NODE_ID,CHARGING_CAP,QUEUE_CAP,DOCK_CAP,IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,W,POS_X,POS_Y) IS NOT DISTINCT FROM OLD;
      INSERT INTO __temp__drone_charge_targets SELECT (NEW).*; 
    ELSIF TG_OP = 'DELETE' THEN
      DELETE FROM __temp__drone_charge_targets WHERE ROW(UAV_ID,STATION_ID,NODE_ID,CHARGING_CAP,QUEUE_CAP,DOCK_CAP,IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,W,POS_X,POS_Y) IS NOT DISTINCT FROM OLD;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_charge_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_charge_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_charge_targets_trigger_update ON public.drone_charge_targets;
CREATE TRIGGER drone_charge_targets_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.drone_charge_targets FOR EACH ROW EXECUTE PROCEDURE public.drone_charge_targets_update();

