// Please make sure to replace <YOUR_API_KEY> with your actual API key.
// Also, ensure you have the required dependencies (node-fetch and util) installed in your Node.js project. 
// This code will download the files in parallel, and you can adjust it as needed for your use case.

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');

const writeFile = promisify(fs.writeFile);

// Set colors (ANSI escape codes)
const redText = '\x1b[31m';
const greenText = '\x1b[32m';
const yellowText = '\x1b[33m';
const blueText = '\x1b[34m';
const resetColor = '\x1b[0m';

console.log('Downloading Threat Intel data from whoisxmlapi.com');
console.log('Contact sales@whoisxmlapi.com for more information.');

// Define the list of files to download. Modify the list to match your use case.
const tidfFileNamePreFix = 'tidf.';
const tidfFileNameExtension = '.gz';
const tidfFileNames = [
  'deny-cidrs.v4',
  'deny-cidrs.v6',
  'deny-domains',
  'deny-ips.v4',
  'deny-ips.v6',
  'hosts',
  'malicious-cidrs.v4.csv',
  'malicious-cidrs.v4.jsonl',
  'malicious-cidrs.v6.csv',
  'malicious-cidrs.v6.jsonl',
  'malicious-domains.csv',
  'malicious-domains.jsonl',
  'malicious-file-hashes.csv',
  'malicious-file-hashes.jsonl',
  'malicious-ips.v4.csv',
  'malicious-ips.v6.csv',
  'malicious-ips.v4.jsonl',
  'malicious-ips.v6.jsonl',
  'malicious-urls.csv',
  'malicious-urls.jsonl',
  'nginx-access.v4',
  'nginx-access.v6',
];

// Define the base URL where the WXA Threat Intel files are located
const baseUrl = 'https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/';

// Manually define the WHOISXMLAPI.COM API Key
const apiKey = '<YOUR_API_KEY>';
// Better to define it in the environment
// const apiKey = process.env.WXAAPIKEY;

// Specify the local path where you want to save the downloaded zip file
const localPath = 'C:/TEMP'; // Use forward slashes (/) or double backslashes (\\) for Windows paths

// Get the current date in the desired format (YYYY-MM-DD)
const yesterday = new Date();
yesterday.setDate(yesterday.getDate() - 1);
const formattedDate = yesterday.toISOString().split('T')[0];

console.log(`Preparing to download ${tidfFileNames.length} files for ${formattedDate}`);

let iterationCount = 0;

async function downloadFile(tdifFileName) {
  iterationCount++;

  // Construct the URL for tdif.YYYY-MM-DD.daily.
  const tdifGetFile = `tidf.${formattedDate}.daily.${tdifFileName}${tidfFileNameExtension}`;
  const completeURI = `${baseUrl}${tdifGetFile}`;
  const localFilePath = path.join(localPath, tdifGetFile);

  try {
    console.log(`${yellowText}${iterationCount} ... Downloading ${tdifGetFile} file to: ${localFilePath}${resetColor}`);
    const response = await fetch(completeURI, {
      headers: {
        Authorization: `Basic ${Buffer.from(`${apiKey}:${apiKey}`).toString('base64')}`,
      },
    });

    if (response.ok) {
      const fileStream = fs.createWriteStream(localFilePath);
      await new Promise((resolve, reject) => {
        response.body.pipe(fileStream);
        fileStream.on('finish', resolve);
        fileStream.on('error', reject);
      });
      console.log(`${greenText}  Success${resetColor}`);
    } else {
      console.log(`${redText}  An error occurred while downloading the ${tdifGetFile} file${resetColor}`);
      console.log(`${redText}  Error details: ${response.statusText}${resetColor}`);
    }
  } catch (error) {
    console.log(`${redText}  An error occurred while downloading the ${tdifGetFile} file${resetColor}`);
    console.log(`${redText}  Error details: ${error.message}${resetColor}`);
  }
}

// Download files in parallel (you can also use a sequential loop if needed)
Promise.all(tidfFileNames.map(downloadFile))
  .then(() => console.log('All files downloaded successfully'))
  .catch((err) => console.error(`Error: ${err}`));

