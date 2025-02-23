import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import schedule
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def sanitize_filename(filename):
    """Ensure a valid filename and enforce .pdf extension."""
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    return filename

def get_filename_from_headers(response):
    """Extract filename from Content-Disposition header if available."""
    content_disp = response.headers.get("Content-Disposition")
    if content_disp and "filename=" in content_disp:
        filename = content_disp.split("filename=")[-1].strip().strip("\"'")
        return sanitize_filename(filename)
    return None

def track_downloaded_files(download_folder):
    """Load previously downloaded filenames to avoid redundant downloads."""
    downloaded_files_path = os.path.join(download_folder, "downloaded_files.txt")
    if os.path.exists(downloaded_files_path):
        with open(downloaded_files_path, "r") as file:
            return set(file.read().splitlines())
    return set()

def save_downloaded_file(download_folder, filename):
    """Save the name of the downloaded file to track it."""
    downloaded_files_path = os.path.join(download_folder, "downloaded_files.txt")
    with open(downloaded_files_path, "a") as file:
        file.write(f"{filename}\n")

def download_files(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all 'a' tags that contain 'Download' in text
    download_links = [a.get("href") for a in soup.find_all("a") if "Download" in a.get_text()]
    
    if not download_links:
        print("No download links found.")
        return

    # Create the 'data' folder if it doesn't exist
    base_folder = "data"
    os.makedirs(base_folder, exist_ok=True)

    # Don't use dated subfolder, directly use 'data'
    download_folder = base_folder
    os.makedirs(download_folder, exist_ok=True)

    # Track previously downloaded files
    downloaded_files = track_downloaded_files(download_folder)

    new_files_count = 0

    for download_link in download_links:
        if not download_link:
            continue

        file_url = urljoin(url, download_link)

        # Extract filename from URL
        parsed_url = urlparse(file_url)
        original_filename = os.path.basename(parsed_url.path) or "download.pdf"

        # Skip if file has already been downloaded
        if original_filename in downloaded_files:
            continue

        # Request file to check headers
        file_response = requests.get(file_url, headers=HEADERS, stream=True)
        if file_response.status_code != 200:
            print(f"Failed to download: {file_url} (Status: {file_response.status_code})")
            continue

        # Get filename from headers or fallback
        final_filename = get_filename_from_headers(file_response) or sanitize_filename(original_filename)

        file_path = os.path.join(download_folder, final_filename)

        # Save the file
        with open(file_path, "wb") as file:
            for chunk in file_response.iter_content(1024):
                file.write(chunk)

        # Save the filename to track it
        save_downloaded_file(download_folder, final_filename)

        new_files_count += 1
        print(f"Downloaded: {file_path}")

    # Output state with number of new files
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')} - Files downloaded: {new_files_count}")

def job():
    url = "https://okpan.dk/2018/event/aabent-orienteringsloeb-paa-faste-poster/"
    download_files(url)

# Schedule the job to run every day at 08:00
schedule.every().day.at("08:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute to run the scheduled job
