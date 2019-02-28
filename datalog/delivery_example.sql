/*_____get datalog program_______
?- drone_delivery_targets(UAV_ID,AREA_ID,TARGET_ID,LOAD_DEMAND_NUM,IS_ALLOCATED,IS_COMPLETED,POS_X,POS_Y).

drone_delivery_targets(DRONE_DELIVERY_TARGETS_A8_UAV_ID,DRONE_DELIVERY_TARGETS_A8_AREA_ID,DRONE_DELIVERY_TARGETS_A8_TARGET_ID,DRONE_DELIVERY_TARGETS_A8_LOAD_DEMAND_NUM,DRONE_DELIVERY_TARGETS_A8_IS_ALLOCATED,DRONE_DELIVERY_TARGETS_A8_IS_COMPLETED,DRONE_DELIVERY_TARGETS_A8_POS_X,DRONE_DELIVERY_TARGETS_A8_POS_Y) :- drone_delivery_targets_med(DRONE_DELIVERY_TARGETS_A8_UAV_ID,DRONE_DELIVERY_TARGETS_A8_AREA_ID,DRONE_DELIVERY_TARGETS_A8_TARGET_ID,DRONE_DELIVERY_TARGETS_A8_LOAD_DEMAND_NUM,DRONE_DELIVERY_TARGETS_A8_IS_ALLOCATED,DRONE_DELIVERY_TARGETS_A8_IS_COMPLETED,DRONE_DELIVERY_TARGETS_A8_POS_X,DRONE_DELIVERY_TARGETS_A8_POS_Y) , not __dummy__delta__insert__delivery_cur_state(DRONE_DELIVERY_TARGETS_A8_AREA_ID,DRONE_DELIVERY_TARGETS_A8_TARGET_ID,DRONE_DELIVERY_TARGETS_A8_LOAD_DEMAND_NUM,DRONE_DELIVERY_TARGETS_A8_IS_ALLOCATED,DRONE_DELIVERY_TARGETS_A8_IS_COMPLETED,DRONE_DELIVERY_TARGETS_A8_UAV_ID,_).

drone_delivery_targets_med(UID,AID,TID,LD,IA,IC,PX,PY) :- cur_processes(RID,PID,UID,_,_) , PID = 0 , delivery_cur_state(AID,TID,LD,IA,IC,UID,CT) , nodes_config(NID,PX,PY,_) , NID = TID.

__dummy__delta__insert__delivery_cur_state(AID,TID,LD,IA,IC,UID,CT) :- cur_processes(RID,PID,UID,_,_) , PID = 0 , drone_delivery_targets_med(UID,AID,TID,LD,IA,IC,_,_) , CT = '2018-11-01 00:00' , not delivery_cur_state(AID,TID,LD,IA,IC,UID,CT).

______________*/

