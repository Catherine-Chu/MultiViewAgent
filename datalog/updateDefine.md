+ 1 drone_info_example.dl

```datalog
% describe the schema of sources and views
%s: drones_cur_state(UAV_ID, LOC_NODE_ID,VIEW_RANGE,LOAD_NUM,CUR_ELECTRICITY,FLYING_STATE,
                     CUR_PATH_LENGTH,CUR_RESOURCE_COST,CUR_TIMESTAMP).
%s: drones_config(UAV_ID,FLEET_ID,SENSE_RANGE,LOAD_CAP,MAX_ELECTRICITY,CHARGE_EFFICIENCY).
%s: cur_processes(REQ_UUID,PROC_ID,UAV_ID,R_W,TIME_INFO).
%v: drone_self_info(UAV_ID, LOC_NODE_ID,VIEW_RANGE,LOAD_NUM,CUR_ELECTRICITY,FLYING_STATE,
                     CUR_PATH_LENGTH,CUR_RESOURCE_COST,
                     FLEET_ID,SENSE_RANGE,LOAD_CAP,MAX_ELECTRICITY,CHARGE_EFFICIENCY).

% rules for insertion and deletion from drones_cur_state
+drones_cur_state(UID,NID,VR,LN,CE,FS,L,RC,T)
    :-  drone_self_info(UID,NID,VR,LN,CE,FS,L,RC,FID,SR,LC,ME,CHE),drones_config(UID,FID,SR,LC,ME,CHE),
        drones_cur_state(UID,_,_,_,_,_,_,_,T),
        cur_processes(RID,PID,UID,_,_), PID=0,
        not drones_cur_state(UID,NID,VR,LN,CE,FS,L,RC,T).
-drones_cur_state(UID,NID,VR,LN,CE,FS,L,RC,T)
    :-  drones_cur_state(UID,NID,VR,LN,CE,FS,L,RC,T),drones_config(UID,FID,SR,LC,ME,CHE),
        cur_processes(RID,PID,UID,_,_), PID=0,
        not drone_self_info(UID,NID,VR,LN,CE,FS,L,RC,FID,SR,LC,ME,CHE).
```

+ 2-1 edges_example.dl

```datalog
%s: grid_nodes(NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE).
%s: grid_edges(FROM_ID,TO_ID,EDGE_ID,DISTANCE).
%s: cur_processes(REQ_UUID,PROC_ID,UAV_ID,R_W,TIME_INFO).
%s: drones_cur_state(UAV_ID, LOC_NODE_ID,VIEW_RANGE,LOAD_NUM,CUR_ELECTRICITY,FLYING_STATE,
                     CUR_PATH_LENGTH,CUR_RESOURCE_COST,CUR_TIMESTAMP).
%s: nodes_config(NODE_ID,POS_X,POS_Y,VISIT_CAP).
%v: drone_local_edges(UAV_ID,FROM_ID,TO_ID,EDGE_ID,DISTANCE).

tmp_pos(UID,UPX,UPY,VR)
    :- drones_cur_state(UID,NID,VR,_,_,_,_,_,_),nodes_config(NID,UPX,UPY,_),
    cur_processes(RID,PID,UID,_,_), PID=0.
tmp_range(UID,NID,PX,PY)
    :- grid_nodes(NID,_,_,_,_,_),nodes_config(NID,PX,PY,_),tmp_pos(UID,UPX,UPY,VR),
    (UPX-PX)*(UPX-PX)+(UPY-PY)*(UPY-PY)<=VR*VR.
tmp_edges(UID,FID,TID,EID,DIS)
    :- grid_edges(FID,TID,EID,DIS), tmp_range(UID,NID,PX,PY), NID=FID.
tmp_local_edges(UID,FID,TID,EID,DIS)
    :- drone_local_edges(UID,FID,TID,EID,DIS), tmp_range(UID,NID,PX,PY), NID=FID.

-grid_edges(FID,TID,EID,DIS)
    :- grid_edges(FID,TID,EID,DIS), tmp_edges(UID,FID,TID,EID,DIS),
    tmp_range(UID,NID,PX,PY), NID=TID,
    not drone_local_edges(UID,FID,TID,EID,DIS).
+grid_edges(FID,TID,EID,DIS)
    :- drone_local_edges(UID,FID,TID,EID,DIS), tmp_local_edges(UID,FID,TID,EID,DIS),
    tmp_range(UID,NID,PX,PY), NID=TID,
    not grid_edges(FID,TID,EID,DIS).
```
+ 2-2 local_edge_view_create.sql

