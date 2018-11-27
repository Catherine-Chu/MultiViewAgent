-- Old Implementation in the Old Database

-- CREATE OR REPLACE VIEW public.drone_local_nodes AS(
-- 	SELECT public.grid_nodes.*
-- 	FROM public.grid_nodes,
-- 	(SELECT public.grid_nodes.POS_X as POS_X, public.grid_nodes.POS_Y as POS_Y
-- 	FROM public.grid_nodes, (SELECT public.drones_cur_state.UAV_ID AS UAV_ID, public.drones_cur_state.POS_X AS POS_X, public.drones_cur_state.POS_Y AS POS_Y, public.drones_cur_state.VIEW_RANGE AS VIEW_RANGE
-- 							 FROM public.drones_cur_state, public.cur_processes
-- 							 WHERE public.cur_processes.PROC_ID = 0 AND public.drones_cur_state.UAV_ID = cur_processes.UAV_ID) AS tmp_pos
-- 	 WHERE POWER(tmp_pos.POS_X - public.grid_nodes.POS_X,2) + POWER(tmp_pos.POS_Y - public.grid_nodes.POS_Y,2) <= POWER(tmp_pos.VIEW_RANGE,2)
-- 	) AS tmp_range
-- 	WHERE public.grid_nodes.POS_X = tmp_range.POS_X and public.grid_nodes.POS_Y = tmp_range.POS_Y
-- );

CREATE OR REPLACE VIEW public.drone_local_nodes AS(
  SELECT tmp_range.uav_id,public.grid_nodes.*,tmp_range.pos_x as pos_x, tmp_range.pos_y as pos_y, tmp_range.visit_cap as visit_cap
  FROM public.grid_nodes,(
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )as tmp_range
  WHERE public.grid_nodes.node_id = tmp_range.node_id
);

-- CREATE OR REPLACE VIEW public.local_nodes_config AS(
--   SELECT public.nodes_config.*
--   FROM public.nodes_config, (
--     SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--     FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--     WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--     AND public.cur_processes.proc_id = 0
--     AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--   )AS tmp_pos
--   WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
-- )