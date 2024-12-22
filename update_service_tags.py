import requests
from bs4 import BeautifulSoup
import json
import os
import re
import shutil
from datetime import datetime
import logging
import sys

# Configuration
URL = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"
TEMP_OUTPUT_DIR = "docs_temp/ranges-services-pa"
TEMP_JSON_DIR = "docs_temp/json-history"
OUTPUT_DIR = "docs/ranges-services-pa"
JSON_DIR = "docs/json-history"
TEMPLATE_FILE = "templates/index_template.html"
TEMP_INDEX_FILE = "docs_temp/index.html"
INDEX_FILE = "docs/index.html"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def ensure_directories():
    """Ensure all necessary directories exist."""
    directories = [
        "docs",            # Ensure the main docs directory exists
        TEMP_OUTPUT_DIR,   # Temporary directory for .txt files
        TEMP_JSON_DIR,     # Temporary directory for JSON files
        OUTPUT_DIR,        # Final directory for .txt files
        JSON_DIR           # Final directory for JSON history
    ]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created/verified directory: {directory}")
            # Verify directory is writable
            test_file = os.path.join(directory, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logging.info(f"Verified write permissions for: {directory}")
        except Exception as e:
            logging.error(f"Error creating/verifying directory {directory}: {str(e)}")
            raise

def fetch_latest_json_url():
    """Fetch the JSON URL from the Microsoft download page."""
    logging.info("Fetching the JSON URL from the Microsoft page.")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", string=lambda t: t and "window.__DLCDetails__" in t)
    if not script_tag:
        raise Exception("Script tag containing JSON URL not found.")

    match = re.search(r'"url":"(https://download.microsoft.com/download/[^"]+\.json)"', script_tag.string)
    if not match:
        raise Exception("JSON file URL not found in script tag.")

    json_url = match.group(1)
    logging.info(f"JSON URL successfully retrieved: {json_url}")
    return json_url

def download_json(json_url):
    """Download the JSON file from the given URL."""
    logging.info(f"Downloading JSON file from: {json_url}")
    response = requests.get(json_url)
    response.raise_for_status()

    json_filename = os.path.basename(json_url)
    json_path = os.path.join(TEMP_JSON_DIR, json_filename)

    with open(json_path, "wb") as f:
        f.write(response.content)

    if not os.path.exists(json_path):
        raise Exception(f"JSON file was not saved to {json_path}")

    logging.info(f"JSON file saved to: {json_path}")
    return json_filename, json_path

def process_json(json_path):
    """Process the JSON file and generate .txt files for each service."""
    logging.info(f"Processing JSON file: {json_path}")
    with open(json_path, "r") as f:
        data = json.load(f)

    systems = set(entry["properties"]["systemService"] for entry in data["values"] if "properties" in entry)

    for system in systems:
        if not system:
            continue
        with open(f"{TEMP_OUTPUT_DIR}/{system}.txt", "w") as f:
            addresses = [
                prefix for entry in data["values"]
                if entry["properties"]["systemService"] == system
                for prefix in entry["properties"].get("addressPrefixes", [])
            ]
            f.write("\n".join(addresses))

    version = str(data.get("changeNumber", "Unknown Version"))
    version_date = data.get("version", "Unknown Date")
    change_number = data.get("changeNumber", "Unknown ChangeNumber")
    logging.info(f"Extracted {len(systems)} systems from the JSON file.")
    return len(systems), version, version_date, change_number

def generate_directory_index(directory, output_file):
    """Generate an index.html file for the specified directory."""
    try:
        files = os.listdir(directory)
        links = [
            f'<li><a href="{file}">{file}</a></li>' for file in sorted(files) if not file.startswith('.')
        ]
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Directory Index</title>
        </head>
        <body>
            <h1>Directory Index</h1>
            <p>Click on a file to download:</p>
            <ul>
                {''.join(links)}
            </ul>
        </body>
        </html>
        """
        with open(output_file, "w") as f:
            f.write(html_content)
        logging.info(f"Generated index.html for {directory}.")
    except Exception as e:
        logging.error(f"Failed to generate index.html for {directory}: {str(e)}")
        raise

def update_index_page(json_url, version, version_date, json_filename, change_number):
    """Update the index.html page using the template."""
    if not os.path.exists(TEMPLATE_FILE):
        raise Exception(f"Template file {TEMPLATE_FILE} not found.")

    with open(TEMPLATE_FILE, "r") as template_file:
        template_content = template_file.read()

    # Replace placeholders in the template with dynamic data
    updated_content = template_content.replace("{{JSON_URL}}", json_url)
    updated_content = updated_content.replace("{{LATEST_STATIC_JSON}}", f"json-history/{json_filename}")
    updated_content = updated_content.replace("{{JSON_HISTORY_PATH}}", "json-history/")
    updated_content = updated_content.replace("{{VERSION}}", version)
    updated_content = updated_content.replace("{{GENERATED_TIME}}", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    updated_content = updated_content.replace("{{GENERATED_BY}}", "GitHub Automation")
    updated_content = updated_content.replace("{{CHANGE_NUMBER}}", str(change_number))

    # Write the updated content to the temporary index file
    with open(TEMP_INDEX_FILE, "w") as index_file:
        index_file.write(updated_content)

    logging.info(f"Index page updated and saved to temporary file: {TEMP_INDEX_FILE}")

def finalize_output(json_path, json_filename):
    """Move the temporary output to the final directory and update JSON history."""
    logging.info(f"Finalizing output: json_path={json_path}, json_filename={json_filename}")

    final_json_path = os.path.join(JSON_DIR, json_filename)
    latest_json_path = os.path.join(JSON_DIR, "ServiceTags_Public.json")
    shutil.copy2(json_path, final_json_path)
    shutil.copy2(json_path, latest_json_path)
    logging.info(f"Copied JSON files to: {final_json_path}, {latest_json_path}")

    if os.path.exists(TEMP_OUTPUT_DIR):
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        shutil.copytree(TEMP_OUTPUT_DIR, OUTPUT_DIR)
        logging.info(f"Copied TXT files to: {OUTPUT_DIR}")

    if os.path.exists(TEMP_INDEX_FILE):
        shutil.copy2(TEMP_INDEX_FILE, INDEX_FILE)
        logging.info(f"Copied index.html to: {INDEX_FILE}")

    # Generate index.html for JSON history and ranges-services-pa
    generate_directory_index(JSON_DIR, os.path.join(JSON_DIR, "index.html"))
    generate_directory_index(OUTPUT_DIR, os.path.join(OUTPUT_DIR, "index.html"))

    logging.info("Final output successfully moved to docs/")

def cleanup_temp():
    """Clean up the temporary directory."""
    if os.path.exists("docs_temp"):
        shutil.rmtree("docs_temp")
    logging.info("Temporary directory cleaned up.")

def main():
    """Main script logic."""
    try:
        logging.info("Starting service tags update process.")
        
        logging.info("Ensuring necessary directories...")
        ensure_directories()

        logging.info("Fetching the latest JSON URL...")
        json_url = fetch_latest_json_url()
        logging.info(f"Found JSON URL: {json_url}")

        logging.info("Downloading JSON...")
        json_filename, json_path = download_json(json_url)
        logging.info(f"Downloaded: {json_filename}")

        logging.info("Processing JSON...")
        total_systems, version, version_date, change_number = process_json(json_path)
        logging.info(f"Processed {total_systems} systems with change number {change_number}.")

        logging.info("Updating index page...")
        update_index_page(json_url, version, version_date, json_filename, change_number)


        logging.info("Finalizing output...")
        finalize_output(json_path, json_filename)
        
        if not os.path.exists("docs") or not os.listdir("docs"):
            raise Exception("docs directory is empty after processing.")
        
        logging.info("Processing completed successfully.")
        
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}", exc_info=True)
        raise
    finally:
        cleanup_temp()

if __name__ == "__main__":
    main()
