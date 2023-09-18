require 'net/http'
require 'fileutils'

# Set colors (ANSI escape codes)
RED_TEXT = "\x1b[31m"
GREEN_TEXT = "\x1b[32m"
YELLOW_TEXT = "\x1b[33m"
RESET_COLOR = "\x1b[0m"

puts "Downloading Threat Intel data from whoisxmlapi.com"
puts "Contact sales@whoisxmlapi.com for more information."

# Define the list of files to download. Modify the list to match your use case.
tidf_file_names = [
  "deny-cidrs.v4",
  "deny-cidrs.v6",
  "deny-domains",
  "deny-ips.v4",
  "deny-ips.v6",
  "hosts",
  "malicious-cidrs.v4.csv",
  "malicious-cidrs.v4.jsonl",
  "malicious-cidrs.v6.csv",
  "malicious-cidrs.v6.jsonl",
  "malicious-domains.csv",
  "malicious-domains.jsonl",
  "malicious-file-hashes.csv",
  "malicious-file-hashes.jsonl",
  "malicious-ips.v4.csv",
  "malicious-ips.v6.csv",
  "malicious-ips.v4.jsonl",
  "malicious-ips.v6.jsonl",
  "malicious-urls.csv",
  "malicious-urls.jsonl",
  "nginx-access.v4",
  "nginx-access.v6",
]

# Define the base URL where the WXA Threat Intel files are located
base_url = "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/"

# Manually define the WHOISXMLAPI.COM API Key
api_key = "<YOUR_API_KEY>"
# Better to define it in an environment variable
# api_key = ENV["WXAAPIKEY"]

# Specify the local path where you want to save the downloaded zip file
local_path = "C:/TEMP" # Use forward slashes (/) or double backslashes (\\) for Windows paths

# Get the current date in the desired format (YYYY-MM-DD)
yesterday = (Time.now - 86400).strftime("%Y-%m-%d")

puts "Preparing to download #{tidf_file_names.length} files for #{yesterday}"

iteration_count = 0

tidf_file_names.each do |tdif_file_name|
  iteration_count += 1

  # Construct the URL for tdif.YYYY-MM-DD.daily.
  tdif_get_file = "tidf.#{yesterday}.daily.#{tdif_file_name}.gz"
  complete_uri = "#{base_url}#{tdif_get_file}"

  # Create the full local path for the zip file
  local_file_path = File.join(local_path, tdif_get_file)

  begin
    puts "#{YELLOW_TEXT} #{iteration_count} ... Downloading #{tdif_get_file} file to: #{local_file_path}#{RESET_COLOR}"
    uri = URI(complete_uri)
    
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true if uri.scheme == "https"
    
    request = Net::HTTP::Get.new(uri.request_uri)
    request.basic_auth(api_key, api_key)
    
    response = http.request(request)
    
    if response.code.to_i == 200
      File.open(local_file_path, 'wb') { |file| file.write(response.body) }
      puts "#{GREEN_TEXT}  Success#{RESET_COLOR}"
    else
      puts "#{RED_TEXT}  An error occurred while downloading the #{tdif_get_file} file#{RESET_COLOR}"
      puts "#{RED_TEXT}  Error details: #{response.code} #{response.message}#{RESET_COLOR}"
    end
  rescue StandardError => e
    puts "#{RED_TEXT}  An error occurred while downloading the #{tdif_get_file} file#{RESET_COLOR}"
    puts "#{RED_TEXT}  Error details: #{e.message}#{RESET_COLOR}"
  end
end

puts "All files downloaded successfully"
