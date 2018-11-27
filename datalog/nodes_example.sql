
CREATE OR REPLACE FUNCTION public.drone_local_nodes_delta_action()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  temprec__dummy__delta__delete__grid_nodes public.grid_nodes%ROWTYPE;
temprec__dummy__delta__insert__grid_nodes public.grid_nodes%ROWTYPE;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'drone_local_nodes_delta_action_flag') THEN
        -- RAISE NOTICE 'execute procedure drone_local_nodes_delta_action';
        CREATE TEMPORARY TABLE drone_local_nodes_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        CREATE TEMPORARY TABLE __dummy__delta__delete__grid_nodes WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5) :: public.grid_nodes).* 
            FROM (SELECT DISTINCT __dummy__delta__delete__grid_nodes_a6_0.col0 AS col0, __dummy__delta__delete__grid_nodes_a6_0.col1 AS col1, __dummy__delta__delete__grid_nodes_a6_0.col2 AS col2, __dummy__delta__delete__grid_nodes_a6_0.col3 AS col3, __dummy__delta__delete__grid_nodes_a6_0.col4 AS col4, __dummy__delta__delete__grid_nodes_a6_0.col5 AS col5 
FROM (SELECT DISTINCT nodes_config_a4_1.NODE_ID AS col0, grid_nodes_a6_0.VISIT_COUNT AS col1, grid_nodes_a6_0.VISITED AS col2, grid_nodes_a6_0.VICTIMS_NUM AS col3, grid_nodes_a6_0.NEED_RESCUE AS col4, grid_nodes_a6_0.NODE_TYPE AS col5 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a3_2 
WHERE tmp_range_a3_2.col1 = nodes_config_a4_1.POS_X AND tmp_range_a3_2.col2 = nodes_config_a4_1.POS_Y AND nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT __temp__drone_local_nodes_a10_0.UAV_ID AS col0, __temp__drone_local_nodes_a10_0.NODE_ID AS col1, __temp__drone_local_nodes_a10_0.VISIT_COUNT AS col2, __temp__drone_local_nodes_a10_0.VISITED AS col3, __temp__drone_local_nodes_a10_0.VICTIMS_NUM AS col4, __temp__drone_local_nodes_a10_0.NEED_RESCUE AS col5, __temp__drone_local_nodes_a10_0.NODE_TYPE AS col6, __temp__drone_local_nodes_a10_0.POS_X AS col7, __temp__drone_local_nodes_a10_0.POS_Y AS col8, __temp__drone_local_nodes_a10_0.VISIT_CAP AS col9 
FROM __temp__drone_local_nodes AS __temp__drone_local_nodes_a10_0  ) AS drone_local_nodes_a10 
WHERE drone_local_nodes_a10.col9 IS NOT DISTINCT FROM nodes_config_a4_1.VISIT_CAP AND drone_local_nodes_a10.col8 IS NOT DISTINCT FROM tmp_range_a3_2.col2 AND drone_local_nodes_a10.col7 IS NOT DISTINCT FROM tmp_range_a3_2.col1 AND drone_local_nodes_a10.col6 IS NOT DISTINCT FROM grid_nodes_a6_0.NODE_TYPE AND drone_local_nodes_a10.col5 IS NOT DISTINCT FROM grid_nodes_a6_0.NEED_RESCUE AND drone_local_nodes_a10.col4 IS NOT DISTINCT FROM grid_nodes_a6_0.VICTIMS_NUM AND drone_local_nodes_a10.col3 IS NOT DISTINCT FROM grid_nodes_a6_0.VISITED AND drone_local_nodes_a10.col2 IS NOT DISTINCT FROM grid_nodes_a6_0.VISIT_COUNT AND drone_local_nodes_a10.col1 IS NOT DISTINCT FROM nodes_config_a4_1.NODE_ID AND drone_local_nodes_a10.col0 IS NOT DISTINCT FROM tmp_range_a3_2.col0 ) ) AS __dummy__delta__delete__grid_nodes_a6_0  ) AS __dummy__delta__delete__grid_nodes_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__insert__grid_nodes WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3,col4,col5) :: public.grid_nodes).* 
            FROM (SELECT DISTINCT __dummy__delta__insert__grid_nodes_a6_0.col0 AS col0, __dummy__delta__insert__grid_nodes_a6_0.col1 AS col1, __dummy__delta__insert__grid_nodes_a6_0.col2 AS col2, __dummy__delta__insert__grid_nodes_a6_0.col3 AS col3, __dummy__delta__insert__grid_nodes_a6_0.col4 AS col4, __dummy__delta__insert__grid_nodes_a6_0.col5 AS col5 
FROM (SELECT DISTINCT drone_local_nodes_a10_0.col1 AS col0, drone_local_nodes_a10_0.col2 AS col1, drone_local_nodes_a10_0.col3 AS col2, drone_local_nodes_a10_0.col4 AS col3, drone_local_nodes_a10_0.col5 AS col4, drone_local_nodes_a10_0.col6 AS col5 
FROM (SELECT DISTINCT __temp__drone_local_nodes_a10_0.UAV_ID AS col0, __temp__drone_local_nodes_a10_0.NODE_ID AS col1, __temp__drone_local_nodes_a10_0.VISIT_COUNT AS col2, __temp__drone_local_nodes_a10_0.VISITED AS col3, __temp__drone_local_nodes_a10_0.VICTIMS_NUM AS col4, __temp__drone_local_nodes_a10_0.NEED_RESCUE AS col5, __temp__drone_local_nodes_a10_0.NODE_TYPE AS col6, __temp__drone_local_nodes_a10_0.POS_X AS col7, __temp__drone_local_nodes_a10_0.POS_Y AS col8, __temp__drone_local_nodes_a10_0.VISIT_CAP AS col9 
FROM __temp__drone_local_nodes AS __temp__drone_local_nodes_a10_0  ) AS drone_local_nodes_a10_0, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a3_1 
WHERE tmp_range_a3_1.col1 = drone_local_nodes_a10_0.col7 AND tmp_range_a3_1.col2 = drone_local_nodes_a10_0.col8 AND tmp_range_a3_1.col0 = drone_local_nodes_a10_0.col0 AND NOT EXISTS ( SELECT * 
FROM public.grid_nodes AS grid_nodes_a6 
WHERE grid_nodes_a6.NODE_TYPE IS NOT DISTINCT FROM drone_local_nodes_a10_0.col6 AND grid_nodes_a6.NEED_RESCUE IS NOT DISTINCT FROM drone_local_nodes_a10_0.col5 AND grid_nodes_a6.VICTIMS_NUM IS NOT DISTINCT FROM drone_local_nodes_a10_0.col4 AND grid_nodes_a6.VISITED IS NOT DISTINCT FROM drone_local_nodes_a10_0.col3 AND grid_nodes_a6.VISIT_COUNT IS NOT DISTINCT FROM drone_local_nodes_a10_0.col2 AND grid_nodes_a6.NODE_ID IS NOT DISTINCT FROM drone_local_nodes_a10_0.col1 ) ) AS __dummy__delta__insert__grid_nodes_a6_0  ) AS __dummy__delta__insert__grid_nodes_extra_alias; 

