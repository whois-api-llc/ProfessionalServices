Collection of scripts for WHOISXMLAPI.com Geo-IP datafeed.

Professional.Services@whoisxmlapi.com

find-ip-using-csvreader.py - is a simple python script that reads the native csv provided by WHOIS and searches the entire file for the row that matches the ip address supplied as an argument.

find-ip-using-pandas.py - similar to above, using pandas dataframes.

readgeoip-addCIDR - suppliments the ip geolocation file by adding the beginning 'mark' and the ending 'mark' so you search by range.  The output creates a new CSV file.

readgeoip - searches the file created by find-ip-using-csvreader.py without conversion.

The directory sqlite-example illustrates how to load the file into a sql database and execute a query.