CREATE OR REPLACE VIEW public.drone_delivery_targets AS 
SELECT __dummy__.col0 AS UAV_ID,__dummy__.col1 AS AREA_ID,__dummy__.col2 AS TARGET_ID,__dummy__.col3 AS LOAD_DEMAND_NUM,__dummy__.col4 AS IS_ALLOCATED,__dummy__.col5 AS IS_COMPLETED,__dummy__.col6 AS POS_X,__dummy__.col7 AS POS_Y 
FROM (SELECT DISTINCT drone_delivery_targets_a8_0.col0 AS col0, drone_delivery_targets_a8_0.col1 AS col1, drone_delivery_targets_a8_0.col2 AS col2, drone_delivery_targets_a8_0.col3 AS col3, drone_delivery_targets_a8_0.col4 AS col4, drone_delivery_targets_a8_0.col5 AS col5, drone_delivery_targets_a8_0.col6 AS col6, drone_delivery_targets_a8_0.col7 AS col7 
FROM (SELECT DISTINCT drone_delivery_targets_med_a8_0.col0 AS col0, drone_delivery_targets_med_a8_0.col1 AS col1, drone_delivery_targets_med_a8_0.col2 AS col2, drone_delivery_targets_med_a8_0.col3 AS col3, drone_delivery_targets_med_a8_0.col4 AS col4, drone_delivery_targets_med_a8_0.col5 AS col5, drone_delivery_targets_med_a8_0.col6 AS col6, drone_delivery_targets_med_a8_0.col7 AS col7 
FROM (SELECT DISTINCT delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID AS col0, delivery_cur_state_a7_1.AREA_ID AS col1, delivery_cur_state_a7_1.TARGET_ID AS col2, delivery_cur_state_a7_1.LOAD_DEMAND_NUM AS col3, delivery_cur_state_a7_1.IS_ALLOCATED AS col4, delivery_cur_state_a7_1.IS_COMPLETED AS col5, nodes_config_a4_2.POS_X AS col6, nodes_config_a4_2.POS_Y AS col7 
FROM public.cur_processes AS cur_processes_a5_0, public.delivery_cur_state AS delivery_cur_state_a7_1, public.nodes_config AS nodes_config_a4_2 
WHERE delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID = cur_processes_a5_0.UAV_ID AND cur_processes_a5_0.PROC_ID = 0 AND nodes_config_a4_2.NODE_ID = delivery_cur_state_a7_1.TARGET_ID ) AS drone_delivery_targets_med_a8_0 
WHERE NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT drone_delivery_targets_med_a8_1.col1 AS col0, drone_delivery_targets_med_a8_1.col2 AS col1, drone_delivery_targets_med_a8_1.col3 AS col2, drone_delivery_targets_med_a8_1.col4 AS col3, drone_delivery_targets_med_a8_1.col5 AS col4, drone_delivery_targets_med_a8_1.col0 AS col5, '2018-11-01 00:00' AS col6 
FROM public.cur_processes AS cur_processes_a5_0, (SELECT DISTINCT delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID AS col0, delivery_cur_state_a7_1.AREA_ID AS col1, delivery_cur_state_a7_1.TARGET_ID AS col2, delivery_cur_state_a7_1.LOAD_DEMAND_NUM AS col3, delivery_cur_state_a7_1.IS_ALLOCATED AS col4, delivery_cur_state_a7_1.IS_COMPLETED AS col5, nodes_config_a4_2.POS_X AS col6, nodes_config_a4_2.POS_Y AS col7 
FROM public.cur_processes AS cur_processes_a5_0, public.delivery_cur_state AS delivery_cur_state_a7_1, public.nodes_config AS nodes_config_a4_2 
WHERE delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID = cur_processes_a5_0.UAV_ID AND cur_processes_a5_0.PROC_ID = 0 AND nodes_config_a4_2.NODE_ID = delivery_cur_state_a7_1.TARGET_ID ) AS drone_delivery_targets_med_a8_1 
WHERE drone_delivery_targets_med_a8_1.col0 = cur_processes_a5_0.UAV_ID AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.delivery_cur_state AS delivery_cur_state_a7 
WHERE delivery_cur_state_a7.CUR_TIMESTAMP IS NOT DISTINCT FROM '2018-11-01 00:00' AND delivery_cur_state_a7.RESPONSIBLE_UAV_ID IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col0 AND delivery_cur_state_a7.IS_COMPLETED IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col5 AND delivery_cur_state_a7.IS_ALLOCATED IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col4 AND delivery_cur_state_a7.LOAD_DEMAND_NUM IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col3 AND delivery_cur_state_a7.TARGET_ID IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col2 AND delivery_cur_state_a7.AREA_ID IS NOT DISTINCT FROM drone_delivery_targets_med_a8_1.col1 ) ) AS __dummy__delta__insert__delivery_cur_state_a7 
WHERE __dummy__delta__insert__delivery_cur_state_a7.col5 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col0 AND __dummy__delta__insert__delivery_cur_state_a7.col4 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col5 AND __dummy__delta__insert__delivery_cur_state_a7.col3 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col4 AND __dummy__delta__insert__delivery_cur_state_a7.col2 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col3 AND __dummy__delta__insert__delivery_cur_state_a7.col1 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col2 AND __dummy__delta__insert__delivery_cur_state_a7.col0 IS NOT DISTINCT FROM drone_delivery_targets_med_a8_0.col1 ) ) AS drone_delivery_targets_a8_0  ) AS __dummy__;

