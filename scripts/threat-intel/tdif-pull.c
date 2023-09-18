#include <stdio.h>
#include <stdlib.h>
#include <string.h>
# be sure libcurl is installed
#include <curl/curl.h>

// Set colors (ANSI escape codes)
#define RED_TEXT "\x1b[31m"
#define GREEN_TEXT "\x1b[32m"
#define YELLOW_TEXT "\x1b[33m"
#define RESET_COLOR "\x1b[0m"

// Define the list of files to download. Modify the list to match your use case.
const char *tidf_file_names[] = {
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
    "nginx-access.v6"
};

// Define the base URL where the WXA Threat Intel files are located
const char *base_url = "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/";

// Manually define the WHOISXMLAPI.COM API Key
const char *api_key = "<YOUR_API_KEY>";
// Better to define it in an environment variable
// const char *api_key = getenv("WXAAPIKEY");

// Specify the local path where you want to save the downloaded zip file
const char *local_path = "C:/TEMP"; // Use forward slashes (/) or double backslashes (\\) for Windows paths

int main() {
    CURL *curl;
    CURLcode res;

    // Initialize libcurl
    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();

    if (curl) {
        // Get the current date in the desired format (YYYY-MM-DD)
        char formatted_date[11];
        time_t t = time(NULL);
        struct tm tm_info;
        strftime(formatted_date, sizeof(formatted_date), "%Y-%m-%d", localtime_r(&t, &tm_info));

        printf("Preparing to download %d files for %s\n", sizeof(tidf_file_names) / sizeof(tidf_file_names[0]), formatted_date);

        int iteration_count = 0;

        for (int i = 0; i < sizeof(tidf_file_names) / sizeof(tidf_file_names[0]); i++) {
            iteration_count++;

            // Construct the URL for tdif.YYYY-MM-DD.daily.
            char tdif_get_file[512];
            snprintf(tdif_get_file, sizeof(tdif_get_file), "tidf.%s.daily.%s.gz", formatted_date, tidf_file_names[i]);
            char complete_uri[512];
            snprintf(complete_uri, sizeof(complete_uri), "%s%s", base_url, tdif_get_file);

            // Create the full local path for the zip file
            char local_file_path[512];
            snprintf(local_file_path, sizeof(local_file_path), "%s/%s", local_path, tdif_get_file);

            // Create Authorization header
            char authorization_header[512];
            snprintf(authorization_header, sizeof(authorization_header), "Authorization: Basic %s:%s", api_key, api_key);

            // Set libcurl options
            curl_easy_setopt(curl, CURLOPT_URL, complete_uri);
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, curl_slist_append(NULL, authorization_header));
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, NULL);
            curl_easy_setopt(curl, CURLOPT_VERBOSE, 0L);

            // Perform the HTTP request
            res = curl_easy_perform(curl);

            if (res == CURLE_OK) {
                FILE *fp = fopen(local_file_path, "wb");
                if (fp) {
                    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, fwrite);
                    curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);

                    res = curl_easy_perform(curl);

                    if (res == CURLE_OK) {
                        fclose(fp);
                        printf("%s ... Downloading %s file to: %s\n", YELLOW_TEXT, iteration_count, tdif_get_file, local_file_path);
                        printf("%s  Success%s\n", GREEN_TEXT, RESET_COLOR);
                    } else {
                        fclose(fp);
                        printf("%s ... An error occurred while downloading the %s file%s\n", iteration_count, RED_TEXT, tdif_get_file, RESET_COLOR);
                        printf("%s  Error details: %s%s\n", RED_TEXT, RESET_COLOR, curl_easy_strerror(res));
                    }
                }
            } else {
                printf("%s ... An error occurred while downloading the %s file%s\n", iteration_count, RED_TEXT, tdif_get_file, RESET_COLOR);
                printf("%s  Error details: %s%s\n", RED_TEXT, RESET_COLOR, curl_easy_strerror(res));
            }
        }

        // Cleanup libcurl
        curl_easy_cleanup(curl);
        curl_global_cleanup();

        printf("All files downloaded successfully\n");
    }

    return 0;
}
