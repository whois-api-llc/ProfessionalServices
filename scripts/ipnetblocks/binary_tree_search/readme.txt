
IP-Netblock Interval Tree Scripts
WHOISXMLAPI.COM, 2024
Version 1.0 by Mengchen Qu

These scripts are designed to work together to build an interval tree from a CSV file of ip-netblocks data in order to be able to query an IP address to retrieve related information.

Script 1: Building the Interval Tree
This script reads a CSV file containing ip-netblock data, constructs an interval tree based on it, and serializes it to a `.pkl` file.

Usage:
1. Dependencies:
   Ensure you have Python installed and the necessary packages:

   pip install intervaltree

2. Running the Script:
   - Save the script to a file (e.g., build_tree.py).
   - Prepare a CSV file containing ip-netblock data.
   - Run the script, which will prompt you to input:
     - The name of the CSV file that contains ip-netblock data (e.g., example_data.csv).
     - The name of the `.pkl` file to save the tree to (e.g., example_tree.pkl).

   python3 build_tree.py

3. Output:
   - The script will read data from the CSV file, build an interval tree, and serialize it to the specified `.pkl` file.
   - It also prints the time taken to build the tree and the size of the serialized file.

Script 2: Querying the Interval Tree
This script loads the serialized interval tree from a `.pkl` file and queries an IP address to retrieve related information.

Usage:
1. Dependencies:
   Ensure you have Python installed and the necessary packages:

   pip install ipaddress logging

2. Running the Script:
   - Save the script to a file (e.g., query_tree.py).
   - Prepare a `.pkl` file containing the serialized interval tree (e.g., example_tree.pkl).
   - Run the script, which will prompt you to input:
     - The name of the `.pkl` file.
     - The IP address to search for.

   python3 query_tree.py

3. Output:
   - The script loads the interval tree from the specified `.pkl` file.
   - It then queries the specified IP address and prints:
     - The ASN.
     - The country.
     - The AS name.
     - The netname.

Notes:
- Make sure to build the tree using the first script before running the second script.
