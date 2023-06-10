from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.document_loaders import CSVLoader
from langchain.document_loaders import ReadTheDocsLoader
from langchain.document_loaders import UnstructuredHTMLLoader
from bs4 import BeautifulSoup
import os

# This adds documents from a langchain loader to the database. The customized splitters serve to be able to break at sentence level if required.
def add_documents(loader, instance):
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=60, separators= ["\n\n", "\n", ".", ";", ",", " ", ""])
    texts = text_splitter.split_documents(documents)
    instance.add_documents(texts)

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

# Create embeddings instance
embeddings = OpenAIEmbeddings()

# Create Chroma instance
instance = Chroma(embedding_function=embeddings, persist_directory="C:\\temp\\OpenAIPlayground - V2\\combitEN")

# add EN Blog sitemap. Set user agent to circumvent bot filter.
loader = SitemapLoader(web_path='https://www.combit.blog/post-sitemap.xml', filter_urls=["https://www.combit.blog/en/"], parsing_function=sanitize_blog_post)
loader.session.headers["User-Agent"] ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
add_documents(loader, instance)


# add documentation PDFs
pdf_files = ["C:\\temp\\OpenAIPlayground - V2\\input\\Designer-Manual.pdf",
            "C:\\temp\\OpenAIPlayground - V2\\input\\Ad-hoc Designer-Manual.pdf",
            "C:\\temp\\OpenAIPlayground - V2\\input\\Programmers-Manual.pdf",
            "C:\\temp\\OpenAIPlayground - V2\\input\\ServicePack.pdf",
            "C:\\temp\\OpenAIPlayground - V2\\input\\ReportServer.pdf"]

for file_name in pdf_files:
    loader = UnstructuredPDFLoader(file_name)
    add_documents(loader, instance)

# add .NET help

# set the directory path
dir_path = 'C:\\temp\\OpenAIPlayground - V2\\input\\docu_net_en'

# get a list of all files in the directory
files = os.listdir(dir_path)

# loop over the files that do not contain a tilde character
for filename in files:
    if '~' not in filename and filename.endswith('.html') and 'websearch' not in filename and 'webindex' not in filename:
        full_path = os.path.join(dir_path, filename)
        loader = UnstructuredHTMLLoader(file_path=full_path)
        add_documents(loader, instance)

# add EN sitemap
loader = SitemapLoader(web_path='https://www.combit.com/page-sitemap.xml')
loader.session.headers["User-Agent"] ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
add_documents(loader, instance)

# add KB dump
loader = CSVLoader("C:\\temp\\OpenAIPlayground - V2\\input\\en-kb@forum-combit-net-2023-04-25.dcqresult.sanitized.csv", csv_args={
    'delimiter': ',',
    'quotechar': '"',
    'fieldnames': ['title','raw']
})

add_documents(loader, instance)

instance.persist()
instance = None