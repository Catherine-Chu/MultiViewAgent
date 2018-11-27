
CREATE OR REPLACE FUNCTION public.drone_local_edges_delta_action()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  temprec__dummy__delta__delete__grid_edges public.grid_edges%ROWTYPE;
temprec__dummy__delta__insert__grid_edges public.grid_edges%ROWTYPE;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'drone_local_edges_delta_action_flag') THEN
        -- RAISE NOTICE 'execute procedure drone_local_edges_delta_action';
        CREATE TEMPORARY TABLE drone_local_edges_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        CREATE TEMPORARY TABLE __dummy__delta__delete__grid_edges WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3) :: public.grid_edges).* 
            FROM (SELECT DISTINCT __dummy__delta__delete__grid_edges_a4_0.col0 AS col0, __dummy__delta__delete__grid_edges_a4_0.col1 AS col1, __dummy__delta__delete__grid_edges_a4_0.col2 AS col2, __dummy__delta__delete__grid_edges_a4_0.col3 AS col3 
FROM (SELECT DISTINCT tmp_edges_a5_1.col1 AS col0, tmp_edges_a5_1.col2 AS col1, tmp_edges_a5_1.col3 AS col2, tmp_edges_a5_1.col4 AS col3 
FROM public.grid_edges AS grid_edges_a4_0, (SELECT DISTINCT tmp_range_a4_1.col0 AS col0, grid_edges_a4_0.FROM_ID AS col1, grid_edges_a4_0.TO_ID AS col2, grid_edges_a4_0.EDGE_ID AS col3, grid_edges_a4_0.DISTANCE AS col4 
FROM public.grid_edges AS grid_edges_a4_0, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.NODE_ID AS col1, nodes_config_a4_1.POS_X AS col2, nodes_config_a4_1.POS_Y AS col3 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a4_1 
WHERE tmp_range_a4_1.col1 = grid_edges_a4_0.FROM_ID ) AS tmp_edges_a5_1, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.NODE_ID AS col1, nodes_config_a4_1.POS_X AS col2, nodes_config_a4_1.POS_Y AS col3 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a4_2 
WHERE tmp_edges_a5_1.col2 = grid_edges_a4_0.TO_ID AND tmp_edges_a5_1.col4 = grid_edges_a4_0.DISTANCE AND tmp_edges_a5_1.col1 = grid_edges_a4_0.FROM_ID AND tmp_edges_a5_1.col3 = grid_edges_a4_0.EDGE_ID AND tmp_range_a4_2.col0 = tmp_edges_a5_1.col0 AND tmp_range_a4_2.col1 = tmp_edges_a5_1.col2 AND NOT EXISTS ( SELECT * 
FROM (SELECT DISTINCT __temp__drone_local_edges_a5_0.UAV_ID AS col0, __temp__drone_local_edges_a5_0.FROM_ID AS col1, __temp__drone_local_edges_a5_0.TO_ID AS col2, __temp__drone_local_edges_a5_0.EDGE_ID AS col3, __temp__drone_local_edges_a5_0.DISTANCE AS col4 
FROM __temp__drone_local_edges AS __temp__drone_local_edges_a5_0  ) AS drone_local_edges_a5 
WHERE drone_local_edges_a5.col4 IS NOT DISTINCT FROM tmp_edges_a5_1.col4 AND drone_local_edges_a5.col3 IS NOT DISTINCT FROM tmp_edges_a5_1.col3 AND drone_local_edges_a5.col2 IS NOT DISTINCT FROM tmp_edges_a5_1.col2 AND drone_local_edges_a5.col1 IS NOT DISTINCT FROM tmp_edges_a5_1.col1 AND drone_local_edges_a5.col0 IS NOT DISTINCT FROM tmp_range_a4_2.col0 ) ) AS __dummy__delta__delete__grid_edges_a4_0  ) AS __dummy__delta__delete__grid_edges_extra_alias;

