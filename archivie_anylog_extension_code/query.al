AL > get columns where dbms=new_company and table=live_data


Schema for DBMS: 'new_company' and Table: 'live_data'

Column Name	Column Type
row_id	integer
insert_timestamp	timestamp without time zone
tsd_name	char(3)
tsd_id	int
start_time	timestamp without time zone
end_time	timestamp without time zone
duration	float
frame_count	int
fps	float
file_name	character varying
file	character varying



sql new_company info = (dest_type = rest) and extend=(+country, +city, @ip, @port, @dbms_name, @table_name) and format = json and timezone = utc  select  file_name, file, start_time::ljust(19), end_time::ljust(19), frame_count, duration from live_data order by duration --> selection (columns: ip using ip and port using port and dbms using dbms_name and table using table_name and file using file)

sql new_company info = (dest_type = rest) and format = json and timezone = utc select file from live_feed --> selection (columns: file as file)