FOR temprec__dummy__delta__delete__grid_nodes IN ( SELECT * FROM __dummy__delta__delete__grid_nodes) LOOP 
            DELETE FROM public.grid_nodes WHERE ROW(NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE) IS NOT DISTINCT FROM  temprec__dummy__delta__delete__grid_nodes;
            END LOOP;
DROP TABLE __dummy__delta__delete__grid_nodes;

INSERT INTO public.grid_nodes SELECT * FROM  __dummy__delta__insert__grid_nodes; 
DROP TABLE __dummy__delta__insert__grid_nodes;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_nodes';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_nodes ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.drone_local_nodes_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__temp__drone_local_nodes')
    THEN
        -- RAISE NOTICE 'execute procedure drone_local_nodes_materialization';
        CREATE TEMPORARY TABLE __temp__drone_local_nodes WITH OIDS ON COMMIT DROP AS SELECT * FROM public.drone_local_nodes;
        CREATE CONSTRAINT TRIGGER __temp__peer1_public_trigger_delta_action
        AFTER INSERT OR UPDATE OR DELETE ON 
            __temp__drone_local_nodes DEFERRABLE INITIALLY DEFERRED 
            FOR EACH ROW EXECUTE PROCEDURE public.drone_local_nodes_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_nodes';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_nodes ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_local_nodes_trigger_materialization ON public.drone_local_nodes;
CREATE TRIGGER drone_local_nodes_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.drone_local_nodes FOR EACH STATEMENT EXECUTE PROCEDURE public.drone_local_nodes_materialization();

CREATE OR REPLACE FUNCTION public.drone_local_nodes_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE NOTICE 'execute procedure drone_local_nodes_update';
    IF TG_OP = 'INSERT' THEN
      INSERT INTO __temp__drone_local_nodes SELECT (NEW).*; 
    ELSIF TG_OP = 'UPDATE' THEN
      DELETE FROM __temp__drone_local_nodes WHERE ROW(UAV_ID,NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE,POS_X,POS_Y,VISIT_CAP) IS NOT DISTINCT FROM OLD;
      INSERT INTO __temp__drone_local_nodes SELECT (NEW).*; 
    ELSIF TG_OP = 'DELETE' THEN
      DELETE FROM __temp__drone_local_nodes WHERE ROW(UAV_ID,NODE_ID,VISIT_COUNT,VISITED,VICTIMS_NUM,NEED_RESCUE,NODE_TYPE,POS_X,POS_Y,VISIT_CAP) IS NOT DISTINCT FROM OLD;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_nodes';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_nodes ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_local_nodes_trigger_update ON public.drone_local_nodes;
CREATE TRIGGER drone_local_nodes_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.drone_local_nodes FOR EACH ROW EXECUTE PROCEDURE public.drone_local_nodes_update();

