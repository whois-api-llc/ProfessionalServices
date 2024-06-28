There are three files in this repo:

   - build_geoIPv4_interval_tree.py
   - build_geoIPv6_interval_tree.py
   - check_geoIPv4_interval_tree.py

These files are provided "as is", and come with no warranty or support, but are provided as an example of what you can do to build a smiliar MMDB type
data structure to perform fast lookups.  The first step in the process is to build a 'pickle' (.pkl) file that serializes the data and writes the object
to disk.

The second step is to read the pickle object file, and load it as an interval tree.  Once loaded, you can begin performing ultra-fast lookups.

Again, these files are provided as an example. With some creativity and resouces, you can:

* add parallel pocessing during the creation and loading process to speed it up.
* once loaded, offer it as an internal API service or integrate it into your code line.

We've also separated the IPv4 from the IPv6 creation since the two IP addresses are very diffent, but the code could easily be merged.