CREATE OR REPLACE FUNCTION public.drone_delivery_targets_delta_action()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  temprec__dummy__delta__delete__delivery_cur_state public.delivery_cur_state%ROWTYPE;
temprec__dummy__delta__insert__delivery_cur_state public.delivery_cur_state%ROWTYPE;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'drone_delivery_targets_delta_action_flag') THEN
        -- RAISE NOTICE 'execute procedure drone_delivery_targets_delta_action';
        CREATE TEMPORARY TABLE drone_delivery_targets_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        CREATE TEMPORARY TABLE __dummy__delta__delete__delivery_cur_state WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5,col6) :: public.delivery_cur_state).* 
            FROM (SELECT DISTINCT __dummy__delta__delete__delivery_cur_state_a7_0.col0 AS col0, __dummy__delta__delete__delivery_cur_state_a7_0.col1 AS col1, __dummy__delta__delete__delivery_cur_state_a7_0.col2 AS col2, __dummy__delta__delete__delivery_cur_state_a7_0.col3 AS col3, __dummy__delta__delete__delivery_cur_state_a7_0.col4 AS col4, __dummy__delta__delete__delivery_cur_state_a7_0.col5 AS col5, __dummy__delta__delete__delivery_cur_state_a7_0.col6 AS col6 
FROM (SELECT DISTINCT delivery_cur_state_a7_1.AREA_ID AS col0, delivery_cur_state_a7_1.TARGET_ID AS col1, delivery_cur_state_a7_1.LOAD_DEMAND_NUM AS col2, delivery_cur_state_a7_1.IS_ALLOCATED AS col3, delivery_cur_state_a7_1.IS_COMPLETED AS col4, delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID AS col5, delivery_cur_state_a7_1.CUR_TIMESTAMP AS col6 
FROM public.cur_processes AS cur_processes_a5_0, public.delivery_cur_state AS delivery_cur_state_a7_1, public.nodes_config AS nodes_config_a4_2 
WHERE delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID = cur_processes_a5_0.UAV_ID AND cur_processes_a5_0.PROC_ID = 0 AND nodes_config_a4_2.NODE_ID = delivery_cur_state_a7_1.TARGET_ID AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT __temp__drone_delivery_targets_a8_0.UAV_ID AS col0, __temp__drone_delivery_targets_a8_0.AREA_ID AS col1, __temp__drone_delivery_targets_a8_0.TARGET_ID AS col2, __temp__drone_delivery_targets_a8_0.LOAD_DEMAND_NUM AS col3, __temp__drone_delivery_targets_a8_0.IS_ALLOCATED AS col4, __temp__drone_delivery_targets_a8_0.IS_COMPLETED AS col5, __temp__drone_delivery_targets_a8_0.POS_X AS col6, __temp__drone_delivery_targets_a8_0.POS_Y AS col7 
FROM __temp__drone_delivery_targets AS __temp__drone_delivery_targets_a8_0  ) AS drone_delivery_targets_a8 
WHERE drone_delivery_targets_a8.col7 IS NOT DISTINCT FROM nodes_config_a4_2.POS_Y AND drone_delivery_targets_a8.col6 IS NOT DISTINCT FROM nodes_config_a4_2.POS_X AND drone_delivery_targets_a8.col5 IS NOT DISTINCT FROM delivery_cur_state_a7_1.IS_COMPLETED AND drone_delivery_targets_a8.col4 IS NOT DISTINCT FROM delivery_cur_state_a7_1.IS_ALLOCATED AND drone_delivery_targets_a8.col3 IS NOT DISTINCT FROM delivery_cur_state_a7_1.LOAD_DEMAND_NUM AND drone_delivery_targets_a8.col2 IS NOT DISTINCT FROM delivery_cur_state_a7_1.TARGET_ID AND drone_delivery_targets_a8.col1 IS NOT DISTINCT FROM delivery_cur_state_a7_1.AREA_ID AND drone_delivery_targets_a8.col0 IS NOT DISTINCT FROM delivery_cur_state_a7_1.RESPONSIBLE_UAV_ID ) ) AS __dummy__delta__delete__delivery_cur_state_a7_0  ) AS __dummy__delta__delete__delivery_cur_state_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__insert__delivery_cur_state WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5,col6) :: public.delivery_cur_state).* 
            FROM (SELECT DISTINCT __dummy__delta__insert__delivery_cur_state_a7_0.col0 AS col0, __dummy__delta__insert__delivery_cur_state_a7_0.col1 AS col1, __dummy__delta__insert__delivery_cur_state_a7_0.col2 AS col2, __dummy__delta__insert__delivery_cur_state_a7_0.col3 AS col3, __dummy__delta__insert__delivery_cur_state_a7_0.col4 AS col4, __dummy__delta__insert__delivery_cur_state_a7_0.col5 AS col5, __dummy__delta__insert__delivery_cur_state_a7_0.col6 AS col6 
FROM (SELECT DISTINCT drone_delivery_targets_a8_1.col1 AS col0, drone_delivery_targets_a8_1.col2 AS col1, drone_delivery_targets_a8_1.col3 AS col2, drone_delivery_targets_a8_1.col4 AS col3, drone_delivery_targets_a8_1.col5 AS col4, drone_delivery_targets_a8_1.col0 AS col5, '2018-11-01 00:00' AS col6 
FROM public.cur_processes AS cur_processes_a5_0, (SELECT DISTINCT __temp__drone_delivery_targets_a8_0.UAV_ID AS col0, __temp__drone_delivery_targets_a8_0.AREA_ID AS col1, __temp__drone_delivery_targets_a8_0.TARGET_ID AS col2, __temp__drone_delivery_targets_a8_0.LOAD_DEMAND_NUM AS col3, __temp__drone_delivery_targets_a8_0.IS_ALLOCATED AS col4, __temp__drone_delivery_targets_a8_0.IS_COMPLETED AS col5, __temp__drone_delivery_targets_a8_0.POS_X AS col6, __temp__drone_delivery_targets_a8_0.POS_Y AS col7 
FROM __temp__drone_delivery_targets AS __temp__drone_delivery_targets_a8_0  ) AS drone_delivery_targets_a8_1 
WHERE drone_delivery_targets_a8_1.col0 = cur_processes_a5_0.UAV_ID AND cur_processes_a5_0.PROC_ID = 0 AND NOT EXISTS ( SELECT * 
FROM public.delivery_cur_state AS delivery_cur_state_a7 
WHERE delivery_cur_state_a7.CUR_TIMESTAMP IS NOT DISTINCT FROM '2018-11-01 00:00' AND delivery_cur_state_a7.RESPONSIBLE_UAV_ID IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col0 AND delivery_cur_state_a7.IS_COMPLETED IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col5 AND delivery_cur_state_a7.IS_ALLOCATED IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col4 AND delivery_cur_state_a7.LOAD_DEMAND_NUM IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col3 AND delivery_cur_state_a7.TARGET_ID IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col2 AND delivery_cur_state_a7.AREA_ID IS NOT DISTINCT FROM drone_delivery_targets_a8_1.col1 ) ) AS __dummy__delta__insert__delivery_cur_state_a7_0  ) AS __dummy__delta__insert__delivery_cur_state_extra_alias; 

