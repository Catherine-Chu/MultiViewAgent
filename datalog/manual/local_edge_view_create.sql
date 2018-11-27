-- Old Implementation in the Old Database
--
-- CREATE OR REPLACE VIEW public.drone_local_edges AS(
-- 	SELECT public.grid_edges.*
-- 	FROM public.grid_edges
-- 	WHERE
-- 	public.grid_edges.FROM_ID in
-- 	(SELECT NODE_ID
-- 	 FROM
-- 	 (SELECT public.grid_nodes.NODE_ID as NODE_ID, public.grid_nodes.POS_X as POS_X, public.grid_nodes.POS_Y as POS_Y
-- 	  FROM public.grid_nodes, (SELECT public.drones_cur_state.POS_X AS POS_X, public.drones_cur_state.POS_Y AS POS_Y, public.drones_cur_state.VIEW_RANGE AS VIEW_RANGE
-- 							   FROM public.drones_cur_state, public.cur_processes
-- 							   WHERE public.cur_processes.PROC_ID = 0 AND public.drones_cur_state.UAV_ID = cur_processes.UAV_ID) AS tmp_pos
-- 	  WHERE POWER(tmp_pos.POS_X - public.grid_nodes.POS_X,2) + POWER(tmp_pos.POS_Y - public.grid_nodes.POS_Y,2) <= POWER(tmp_pos.VIEW_RANGE,2)
-- 	 ) AS tmp_range
-- 	)
-- 	and
-- 	public.grid_edges.TO_ID in
-- 	(SELECT NODE_ID
-- 	 FROM
-- 	 (SELECT public.grid_nodes.NODE_ID as NODE_ID, public.grid_nodes.POS_X as POS_X, public.grid_nodes.POS_Y as POS_Y
-- 	  FROM public.grid_nodes, (SELECT public.drones_cur_state.POS_X AS POS_X, public.drones_cur_state.POS_Y AS POS_Y, public.drones_cur_state.VIEW_RANGE AS VIEW_RANGE
-- 							   FROM public.drones_cur_state, public.cur_processes
-- 							   WHERE public.cur_processes.PROC_ID = 0 AND public.drones_cur_state.UAV_ID = cur_processes.UAV_ID) AS tmp_pos
-- 	  WHERE POWER(tmp_pos.POS_X - public.grid_nodes.POS_X,2) + POWER(tmp_pos.POS_Y - public.grid_nodes.POS_Y,2) <= POWER(tmp_pos.VIEW_RANGE,2)
-- 	 )AS tmp_range
-- 	)
-- 	);


-- Without consider the separation of different drones' view data in one big view
-- CREATE OR REPLACE VIEW public.drone_local_edges AS(
--   SELECT public.grid_edges.*
--   FROM public.grid_edges,
--   WHERE
--   public.grid_edges.from_id IN
--   (
--   SELECT node_id
--   FROM
--   (
--     SELECT tmp_pos.uav_id, public.nodes_config.*
--     FROM public.nodes_config, (
--       SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--       FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--       WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--       AND public.cur_processes.proc_id = 0
--       AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--     )AS tmp_pos
--     WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
--   )AS tmp_r
--   )
--   AND
--   public.grid_edges.to_id IN
--   (
--   SELECT node_id
--   FROM
--   (
--     SELECT tmp_pos.uav_id, public.nodes_config.*
--     FROM public.nodes_config, (
--       SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--       FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--       WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--       AND public.cur_processes.proc_id = 0
--       AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--     )AS tmp_pos
--     WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
--   )AS tmp_r
--   )
-- );

-- CREATE OR REPLACE VIEW public.drone_local_edges AS(
--   SELECT tmp_range.uav_id, public.grid_edges.*
--   FROM public.grid_edges,
--   (
--     SELECT tmp_pos.uav_id, public.nodes_config.*
--     FROM public.nodes_config, (
--       SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--       FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--       WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--       AND public.cur_processes.proc_id = 0
--       AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--     )AS tmp_pos
--     WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
--   )AS tmp_range
--   WHERE
--   public.grid_edges.from_id IN
--   (
--   SELECT node_id
--   FROM
--   (
--     SELECT tmp_pos.uav_id, public.nodes_config.*
--     FROM public.nodes_config, (
--       SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--       FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--       WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--       AND public.cur_processes.proc_id = 0
--       AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--     )AS tmp_pos
--     WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
--   )AS tmp_r
--   WHERE tmp_r.uav_id = tmp_range.uav_id
--   )
--   AND
--   public.grid_edges.to_id IN
--   (
--   SELECT node_id
--   FROM
--   (
--     SELECT tmp_pos.uav_id, public.nodes_config.*
--     FROM public.nodes_config, (
--       SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
--       FROM public.drones_cur_state, public.nodes_config, public.cur_processes
--       WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
--       AND public.cur_processes.proc_id = 0
--       AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
--     )AS tmp_pos
--     WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
--   )AS tmp_r
--   WHERE tmp_r.uav_id = tmp_range.uav_id
--   )
-- );
CREATE OR REPLACE VIEW public.drone_local_edges AS(
SELECT TMP_1.uav_id, public.grid_edges.*
FROM
(SELECT A.uav_id as uav_id, A.node_id as from_id, B.to_id as to_id
  FROM (
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )AS A, public.grid_edges as B
  WHERE A.node_id = B.from_id
) AS TMP_1
,
(SELECT A.uav_id as uav_id,B.from_id as from_id,A.node_id as to_id
  FROM (
    SELECT tmp_pos.uav_id, public.nodes_config.*
    FROM public.nodes_config, (
      SELECT public.drones_cur_state.uav_id as uav_id, public.nodes_config.pos_x as pos_x, public.nodes_config.pos_y as pos_y, public.drones_cur_state.view_range as view_range
      FROM public.drones_cur_state, public.nodes_config, public.cur_processes
      WHERE public.drones_cur_state.loc_node_id = public.nodes_config.node_id
      AND public.cur_processes.proc_id = 0
      AND public.cur_processes.uav_id = public.drones_cur_state.uav_id
    )AS tmp_pos
    WHERE POWER(tmp_pos.pos_x-public.nodes_config.pos_x,2)+ POWER(tmp_pos.pos_y-public.nodes_config.pos_y,2)<= POWER(tmp_pos.view_range,2)
  )AS A, public.grid_edges as B
  WHERE A.node_id = B.to_id
) AS TMP_2
,
public.grid_edges

WHERE
TMP_1.uav_id = TMP_2.uav_id and TMP_1.from_id = TMP_2.from_id and TMP_1.to_id = TMP_2.to_id
and TMP_1.from_id = public.grid_edges.from_id and TMP_2.to_id = public.grid_edges.to_id
)