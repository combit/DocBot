"""Allows to generate sitemaps for URLs that don't have one."""
import time
import os
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# pylint: disable=line-too-long,too-many-locals,invalid-name

def scroll_to_bottom(driver):
    """Scroll to the bottom of the page"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the dynamically loaded content to appear
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def add_page_to_sitemap(current_url, soup, sitemap):
    """Checks to see if a page is "worth" being added to the sitemap"""

    # Checks to see if a page is "worth" being added to the sitemap
    conditions = [
        current_url in sitemap,
        current_url.replace("index.html#!","") in sitemap,
        ("/net/" in current_url and "#" in current_url),
        ("/net/" in current_url and "webindex" in current_url),
        ("#c1tab" in current_url or "#c1popup" in current_url),
        current_url.endswith("#"),
        current_url.endswith("/")
    ]

    if any(conditions):
        return False

    if ("/net/" in current_url and "~" in current_url):
        # Check if we have enough documentation to add the current URL
        div_element = soup.find('div', class_='i-description-content')

        # Check if the div element exists and the text length is more than 256 characters
        if not div_element or len(div_element.text) < 128:
            return False
    return True

def generate_sitemap(start_url, target_name):
    """Generate a sitemap for the given start_url by following all links within the domain."""
    # Initialize the visited set and the sitemap list
    visited = set()
    sitemap = []

    # Parse the start URL
    parsed_url = urlparse(start_url)

    # Configure Selenium to use Chrome in headless mode
    options = Options()
    options.headless = True
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    try:
        # Create a stack to store URLs for iterative crawling
        url_stack = [start_url]

        while url_stack:
            url = url_stack.pop()           

            if url in visited:
                continue

            # Add the current URL to the visited set
            visited.add(url)

            # Load the web page using Selenium
            driver.get(url)

            # Get the current URL after any redirects
            current_url = driver.current_url

            # Parse the HTML using BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Find all the links on the page
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if href is not None:
                    # Resolve relative URLs
                    href = urljoin(current_url, href)
                    parsed_href = urlparse(href)

                    # Some special cases from our docs
                    encoded_href = href.replace(" ", "%20").replace("%2520", "%20")

                    # Ensure the link starts with the same domain and path as the start URL
                    compare_url = start_url
                    if (href.startswith(compare_url.split("?", 1)[0])
                            and parsed_href.netloc == parsed_url.netloc
                            and encoded_href not in visited
                            and encoded_href not in url_stack
                            and not (("#" in encoded_href) and ("/net/" in encoded_href))):
                        # Add the URL to the stack for further crawling
                        url_stack.append(encoded_href)

            # Now decide if this page is worth being added
            if not add_page_to_sitemap(current_url, soup, sitemap):
                continue

            # If we get here, the page is fine to add
            current_url = current_url.replace("index.html#!","")            
            sitemap.append(current_url)
            # Print the current URL being added
            print("Added:", current_url)

        # Extract the directory from the target path
        target_directory = os.path.dirname(target_name)

        # Check if the directory exists
        if not os.path.exists(target_directory):
            # Create the directory if it doesn't exist
            os.makedirs(target_directory)

        # Generate the sitemap.xml file
        with open(target_name, 'w', encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in sitemap:
                f.write('  <url>\n')
                f.write(f'    <loc>{url}</loc>\n')
                f.write('  </url>\n')
            f.write('</urlset>\n')

    finally:
        # Quit the Selenium driver
        driver.quit()

#DE
#generate_sitemap('https://docu.combit.net/designer/de/', '.\\input_de\\sitemap_designer.xml')
#generate_sitemap('https://docu.combit.net/adhocdesigner/de/', '.\\input_de\\sitemap_adhoc.xml')
#generate_sitemap('https://docu.combit.net/reportserver/de/', '.\\input_de\\sitemap_reportserver.xml')
#generate_sitemap('https://docu.combit.net/progref/de/', '.\\input_de\\sitemap_progref.xml')
generate_sitemap('https://docu.combit.net/net/de/', '.\\input_de\\sitemap_net.xml')

#EN
#generate_sitemap('https://docu.combit.net/net/en/', '.\\input_en\\sitemap_net.xml')
#generate_sitemap('https://docu.combit.net/designer/en/', '.\\input_en\\sitemap_designer.xml')
#generate_sitemap('https://docu.combit.net/reportserver/en/', '.\\input_en\\sitemap_reportserver.xml')
#generate_sitemap('https://docu.combit.net/progref/en/', '.\\input_en\\sitemap_progref.xml')
#generate_sitemap('https://docu.combit.net/adhocdesigner/en/', '.\\input_en\\sitemap_adhoc.xml')
