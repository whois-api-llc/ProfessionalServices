package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Set colors (ANSI escape codes)
const (
	redText   = "\x1b[31m"
	greenText = "\x1b[32m"
	yellowText = "\x1b[33m"
	resetColor = "\x1b[0m"
)

func main() {
	fmt.Println("Downloading Threat Intel data from whoisxmlapi.com")
	fmt.Println("Contact sales@whoisxmlapi.com for more information.")

	// Define the list of files to download. Modify the list to match your use case.
	tidfFileNames := []string{
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
	}

	// Define the base URL where the WXA Threat Intel files are located
	baseURL := "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/"

	// Manually define the WHOISXMLAPI.COM API Key
	apiKey := "<YOUR_API_KEY>"
	// Better to define it in an environment variable
	// apiKey := os.Getenv("WXAAPIKEY")

	// Specify the local path where you want to save the downloaded zip file
	localPath := "C:/TEMP" // Use forward slashes (/) or double backslashes (\\) for Windows paths

	// Get the current date in the desired format (YYYY-MM-DD)
	yesterday := time.Now().AddDate(0, 0, -1).Format("2006-01-02")

	fmt.Printf("Preparing to download %d files for %s\n", len(tidfFileNames), yesterday)

	iterationCount := 0

	for _, tdifFileName := range tidfFileNames {
		iterationCount++

		// Construct the URL for tdif.YYYY-MM-DD.daily.
		tdifGetFile := fmt.Sprintf("tidf.%s.daily.%s.gz", yesterday, tdifFileName)
		completeURI := baseURL + tdifGetFile

		// Create the full local path for the zip file
		localFilePath := filepath.Join(localPath, tdifGetFile)

		// Create an HTTP client
		client := &http.Client{}

		// Create an HTTP request
		req, err := http.NewRequest("GET", completeURI, nil)
		if err != nil {
			fmt.Printf("%s ... An error occurred while creating the request for %s file%s\n", iterationCount, redText, tdifGetFile, resetColor)
			fmt.Printf("%s  Error details: %s%s\n", redText, resetColor, err)
			continue
		}

		// Set the Authorization header
		req.Header.Add("Authorization", "Basic "+apiKey+":"+apiKey)

		// Perform the HTTP request
		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("%s ... An error occurred while downloading the %s file%s\n", iterationCount, redText, tdifGetFile, resetColor)
			fmt.Printf("%s  Error details: %s%s\n", redText, resetColor, err)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			// Create the local file
			localFile, err := os.Create(localFilePath)
			if err != nil {
				fmt.Printf("%s ... An error occurred while creating the local file for %s%s\n", iterationCount, redText, tdifGetFile, resetColor)
				fmt.Printf("%s  Error details: %s%s\n", redText, resetColor, err)
				continue
			}
			defer localFile.Close()

			// Copy the response body to the local file
			_, err = io.Copy(localFile, resp.Body)
			if err != nil {
				fmt.Printf("%s ... An error occurred while copying the data to the local file for %s%s\n", iterationCount, redText, tdifGetFile, resetColor)
				fmt.Printf("%s  Error details: %s%s\n", redText, resetColor, err)
				continue
			}

			fmt.Printf("%s ... Downloading %s file to: %s\n", iterationCount, yellowText, tdifGetFile, localFilePath, resetColor)
			fmt.Printf("%s  Success%s\n", greenText, resetColor)
		} else {
			fmt.Printf("%s ... An error occurred while downloading the %s file%s\n", iterationCount, redText, tdifGetFile, resetColor)
			fmt.Printf("%s  Error details: %s%s\n", redText, resetColor, resp.Status)
		}
	}

	fmt.Println("All files downloaded successfully")
}