FOR temprec__dummy__delta__delete__delivery_cur_state IN ( SELECT * FROM __dummy__delta__delete__delivery_cur_state) LOOP 
            DELETE FROM public.delivery_cur_state WHERE ROW(AREA_ID,TARGET_ID,LOAD_DEMAND_NUM,IS_ALLOCATED,IS_COMPLETED,RESPONSIBLE_UAV_ID,CUR_TIMESTAMP) IS NOT DISTINCT FROM  temprec__dummy__delta__delete__delivery_cur_state;
            END LOOP;
DROP TABLE __dummy__delta__delete__delivery_cur_state;

INSERT INTO public.delivery_cur_state SELECT * FROM  __dummy__delta__insert__delivery_cur_state; 
DROP TABLE __dummy__delta__insert__delivery_cur_state;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_delivery_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_delivery_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.drone_delivery_targets_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__temp__drone_delivery_targets')
    THEN
        -- RAISE NOTICE 'execute procedure drone_delivery_targets_materialization';
        CREATE TEMPORARY TABLE __temp__drone_delivery_targets WITH OIDS ON COMMIT DROP AS SELECT * FROM public.drone_delivery_targets;
        CREATE CONSTRAINT TRIGGER __temp__peer1_public_trigger_delta_action
        AFTER INSERT OR UPDATE OR DELETE ON 
            __temp__drone_delivery_targets DEFERRABLE INITIALLY DEFERRED 
            FOR EACH ROW EXECUTE PROCEDURE public.drone_delivery_targets_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_delivery_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_delivery_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_delivery_targets_trigger_materialization ON public.drone_delivery_targets;
CREATE TRIGGER drone_delivery_targets_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.drone_delivery_targets FOR EACH STATEMENT EXECUTE PROCEDURE public.drone_delivery_targets_materialization();

CREATE OR REPLACE FUNCTION public.drone_delivery_targets_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE NOTICE 'execute procedure drone_delivery_targets_update';
    IF TG_OP = 'INSERT' THEN
      INSERT INTO __temp__drone_delivery_targets SELECT (NEW).*; 
    ELSIF TG_OP = 'UPDATE' THEN
      DELETE FROM __temp__drone_delivery_targets WHERE ROW(UAV_ID,AREA_ID,TARGET_ID,LOAD_DEMAND_NUM,IS_ALLOCATED,IS_COMPLETED,POS_X,POS_Y) IS NOT DISTINCT FROM OLD;
      INSERT INTO __temp__drone_delivery_targets SELECT (NEW).*; 
    ELSIF TG_OP = 'DELETE' THEN
      DELETE FROM __temp__drone_delivery_targets WHERE ROW(UAV_ID,AREA_ID,TARGET_ID,LOAD_DEMAND_NUM,IS_ALLOCATED,IS_COMPLETED,POS_X,POS_Y) IS NOT DISTINCT FROM OLD;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_delivery_targets';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_delivery_targets ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_delivery_targets_trigger_update ON public.drone_delivery_targets;
CREATE TRIGGER drone_delivery_targets_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.drone_delivery_targets FOR EACH ROW EXECUTE PROCEDURE public.drone_delivery_targets_update();

