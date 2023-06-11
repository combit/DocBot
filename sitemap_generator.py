import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, urljoin, quote
from bs4 import BeautifulSoup


def scroll_to_bottom(driver):
    # Scroll to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the dynamically loaded content to appear
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def crawl_page(url, start_url, visited, sitemap, parsed_url, driver):
    # Add the current URL to the visited set
    visited.add(url)

    # Load the web page using Selenium
    driver.get(url)

    # Get the current URL after any redirects
    current_url = driver.current_url

    # Make sure to load dynamically generated content for the start page (KB!)
    if (url == start_url):
        scroll_to_bottom(driver)

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
                and not ("~" in href and "/net/" in href)
            ):
                # Add the link to the sitemap
                # Exclude URLs with fragments (anchor links)
                if not "#" in href:
                    sitemap.append(encoded_href)
                    # Print the current URL being added
                    print("Added:", encoded_href)

                # Recursively crawl the linked page
                crawl_page(encoded_href, start_url, visited, sitemap, parsed_url, driver)


# Main function
def generate_sitemap(start_url):
    # Initialize the visited set and the sitemap list
    visited = set()
    sitemap = []

    # Parse the start URL
    parsed_url = urlparse(start_url)

    # Configure Selenium to use Chrome in headless mode
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)

    try:
        # Crawl the start page
        crawl_page(start_url, start_url, visited, sitemap, parsed_url, driver)

        # Generate the sitemap.xml file
        with open('sitemap.xml', 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in sitemap:
                f.write(f'  <url>\n')
                f.write(f'    <loc>{url}</loc>\n')
                f.write(f'  </url>\n')
            f.write('</urlset>\n')
    finally:
        # Quit the Selenium driver
        driver.quit()


generate_sitemap("https://forum.combit.net/docs?category=9")
# generate_sitemap('https://docu.combit.net/net/en/')
# generate_sitemap('https://docu.combit.net/designer/en/')
# generate_sitemap('https://docu.combit.net/reportserver/en/')
# generate_sitemap('https://docu.combit.net/progref/en/')
# generate_sitemap('https://docu.combit.net/adhocdesigner/en/')
