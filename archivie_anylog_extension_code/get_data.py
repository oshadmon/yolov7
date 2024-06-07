import requests

def get_data(conn:str, query:str):
    headers = {
        "command": query,
        "User-Agent": "AnyLog/1.23",
        "destination": "network"
    }

    try:
        response = requests.get(url=f"http://{conn}", headers=headers)
        response.raise_for_status()
    except Exception as error:
        print(f"Failed to execute GET against {conn} (Error: {error})")
    else:
        if 200 <= int(response.status_code) < 300:
            try:
                return response.json()
            except:
                return response.text


def main():
    query1 = "sql new_company extend=(+country, +city, @ip, @port, @dbms_name, @table_name) and format = json and stat=false and timezone = utc select file_name, file, start_time::ljust(19), end_time::ljust(19), frame_count, duration from live_data order by duration --> selection (columns: ip using ip and port using port and dbms using dbms_name and table using table_name and file using file)"
    results = get_data(conn='198.74.50.131:32349', query=query1)
    for result in results['Query']:
        file_name = result['file_name']
        start_time = result['start_time']
        end_time = result['end_time']
        query2 = f"sql new_company info = (dest_type = rest) and format = json and timezone = utc select file from live_data where file_name='{file_name}'"
        output = get_data(conn='198.74.50.131:32349', query=query2)
        print(output)

if __name__ == '__main__':
    main()