```sql
CREATE OR REPLACE VIEW public.drone_local_edges AS(
  SELECT tmp_range.uav_id, public.grid_edges.*
  FROM public.grid_edges,
  (
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, 
      public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, 
      public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)
    + POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )AS tmp_range
  WHERE
  public.grid_edges.from_id IN
  (
  SELECT node_id
  FROM
  (
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, 
      public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, 
      public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)
    + POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )AS tmp_r
  WHERE tmp_r.uav_id = tmp_range.uav_id
  )
  AND
  public.grid_edges.to_id IN
  (
  SELECT node_id
  FROM
  (
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, 
      public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, 
      public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)
    + POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )AS tmp_r
  WHERE tmp_r.uav_id = tmp_range.uav_id
  )
);
```
+ 3-1 nodes_example.dl

```datalog
%s: grid_nodes(NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE).
%s: cur_processes(REQ_UUID,PROC_ID,UAV_ID,R_W,TIME_INFO).
%s: drones_cur_state(UAV_ID, LOC_NODE_ID,VIEW_RANGE,LOAD_NUM,CUR_ELECTRICITY,FLYING_STATE,
                     CUR_PATH_LENGTH,CUR_RESOURCE_COST,CUR_TIMESTAMP).
%s: nodes_config(NODE_ID,POS_X,POS_Y,VISIT_CAP).
%v: drone_local_nodes(UAV_ID,NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE,POS_X,POS_Y,VISITED_CAP).

tmp_pos(UID,UPX,UPY,VR)
    :- drones_cur_state(UID,NID,VR,_,_,_,_,_,_),nodes_config(NID,UPX,UPY,_),
    cur_processes(RID,PID,UID,_,_), PID=0.
tmp_range(UID,PX,PY)
    :- grid_nodes(NID,_,_,_,_,_),nodes_config(NID,PX,PY,_),tmp_pos(UID,UPX,UPY,VR),
    (UPX-PX)*(UPX-PX)+(UPY-PY)*(UPY-PY)<=VR*VR.

-grid_nodes(NID,VC,V,VN,NR,NT)
    :- grid_nodes(NID,VC,V,VN,NR,NT),nodes_config(NID,PX,PY,VC),tmp_range(UID,PX,PY),
    not drone_local_nodes(UID,NID,VC,V,VN,NR,NT,PX,PY,VC).
+grid_nodes(NID,VC,V,VN,NR,NT)
    :- drone_local_nodes(UID,NID,VC,V,VN,NR,NT,PX,PY,VC),tmp_range(UID,PX,PY),
    not grid_nodes(NID,VC,V,VN,NR,NT).

```
+ 3-2 local_node_view_create.sql

```sql
CREATE OR REPLACE VIEW public.drone_local_nodes AS(
  SELECT tmp_range.uav_id,public.grid_nodes.*,
  tmp_range.pos_x as pos_x, tmp_range.pos_y as pos_y, 
  tmp_range.visit_cap as visit_cap
  FROM public.grid_nodes,(
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, 
      public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, 
      public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)
    + POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )as tmp_range
  WHERE public.grid_nodes.node_id = tmp_range.node_id
);
```
+ 4 charging_station_example.dl

