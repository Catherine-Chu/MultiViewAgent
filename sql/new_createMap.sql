-- Database: multiAgent
-- Create Abstract Global Map

-- DROP TABLE "grid_nodes";
-- DROP TABLE "grid_edges";
-- DROP TABLE "charging_stations";

CREATE TABLE grid_nodes
(
	node_id int NOT NULL PRIMARY KEY,
	visit_count int DEFAULT 0,
	visited bool DEFAULT False,
	victims_num int DEFAULT 0,
	need_rescue bool DEFAULT False,
	node_type int
);

CREATE TABLE nodes_config
(
	node_id int NOT NULL PRIMARY KEY,
	pos_x int NOT NULL,
	pos_y int NOT NULL,
	visit_cap int DEFAULT 1
);

CREATE TABLE grid_edges
(
	from_id int NOT NULL,
	to_id int NOT NULL,
	edge_id int NOT NULL,
	distance real DEFAULT 1.0,
	PRIMARY KEY(from_id, to_id)
);

CREATE TABLE charging_stations_config
(
	station_id int NOT NULL PRIMARY KEY,
	node_id int NOT NULL,
	charging_cap int,
	queue_cap int,
	dock_cap int
);

CREATE TABLE charging_stations_cur_state
(
	station_id int NOT NULL PRIMARY KEY,
	is_inservice bool DEFAULT True,
	cur_utilization int,
	queue_length int,
	dock_num int,
	cur_timestamp TIMESTAMP NOT NULL
);