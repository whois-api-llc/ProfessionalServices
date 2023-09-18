
// add these dependencies to the Cargo.toml file
//
// [dependencies]
// reqwest = "0.11"
// tokio = { version = "1", features = ["full"] }
//
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE};
use reqwest::{Client, Error};
use std::fs::File;
use std::io::copy;
use std::path::Path;
use tokio::fs::create_dir_all;
use tokio::main;

// Set colors (ANSI escape codes)
const RED_TEXT: &str = "\x1b[31m";
const GREEN_TEXT: &str = "\x1b[32m";
const YELLOW_TEXT: &str = "\x1b[33m";
const RESET_COLOR: &str = "\x1b[0m";

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Define the list of files to download. Modify the list to match your use case.
    let tidf_file_names = vec![
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
    ];

    // Define the base URL where the WXA Threat Intel files are located
    let base_url = "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/";

    // Manually define the WHOISXMLAPI.COM API Key
    let api_key = "<YOUR_API_KEY>";
    // Better to define it in the environment
    // let api_key = std::env::var("WXAAPIKEY").unwrap_or("<YOUR_API_KEY>".to_string());

    // Specify the local path where you want to save the downloaded zip file
    let local_path = "C:/TEMP"; // Use forward slashes (/) or double backslashes (\\) for Windows paths

    // Get the current date in the desired format (YYYY-MM-DD)
    let yesterday = chrono::Utc::today() - chrono::Duration::days(1);
    let formatted_date = yesterday.format("%Y-%m-%d").to_string();

    println!("Preparing to download {} files for {}", tidf_file_names.len(), formatted_date);

    // Create a reqwest client
    let client = Client::new();

    let mut tasks = vec![];

    for tdif_file_name in tidf_file_names {
        let base_url_clone = base_url.to_string();
        let api_key_clone = api_key.to_string();
        let local_path_clone = local_path.to_string();
        let formatted_date_clone = formatted_date.clone();

        let task = tokio::spawn(async move {
            let iteration_count = {
                static ITERATION_COUNT: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
                ITERATION_COUNT.fetch_add(1, std::sync::atomic::Ordering::SeqCst)
            };

            // Construct the URL for tdif.YYYY-MM-DD.daily.
            let tdif_get_file = format!("tidf.{}.daily.{}{}", formatted_date_clone, tdif_file_name, ".gz");
            let complete_uri = format!("{}{}", base_url_clone, tdif_get_file);
            let local_file_path = format!("{}/{}", local_path_clone, tdif_get_file);

            let authorization_header = format!("Basic {}", base64::encode(format!("{}:{}", api_key_clone, api_key_clone)));

            let response = client
                .get(&complete_uri)
                .header(CONTENT_TYPE, "application/octet-stream")
                .header(AUTHORIZATION, authorization_header)
                .send()
                .await?;

            if response.status().is_success() {
                create_dir_all(Path::new(&local_path_clone)).await?;

                let mut dest = File::create(&local_file_path).await?;
                let content = response.bytes().await?;
                copy(&mut content.as_ref(), &mut dest)?;

                println!("{} ... Downloading {} file to: {}", iteration_count, tdif_get_file, local_file_path);
                println!("{}  Success", GREEN_TEXT);
            } else {
                println!("{} ... An error occurred while downloading the {} file", iteration_count, tdif_get_file);
                println!("{}  Error details: {}", RED_TEXT, response.status());
            }

            Ok(())
        });

        tasks.push(task);
    }

    // Wait for all tasks to complete
    for task in tasks {
        task.await?;
    }

    println!("All files downloaded successfully");

    Ok(())
}
