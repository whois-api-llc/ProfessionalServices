import csv
import sys
import ipaddress

def ip_in_range(ip_to_check, csv_file_path):

    def ip_to_int(ip):
        return int(ipaddress.ip_address(ip))

    ip_to_check_int = ip_to_int(ip_to_check)

    with open(csv_file_path, "r",  newline='') as csvfile:
        reader = csv.reader(csvfile)
        previous_row = next(reader)
        previous_row = next(reader)

        for row in reader:
            start_ip = int(previous_row[0])
            end_ip = int(row[0]) - 1 
            
            if start_ip <= ip_to_check_int <= end_ip:
                return True, previous_row[1]  # Found the range

            previous_row = row 

    return False, None

# Example usage
csv_file_path = sys.argv[1]
ip_to_find = sys.argv[2]
found, range_name = ip_in_range(ip_to_find, csv_file_path)

if found:
    print(f"IP {ip_to_find} is in the range named {range_name}")
else:
    print(f"IP {ip_to_find} is not in any range in the file.")

