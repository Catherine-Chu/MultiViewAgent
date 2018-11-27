-- Database: multiAgent
-- Create Tables of Drones & Tasks State
CREATE TABLE drones_cur_state
(
	uav_id int NOT NULL PRIMARY KEY,
	loc_node_id int NOT NULL,
	pos_x int NOT NULL,
	pos_y int NOT NULL,
	fleet_id int NOT NULL,
	sense_range real DEFAULT 2.0,
	view_range real DEFAULT 4.0,
	load_cap int,
	load_num int,
	max_electricity real,
	cur_electricity real,
	charge_efficiency real,
	flying_state int,
	cur_path_length real,
	cur_resource_cost real,
	workload int,
	completed_workload int
);

CREATE TABLE rescue_support_tasks
(
	target_id int NOT NULL PRIMARY KEY,
	pos_x int NOT NULL,
	pos_y int NOT NULL,
	victims_num int,
	load_demand_num int,
	find_time time,
	over_time time,
	is_allocated bool DEFAULT False,
	is_completed bool DEFAULT False,
	responsible_fleet_id int,
	responsible_fleet_num int,
	responsible_uav_id int DEFAULT NULL
);

CREATE TABLE rescue_support_cur_state
(
	-- only store current state
	start_time time,
	cur_time_stamp int NOT NULL PRIMARY KEY,
	cur_working_time interval,
	has_target bool,
	target_num int,
	allocated_num int,
	completed_ratio real,
	is_completed bool,
	end_time time,
	working_uav_ratio real
);

CREATE TABLE search_coverage_tasks
(
	area_id int NOT NULL PRIMARY KEY,
	area_lefttop int,
	area_leftdown int,
	area_righttop int,
	area_rightdown int,
	area_size real,
	is_completed bool DEFAULT False,
	coverage_ratio real,
	responsible_fleet_id int,
	responsible_fleet_num int,
	start_time time,
	end_time time
);

CREATE TABLE search_coverage_state
(
	-- store changed states over time 
	time_stamp int NOT NULL,
	area_id int NOT NULL,
	time_slice real,
	coverage_ratio real,
	cur_working_time interval,
	working_uav_ratio real,
	PRIMARY KEY(time_stamp, area_id)
);


