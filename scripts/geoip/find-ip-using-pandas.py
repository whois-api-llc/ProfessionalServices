import pandas as pd
import ipaddress
import sys

def ip_in_range(ip_to_check, csv_file_path, chunk_size=10000):

    names = []

    def ip_to_int(ip):
        return int(ipaddress.ip_address(ip))

    dtype_spec = {
                'mark': int, 
                'isp': str, 
                'connectionType': str, 
                'country': str, 
                'region': str,
                'city': str,
                'lat': float,
                'lng': float,
                'postalCode': str,
                'timezone': str,
                'geonameId': str
                }

    for n in dtype_spec:
        names.append(n)

    ip_to_check_int = ip_to_int(ip_to_check)

    last_row_previous_chunk = None

    for chunk in pd.read_csv(csv_file_path, dtype=dtype_spec, names=names, chunksize=chunk_size, skiprows=2):

        chunk['end_ip'] = chunk['mark'].shift(-1, fill_value=0) - 1

        if last_row_previous_chunk is not None:
            combined_rows = pd.concat([last_row_previous_chunk, chunk.iloc[:1]])
            combined_rows['end_ip'] = combined_rows['mark'].shift(-1, fill_value=0) - 1
            if (combined_rows.iloc[0]['mark'] <= ip_to_check_int <= combined_rows.iloc[0]['end_ip']):
                row = combined_rows.iloc[0]
                return True, row['isp'], row['country']

        range_row = chunk[(chunk['mark'] <= ip_to_check_int) & (chunk['end_ip'] >= ip_to_check_int)]

        if not range_row.empty:
            row = range_row.iloc[0]
            return True, row['isp'], row['country']

        last_row_previous_chunk = chunk.tail(1)

    return False, None, None

csv_file_path = sys.argv[1]
ip_to_find = sys.argv[2]
chunk_size = 100000  

found, isp, country = ip_in_range(ip_to_find, csv_file_path, chunk_size)

if found:
    print(f"IP {ip_to_find} belows to {isp}, in {country}")
else:
    print(f"IP {ip_to_find} is not in any range in the file.")
