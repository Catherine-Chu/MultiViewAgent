CREATE TABLE cur_processes
(
  req_uuid int PRIMARY KEY,
	proc_id int NOT NULL,
	uav_id int NOT NULL,
	r_w char NOT NULL,
	time_info time NOT NULL
);

CREATE TABLE drones_cur_charging_targets
(
  cur_timestamp TIMESTAMP NOT NULL,
  station_id int NOT NULL,
  uav_id int NOT NULL,
  weight real
);