CREATE TABLE delivery_task
(
	area_id int NOT NULL PRIMARY KEY,
	start_time time,
	end_time time,
	targets_num int,
	end_completed_ratio real,
	responsible_fleet_id int
);

CREATE TABLE delivery_task_targets
(
	area_id int NOT NULL,
	target_id int NOT NULL,
	find_time time,
	over_time time,
	PRIMARY KEY(area_id,target_id)
);

CREATE TABLE delivery_cur_state
(
	area_id int NOT NULL,
	target_id int NOT NULL,
	load_demand_num int,
	is_allocated bool DEFAULT False,
	is_completed bool DEFAULT False,
	responsible_uav_id int DEFAULT NULL,
	cur_timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY(area_id,target_id)
);