```datalog
%s: charging_stations_config(STATION_ID,NODE_ID,CHARGING_CAP,QUEUE_CAP,DOCK_CAP).
%s: charging_stations_cur_state(STATION_ID,IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,CUR_TIMESTAMP).
%s: drones_cur_charging_targets(CUR_TIMESTAMP,STATION_ID,UAV_ID,WEIGHT).
%s: cur_processes(REQ_UUID,PROC_ID,UAV_ID,R_W,TIME_INFO).
%s: nodes_config(NODE_ID,POS_X,POS_Y,VISIT_CAP).
%v: drone_charge_targets(UAV_ID,STATION_ID,NODE_ID,CHARGING_CAP,QUEUE_CAP,DOCK_CAP,
                         IS_INSERVICE,CUR_UTILIZATION,QUEUE_LENGTH,DOCK_NUM,
                         W,POS_X,POS_Y).

+charging_stations_cur_state(SID,II,CU,QL,DN,CT)
    :- cur_processes(_,PID,UID,_,_), PID=0,
    drones_cur_charging_targets(_,SID,UID,W),
    charging_stations_config(SID,NID,CC,QC,DC),
    nodes_config(NID,PX,PY,_),
    drone_charge_targets(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY),
    charging_stations_cur_state(SID,_,_,_,_,CT),
    not charging_stations_cur_state(SID,II,CU,QL,DN,CT).
-charging_stations_cur_state(SID,II,CU,QL,DN,CT)
    :- cur_processes(_,PID,UID,_,_), PID=0,
    drones_cur_charging_targets(_,SID,UID,W),
    charging_stations_config(SID,NID,CC,QC,DC),
    nodes_config(NID,PX,PY,_),
    charging_stations_cur_state(SID,II,CU,QL,DN,CT),
    not drone_charge_targets(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY).

+drones_cur_charging_targets(CT,SID,UID,W)
    :- cur_processes(_,PID,UID,_,_), PID=0,
    drone_charge_targets(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY),
    charging_stations_config(SID,NID,CC,QC,DC),
    charging_stations_cur_state(SID,II,CU,QL,DN,_),
    nodes_config(NID,PX,PY,_),
    drones_cur_charging_targets(CT,SID,UID,_),
    not drones_cur_charging_targets(CT,SID,UID,W).
-drones_cur_charging_targets(CT,SID,UID,W)
    :- cur_processes(_,PID,UID,_,_), PID=0,
    drones_cur_charging_targets(CT,SID,UID,W),
    charging_stations_config(SID,NID,CC,QC,DC),
    charging_stations_cur_state(SID,II,CU,QL,DN,_),
    nodes_config(NID,PX,PY,_),
    not drone_charge_targets(UID,SID,NID,CC,QC,DC,II,CU,QL,DN,W,PX,PY).

```
+ 5 rescue_support_example.dl

```datalog
%s: rescue_support_cur_state(AREA_ID,TARGET_ID,VICTIMS_NUM,LOAD_DEMAND_NUM,
                             IS_ALLOCATED,IS_COMPLETED,RESPONSIBLE_UAV_ID,CUR_TIMESTAMP).
%s: nodes_config(NODE_ID,POS_X,POS_Y,VISIT_CAP).
%s: cur_processes(REQ_UUID,PROC_ID,UAV_ID,R_W,TIME_INFO).
%v: drone_rescue_targets(UAV_ID,AREA_ID,TARGET_ID,VICTIMS_NUM,LOAD_DEMAND_NUM,
                         IS_ALLOCATED,IS_COMPLETED,POS_X,POS_Y).


-rescue_support_cur_state(AID,TID,VN,LD,IA,IC,UID,CT)
    :- cur_processes(RID,PID,UID,_,_), PID=0,
    rescue_support_cur_state(AID,TID,VN,LD,IA,IC,UID,CT),
    nodes_config(NID,PX,PY,_),NID=TID,
    not drone_rescue_targets(UID,AID,TID,VN,LD,IA,IC,PX,PY).
+rescue_support_cur_state(AID,TID,VN,LD,IA,IC,UID,CT)
    :- cur_processes(RID,PID,UID,_,_), PID=0,
    drone_rescue_targets(UID,AID,TID,VN,LD,IA,IC,_,_),
    CT='2018-11-01 00:00',
    not rescue_support_cur_state(AID,TID,VN,LD,IA,IC,UID,CT).
```