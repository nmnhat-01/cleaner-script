import re
import os
import sys
import json
from urllib.parse import urlparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging
import requests

def find_url_end_idx(subset_from_start):
    double_quote_idx = subset_from_start.find('"')
    if double_quote_idx == -1:
        double_quote_idx = sys.maxsize

    single_quote_idx = subset_from_start.find("'")
    if single_quote_idx == -1:
        single_quote_idx = sys.maxsize

    closed_parenthesis_idx = subset_from_start.find(')')
    if closed_parenthesis_idx == -1:
        closed_parenthesis_idx = sys.maxsize

    space_idx = subset_from_start.find(' ')
    if space_idx == -1:
        space_idx = sys.maxsize

    end_tag_idx = subset_from_start.find('</')
    if end_tag_idx == -1:
        end_tag_idx = sys.maxsize

    return min(
        double_quote_idx,
        single_quote_idx,
        closed_parenthesis_idx,
        space_idx,
        end_tag_idx
    )

def replace_url(url):
    mid_idx = len(url) // 2
    half_end_url = url[-mid_idx:]
    if ('.css' in half_end_url or
        '.js' in half_end_url or
        # images https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types
        '.apng' in half_end_url or
        '.avif' in half_end_url or
        '.gif' in half_end_url or
        '.jpeg' in half_end_url or
        '.jpg' in half_end_url or
        '.png' in half_end_url or
        '.webp' in half_end_url or
        '.bmp' in half_end_url or
        '.ico' in half_end_url or
        '.cur' in half_end_url or
        # fonts https://www.w3schools.com/css/css3_fonts.asp
        '.ttf' in half_end_url or
        '.otf' in half_end_url or
        '.woff2' in half_end_url or
        '.woff' in half_end_url or
        '.eot' in half_end_url or
        '.svg' in half_end_url
    ):
        # https://docs.python.org/3/library/urllib.parse.html
        o = urlparse(url)
        return o._replace(scheme='', netloc='', query='', fragment='').geturl()[1:]

    # internal/external URLs
    return '#'

def download_file(url, saved_path, file_path):
    # if file exist, skip download
    file_full_path = os.path.join(saved_path, file_path)
    if os.path.isfile(file_full_path):
        return

    response = requests.get(url, verify=False)
    if response.status_code == 200:
        # create parent directory if not exist
        file_dir = os.path.dirname(file_full_path)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        with open(file_full_path, 'wb') as f:
            f.write(response.content)
        logger.debug(f"File saved to {file_full_path}")
    else:
        logger.debug(f"Failed to download {url}. Status code: {response.status_code}")

# INPUT PATH
html_path = './v9betplus/v9bet/v9betplus.com/index.html'

# create output dir
project_name = html_path[html_path.index('/'):html_path.rindex('/')]
saved_path = f".{project_name}"

# saved_path = html_path[:html_path.rindex('/')]
if not os.path.exists(saved_path):
    os.makedirs(saved_path)

# LOGGING
# Create a logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Create a formatter to define the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler to write logs to a file
log_file_path = os.path.join(saved_path, 'cleaner.log')
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # You can set the desired log level for console output
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# find url start, end index
with open(html_path, 'r', encoding='utf-8') as file:
    html_content = file.read()
    
d = {}

matches = re.finditer(r'https?:\/\/', html_content)
# matches = re.finditer(r'https?:\\?\/\\?\/', html_content)
for m in matches:
    start = m.start()
    subset_from_start = html_content[start: start+512]

    # find end
    end = find_url_end_idx(subset_from_start)
    old_url = html_content[start:start+end]

    # replace url
    new_url = replace_url(old_url)

    # construct into dict key, value will be replaced url
    d[old_url] = new_url

    # download file
    if new_url == '#':
        continue

    download_file(old_url, saved_path, new_url)


# sort dict by key length - longest site replace first - avoid overlap replacement
new_d = {}
for k in sorted(d, key=len, reverse=True):
    new_d[k] = d[k]

# replace
for old, new in new_d.items():
    html_content = html_content.replace(old, new)

# save to new html
# path = os.path.join(saved_path, 'index.html')

new_html_path = html_path[html_path.index('/'):]
new_html_path = f".{new_html_path}"

# new_html_path = html_path
with open(new_html_path, 'w', encoding='utf8') as fp:
    fp.write(html_content)

# save mapping
# path = os.path.join(saved_path, 'url_mapping.json')
# with open(path, 'w') as fp:
#     json.dump(d, fp, indent=2)

