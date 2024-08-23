import os
import time
import re
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from .do_analyze import do_analyze

SAVE_DIR = './downloaded_apks'
os.makedirs(SAVE_DIR, exist_ok=True)

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        filename = 'index.html'
    if not filename.endswith('.html'):
        filename += '.html'
    return filename


def save_page(url, content):
    filename = get_filename_from_url(url)
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Saved {url} to {filepath}")


def find_all_links(url, page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    download_links, visit_links = set(), set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)

        if re.search(r'\.(exe|deb|rpm|apk|AppImage|msi)$', href):
            if is_valid_url(full_url):
                download_links.add(full_url)
        else:
            if is_valid_url(full_url):
                visit_links.add(full_url)

    return download_links, visit_links


def crawl(url):

    lst = []

    parsed_url = urlparse(url)
    filename = parsed_url.path.split('/')[-1]
    if filename.endswith('.apk'):
        item = download_apk(url)
        if item:
            lst += item
        if lst != []:
            do_analyze(lst)
        return lst

    visited_urls = set()
    download_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        urls_to_visit = [(url, 0)]

        while urls_to_visit:
            current_url, current_depth = urls_to_visit.pop()
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                print(f"Crawling: {current_url} Depth: {current_depth}")
                try:
                    page.goto(current_url, timeout=60000)
                    time.sleep(2)
                    page_content = page.content()
                except Exception as e:
                    print(f"Failed to fetch {current_url}: {e}")
                    continue

                download_links, visit_links = find_all_links(current_url, page_content)
                print("Find {} downloaded links".format(len(download_urls)))
                print("Now visited {} links".format(len(visited_urls)))

                download_urls.update(download_links)
                for link in visit_links:
                    if current_depth < 1 and link not in visited_urls:
                        urls_to_visit.append((link, current_depth + 1))
                print("{} links in queue".format(len(urls_to_visit)))

        browser.close()

    for url in download_urls:
        item = download_apk(url)
        if item:
            lst += item
            break

    if lst != []:
        do_analyze(lst)

    return lst


def download_apk(url):
    parsed_url = urlparse(url)
    filename = parsed_url.path.split('/')[-1]
    if filename.endswith('.apk'):
        try:
            print("Downloading {}".format(url))
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                save_path = os.path.join(SAVE_DIR, filename)
                with open(save_path, 'wb') as f, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in response.iter_content(chunk_size=1024):
                        f.write(data)
                        bar.update(len(data))
                print(f"Downloaded {filename} successfully.")
                return [save_path]
            else:
                print(f"Failed to download {url}. Status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Failed to download {url}. Error: {str(e)}")
            return None
    else:
        print(f"Analyze APK file only {url}")
        return None


if __name__ == "__main__":
    # start_url = "https://im.qq.com/linuxqq/index.shtml"
    # start_url = "https://localsend.org/zh-CN/download"
    start_url = "https://github.com/rustdesk/rustdesk/releases/download/1.2.6/rustdesk-1.2.6-aarch64-signed.apk"
    # start_url = "https://sj.qq.com/appdetail/com.huayi.jijiaoguanli?source=gamedetail"

    print(crawl("https://rustdesk.com/"))

