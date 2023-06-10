import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import CSVLoader
from langchain.document_loaders import UnstructuredHTMLLoader
from bs4 import BeautifulSoup


# This adds documents from a langchain loader to the database. The customized splitters serve to be able to break at sentence level if required.
def add_documents(document_loader, chroma_instance):
    documents = document_loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200, separators= ["\n\n", "\n", ".", ";", ",", " ", ""])
    texts = text_splitter.split_documents(documents)
    chroma_instance.add_documents(texts)

def sanitize_blog_post(content: BeautifulSoup) -> str:
    # Find all unneeded elements in the BeautifulSoup object. 
    widget_elements = content.find_all('div', {"class": "widget-area"})
    nav_elements = content.find_all('nav')
    top_elements = content.find_all('div', {"class": "top-bar"})
    author = content.find_all('div', {"class": "saboxplugin-wrap"})
    related = content.find_all('div', {"class": "rp4wp-related-posts"})

    # Remove them from the BeautifulSoup object
    for element in nav_elements + widget_elements+top_elements+author+related :
        element.decompose()

    return str(content.get_text())

def sanitize_doctohelp_page(content: BeautifulSoup) -> str:
    # Find all unneeded elements in the BeautifulSoup object. 
    navbar_elements = content.find_all('div', {"id": "#c1sideInner"})
    nav_elements = content.find_all('nav')
    top_elements = content.find_all('div', {"id": "c1header"})

    # Remove them from the BeautifulSoup object
    for element in nav_elements + navbar_elements+top_elements:
        element.decompose()

    return str(content.get_text())



# Create embeddings instance
embeddings = OpenAIEmbeddings()

# Create Chroma instance
instance = Chroma(embedding_function=embeddings, 
                  persist_directory="C:\\temp\\OpenAIPlayground - V2\\combitEN")

def add_sitemap_documents(web_path, filter_urls, parsing_function, instance):
    if os.path.isfile(web_path):
        # If it's a local file path, use the SitemapLoader with is_local=True
        loader = SitemapLoader(web_path=web_path, filter_urls=filter_urls, parsing_function=parsing_function, is_local=True)
    else:
        # If it's a web URL, use the SitemapLoader with web_path
        loader = SitemapLoader(web_path=web_path, filter_urls=filter_urls, parsing_function=parsing_function)
        
    loader.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    add_documents(loader, instance)

# add EN designer help from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\sitemap_designer_en.xml', 
                      [], 
                      sanitize_doctohelp_page, 
                      instance)

# add EN programmer's reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\sitemap_progref_en.xml', 
                      [], 
                      sanitize_doctohelp_page, 
                      instance)

# add EN Report Server reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\sitemap_reportserver_en.xml', 
                      [], 
                      sanitize_doctohelp_page, 
                      instance)

# add EN AdHoc Designer reference from docu.combit.net
add_sitemap_documents('C:\\temp\\OpenAIPlayground - V2\\sitemap_adhoc_en.xml', 
                      [], 
                      sanitize_doctohelp_page, 
                      instance)

# add EN Blog
add_sitemap_documents('https://www.combit.blog/post-sitemap.xml', 
                      ["https://www.combit.blog/en/"], 
                      sanitize_blog_post, 
                      instance)

# add .NET help

# set the directory path
DIR_PATH = 'C:\\temp\\OpenAIPlayground - V2\\input\\docu_net_en'

# get a list of all files in the directory
files = os.listdir(DIR_PATH)

# loop over the files that do not contain a tilde character
for filename in files:
    if '~' not in filename and filename.endswith('.html') and 'websearch' not in filename and 'webindex' not in filename:
        full_path = os.path.join(DIR_PATH, filename)
        loader = UnstructuredHTMLLoader(file_path=full_path)
        add_documents(loader, instance)

# add EN sitemap
# loader = SitemapLoader(web_path='https://www.combit.com/page-sitemap.xml')
# loader.session.headers["User-Agent"] ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
# add_documents(loader, instance)

# add KB dump
loader = CSVLoader("C:\\temp\\OpenAIPlayground - V2\\input\\en-kb@forum-combit-net-2023-04-25.dcqresult.sanitized.csv", 
                   source_column='title', 
                   csv_args={
    'delimiter': ',',
    'quotechar': '"',
    'fieldnames': ['title','raw'],
})

add_documents(loader, instance)

instance.persist()
instance = None
