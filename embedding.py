import os
import re
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import CSVLoader
from bs4 import BeautifulSoup


def add_documents(document_loader, chroma_instance):
    """Adds documents from a langchain loader to the database"""
    documents = document_loader.load()
    # The customized splitters serve to be able to break at sentence level if required.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200, separators= ["\n\n", "\n", ".", ";", ",", " ", ""])
    texts = text_splitter.split_documents(documents)
    chroma_instance.add_documents(texts)

def sanitize_blog_post(content: BeautifulSoup) -> str:
    """Find all unneeded elements in the BeautifulSoup object."""
    widget_elements = content.find_all('div', {"class": "widget-area"})
    nav_elements = content.find_all('nav')
    top_elements = content.find_all('div', {"class": "top-bar"})
    author = content.find_all('div', {"class": "saboxplugin-wrap"})
    related = content.find_all('div', {"class": "rp4wp-related-posts"})

    # Remove them from the BeautifulSoup object
    for element in nav_elements+widget_elements+top_elements+author+related :
        element.decompose()

    return re.sub("\n+","\n", str(content.get_text()))

def sanitize_documentx_page(content: BeautifulSoup) -> str:
    """Find all unneeded elements in the BeautifulSoup object."""
    # remove some areas
    syntax_element = content.find('div', {"id": "i-syntax-section-content"})
    requirements_element = content.find('div', {"id": "i-requirements-section-content"})
    see_also_element = content.find('div', {"id": "i-seealso-section-content"})

    # Remove them from the BeautifulSoup object
    elements = [element for element in [syntax_element, requirements_element, see_also_element] if element is not None]

    for element in elements:
        element.decompose()

    # Now find content div element
    div_element = content.find('div', {"class": "i-body-content"})
    return re.sub("\n+","\n", str(div_element.get_text()))

def sanitize_content_page(content: BeautifulSoup) -> str:
    """Find all unneeded elements in the BeautifulSoup object."""
    # Find content div element
    div_element = content.find('div', {"id": "main-content"})
    return re.sub("\n+","\n", str(div_element.get_text()))


# Create embeddings instance
embeddings = OpenAIEmbeddings()

# Create Chroma instance
instance = Chroma(embedding_function=embeddings, 
                  persist_directory="C:\\temp\\OpenAIPlayground - V2\\combitEN")

def add_sitemap_documents(web_path, filter_urls, parsing_function, instance):
    """Adds all pages given in the web_path. Allows to filter and parse/sanitize the pages."""
    if os.path.isfile(web_path):
        # If it's a local file path, use the SitemapLoader with is_local=True
        loader = SitemapLoader(web_path=web_path, filter_urls=filter_urls, parsing_function=parsing_function, is_local=True)
    else:
        # If it's a web URL, use the SitemapLoader with web_path
        loader = SitemapLoader(web_path=web_path, filter_urls=filter_urls, parsing_function=parsing_function)
        
    loader.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    add_documents(loader, instance)

# add EN .NET help from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\input\\sitemap_net_en.xml',
                      [],
                      sanitize_documentx_page,
                      instance)

# add EN sitemap
add_sitemap_documents('https://www.combit.com/page-sitemap.xml',
                      [],
                      sanitize_content_page,
                      instance)

# add EN designer help from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\input\\sitemap_designer_en.xml',
                      [],
                      None,
                      instance)

# add EN programmer's reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\input\\sitemap_progref_en.xml',
                      [],
                      None,
                      instance)

# add EN Report Server reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\input\\sitemap_reportserver_en.xml',
                      [],
                      None,
                      instance)

# add EN AdHoc Designer reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\input\\sitemap_adhoc_en.xml',
                      [],
                      None,
                      instance)

# add EN Blog
add_sitemap_documents('https://www.combit.blog/post-sitemap.xml',
                      ["https://www.combit.blog/en/"],
                      sanitize_blog_post,
                      instance)

# add KB dump
loader = CSVLoader("C:\\temp\\OpenAIPlayground - V2\\input\\en-kb.sanitized.csv",
                   source_column='link',
                   csv_args={
                    'delimiter': ',',
                    'quotechar': '"',
                    'fieldnames': ['link','title','raw'],
                    })
add_documents(loader, instance)

instance.persist()
instance = None
