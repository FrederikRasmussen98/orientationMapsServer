import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse

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

    # Create a dated subfolder
    folder_name = datetime.now().strftime('%Y-%m-%d')
    download_folder = os.path.join(base_folder, folder_name)
    os.makedirs(download_folder, exist_ok=True)

    for download_link in download_links:
        if not download_link:
            continue

        file_url = urljoin(url, download_link)

        # Extract filename from URL
        parsed_url = urlparse(file_url)
        original_filename = os.path.basename(parsed_url.path) or "download.pdf"

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

        print(f"Downloaded: {file_path}")

if __name__ == "__main__":
    url = "https://okpan.dk/2018/event/aabent-orienteringsloeb-paa-faste-poster/"
    download_files(url)
