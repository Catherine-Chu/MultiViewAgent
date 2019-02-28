CREATE OR REPLACE VIEW public.drone_local_neighbors AS
(
  SELECT public.drone_local_nodes.uav_id, public.drones_cur_state.uav_id as neighbor_id, public.drones_cur_state.loc_node_id
  FROM public.drone_local_nodes, public.drones_cur_state
  WHERE public.drone_local_nodes.node_id = public.drones_cur_state.loc_node_id
)