CREATE TEMPORARY TABLE __dummy__delta__insert__grid_edges WITH OIDS ON COMMIT DROP AS SELECT (ROW(col0,col1,col2,col3) :: public.grid_edges).* 
            FROM (SELECT DISTINCT __dummy__delta__insert__grid_edges_a4_0.col0 AS col0, __dummy__delta__insert__grid_edges_a4_0.col1 AS col1, __dummy__delta__insert__grid_edges_a4_0.col2 AS col2, __dummy__delta__insert__grid_edges_a4_0.col3 AS col3 
FROM (SELECT DISTINCT tmp_local_edges_a5_1.col1 AS col0, tmp_local_edges_a5_1.col2 AS col1, tmp_local_edges_a5_1.col3 AS col2, tmp_local_edges_a5_1.col4 AS col3 
FROM (SELECT DISTINCT __temp__drone_local_edges_a5_0.UAV_ID AS col0, __temp__drone_local_edges_a5_0.FROM_ID AS col1, __temp__drone_local_edges_a5_0.TO_ID AS col2, __temp__drone_local_edges_a5_0.EDGE_ID AS col3, __temp__drone_local_edges_a5_0.DISTANCE AS col4 
FROM __temp__drone_local_edges AS __temp__drone_local_edges_a5_0  ) AS drone_local_edges_a5_0, (SELECT DISTINCT tmp_range_a4_1.col0 AS col0, drone_local_edges_a5_0.col1 AS col1, drone_local_edges_a5_0.col2 AS col2, drone_local_edges_a5_0.col3 AS col3, drone_local_edges_a5_0.col4 AS col4 
FROM (SELECT DISTINCT __temp__drone_local_edges_a5_0.UAV_ID AS col0, __temp__drone_local_edges_a5_0.FROM_ID AS col1, __temp__drone_local_edges_a5_0.TO_ID AS col2, __temp__drone_local_edges_a5_0.EDGE_ID AS col3, __temp__drone_local_edges_a5_0.DISTANCE AS col4 
FROM __temp__drone_local_edges AS __temp__drone_local_edges_a5_0  ) AS drone_local_edges_a5_0, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.NODE_ID AS col1, nodes_config_a4_1.POS_X AS col2, nodes_config_a4_1.POS_Y AS col3 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a4_1 
WHERE tmp_range_a4_1.col0 = drone_local_edges_a5_0.col0 AND tmp_range_a4_1.col1 = drone_local_edges_a5_0.col1 ) AS tmp_local_edges_a5_1, (SELECT DISTINCT tmp_pos_a4_2.col0 AS col0, nodes_config_a4_1.NODE_ID AS col1, nodes_config_a4_1.POS_X AS col2, nodes_config_a4_1.POS_Y AS col3 
FROM public.grid_nodes AS grid_nodes_a6_0, public.nodes_config AS nodes_config_a4_1, (SELECT DISTINCT cur_processes_a5_2.UAV_ID AS col0, nodes_config_a4_1.POS_X AS col1, nodes_config_a4_1.POS_Y AS col2, drones_cur_state_a9_0.VIEW_RANGE AS col3 
FROM public.drones_cur_state AS drones_cur_state_a9_0, public.nodes_config AS nodes_config_a4_1, public.cur_processes AS cur_processes_a5_2 
WHERE cur_processes_a5_2.UAV_ID = drones_cur_state_a9_0.UAV_ID AND nodes_config_a4_1.NODE_ID = drones_cur_state_a9_0.LOC_NODE_ID AND cur_processes_a5_2.PROC_ID = 0 ) AS tmp_pos_a4_2 
WHERE nodes_config_a4_1.NODE_ID = grid_nodes_a6_0.NODE_ID AND (tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)*(tmp_pos_a4_2.col1-nodes_config_a4_1.POS_X)+(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)*(tmp_pos_a4_2.col2-nodes_config_a4_1.POS_Y)  <=  tmp_pos_a4_2.col3*tmp_pos_a4_2.col3 ) AS tmp_range_a4_2 
WHERE tmp_local_edges_a5_1.col2 = drone_local_edges_a5_0.col2 AND tmp_local_edges_a5_1.col4 = drone_local_edges_a5_0.col4 AND tmp_local_edges_a5_1.col1 = drone_local_edges_a5_0.col1 AND tmp_local_edges_a5_1.col3 = drone_local_edges_a5_0.col3 AND tmp_range_a4_2.col0 = tmp_local_edges_a5_1.col0 AND tmp_range_a4_2.col0 = drone_local_edges_a5_0.col0 AND tmp_range_a4_2.col1 = tmp_local_edges_a5_1.col2 AND NOT EXISTS ( SELECT * 
FROM public.grid_edges AS grid_edges_a4 
WHERE grid_edges_a4.DISTANCE IS NOT DISTINCT FROM tmp_local_edges_a5_1.col4 AND grid_edges_a4.EDGE_ID IS NOT DISTINCT FROM tmp_local_edges_a5_1.col3 AND grid_edges_a4.TO_ID IS NOT DISTINCT FROM tmp_local_edges_a5_1.col2 AND grid_edges_a4.FROM_ID IS NOT DISTINCT FROM tmp_local_edges_a5_1.col1 ) ) AS __dummy__delta__insert__grid_edges_a4_0  ) AS __dummy__delta__insert__grid_edges_extra_alias; 

