-- Database: multiAgent
-- Create Abstract Global Map

-- DROP TABLE "grid_nodes";
-- DROP TABLE "grid_edges";
-- DROP TABLE "charging_stations";

CREATE TABLE grid_nodes
(
	node_id int NOT NULL PRIMARY KEY,
	pos_x int NOT NULL,
	pos_y int NOT NULL,
	is_blocked bool NOT NULL DEFAULT False,
	visited bool DEFAULT False,
	visit_cap int DEFAULT 1,
	visit_count int DEFAULT 0,
	victims_num int DEFAULT 0,
	need_rescue bool DEFAULT False,
	node_type int
);

CREATE TABLE grid_edges
(
	from_id int NOT NULL,
	to_id int NOT NULL,
	edge_id int NOT NULL,
	distance real DEFAULT 1.0, 
	PRIMARY KEY(from_id, to_id)
);

CREATE TABLE charging_stations
(
	node_id int NOT NULL PRIMARY KEY,
	station_id int NOT NULL,
	pos_x int NOT NULL,
	pos_y int NOT NULL,
	is_inservice bool DEFAULT True,
	charging_cap int,
	cur_utilization int,
	queue_cap int,
	queue_length int,
	dock_cap int,
	dock_num int
);

