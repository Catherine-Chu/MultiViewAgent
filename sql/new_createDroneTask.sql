-- Database: multiAgent
-- Create Tables of Drones & Tasks State
CREATE TABLE drones_config
(
	uav_id int NOT NULL PRIMARY KEY,
	fleet_id int NOT NULL,
	sense_range real DEFAULT 2.0,
	load_cap int,
	max_electricity real,
	charge_efficiency real
);

CREATE TABLE drones_cur_state
(
	uav_id int NOT NULL PRIMARY KEY,
	loc_node_id int NOT NULL,
	view_range real DEFAULT 4.0,
	load_num int,
	cur_electricity real,
	flying_state int,
	cur_path_length real,
	cur_resource_cost real,
	cur_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE areas
(
  area_id int NOT NULL PRIMARY KEY,
  area_lefttop int,
	area_leftdown int,
	area_righttop int,
	area_rightdown int,
	area_size real
);

CREATE TABLE rescue_support_task
(
	area_id int NOT NULL PRIMARY KEY,
	start_time time,
	end_time time,
	targets_num int,
	end_completed_ratio real,
	responsible_fleet_id int
);

CREATE TABLE rescue_support_task_targets
(
	area_id int NOT NULL,
	target_id int NOT NULL,
	find_time time,
	over_time time,
	PRIMARY KEY(area_id,target_id)
);

CREATE TABLE rescue_support_cur_state
(
	area_id int NOT NULL,
	target_id int NOT NULL,
	victims_num int,
	load_demand_num int,
	is_allocated bool DEFAULT False,
	is_completed bool DEFAULT False,
	responsible_uav_id int DEFAULT NULL,
	cur_timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY(area_id,target_id)
);

CREATE TABLE search_coverage_task
(
	area_id int NOT NULL PRIMARY KEY,
	end_coverage_ratio real,
	responsible_fleet_id int,
	start_time time,
	end_time time
);

CREATE TABLE search_coverage_history_states
(
	area_id int NOT NULL,
	time_stamp TIMESTAMP NOT NULL,
	move_step int,
	coverage_ratio real,
	working_uav_ratio real,
	cur_working_time interval,
	is_completed bool DEFAULT False,
	PRIMARY KEY(area_id,time_stamp)
);