FOR temprec__dummy__delta__delete__grid_edges IN ( SELECT * FROM __dummy__delta__delete__grid_edges) LOOP 
            DELETE FROM public.grid_edges WHERE ROW(FROM_ID,TO_ID,EDGE_ID,DISTANCE) IS NOT DISTINCT FROM  temprec__dummy__delta__delete__grid_edges;
            END LOOP;
DROP TABLE __dummy__delta__delete__grid_edges;

INSERT INTO public.grid_edges SELECT * FROM  __dummy__delta__insert__grid_edges; 
DROP TABLE __dummy__delta__insert__grid_edges;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_edges';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_edges ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.drone_local_edges_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__temp__drone_local_edges')
    THEN
        -- RAISE NOTICE 'execute procedure drone_local_edges_materialization';
        CREATE TEMPORARY TABLE __temp__drone_local_edges WITH OIDS ON COMMIT DROP AS SELECT * FROM public.drone_local_edges;
        CREATE CONSTRAINT TRIGGER __temp__peer1_public_trigger_delta_action
        AFTER INSERT OR UPDATE OR DELETE ON 
            __temp__drone_local_edges DEFERRABLE INITIALLY DEFERRED 
            FOR EACH ROW EXECUTE PROCEDURE public.drone_local_edges_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_edges';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_edges ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_local_edges_trigger_materialization ON public.drone_local_edges;
CREATE TRIGGER drone_local_edges_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.drone_local_edges FOR EACH STATEMENT EXECUTE PROCEDURE public.drone_local_edges_materialization();

CREATE OR REPLACE FUNCTION public.drone_local_edges_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE NOTICE 'execute procedure drone_local_edges_update';
    IF TG_OP = 'INSERT' THEN
      INSERT INTO __temp__drone_local_edges SELECT (NEW).*; 
    ELSIF TG_OP = 'UPDATE' THEN
      DELETE FROM __temp__drone_local_edges WHERE ROW(UAV_ID,FROM_ID,TO_ID,EDGE_ID,DISTANCE) IS NOT DISTINCT FROM OLD;
      INSERT INTO __temp__drone_local_edges SELECT (NEW).*; 
    ELSIF TG_OP = 'DELETE' THEN
      DELETE FROM __temp__drone_local_edges WHERE ROW(UAV_ID,FROM_ID,TO_ID,EDGE_ID,DISTANCE) IS NOT DISTINCT FROM OLD;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.drone_local_edges';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.drone_local_edges ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS drone_local_edges_trigger_update ON public.drone_local_edges;
CREATE TRIGGER drone_local_edges_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.drone_local_edges FOR EACH ROW EXECUTE PROCEDURE public.drone_local_edges_update();

