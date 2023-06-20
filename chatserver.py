import uuid
import os
import shutil
import requests
from flask import Flask, request,make_response,session, send_from_directory, jsonify
from flask_session import Session
from bs4 import BeautifulSoup
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain

app = Flask(__name__, static_folder='static')

# Initialize session management. Secret is used for cookie encryption. Change for production.
app.secret_key = "T6Otg6T3BlbkFJFow"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'C:\\temp\\OpenAIPlayground - V2\\flask_session'
Session(app)

# Store for session objects (mem cache, qa object)
session_objects = {}

# Clear all session data when restarting the server
session_dir = app.config['SESSION_FILE_DIR']
shutil.rmtree(session_dir)
os.makedirs(session_dir)

# Create embeddings instance
embeddings = OpenAIEmbeddings()

# Open Chroma vector database that is created via embedding.py
instance = Chroma(persist_directory="C:\\temp\\OpenAIPlayground - V2\\combitEN", 
                  embedding_function=embeddings)

# Initialize ChatOpenAI model
llm = ChatOpenAI(temperature=0.5, model_name="gpt-3.5-turbo")

# Prompt Templates & Messages

# Condense Prompt
condense_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_template)

# QA prompt
qa_template = """You are an enthusiastic and helpful combit support bot providing technical information about List & Label to software developers. 
Given the sections from the documentation in the context, answer the question at the end and markdown format the reply.
If you are unsure and the answer is not explicitly given in the context simply answer "Sorry, I don't know."

Context: 
{context}
Question: {question}
Answer:"""

QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["question", "context"])


@app.before_request
def check_session():
    if not session.get('active'):
        reset();
        pass

@app.route('/')
def index():
    session['active'] = 1
    return send_from_directory('static', 'index.html')

# Helper API to return the meta title of a page, used for the sources list
@app.route('/get_meta_title', methods=['GET'])
def get_meta_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is missing'})

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').get_text() if soup.title else ''
        return jsonify({'meta_title': title})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})


# Clears the current session's memory (aka start new chat)
@app.route('/reset')
def reset():
    memory_id = session.get('memory_id', None)
    if not memory_id is None:
        del session['memory_id']
        del session_objects[memory_id]

    qa_id = session.get('qa_id', None)
    if not qa_id is None:
        del session['qa_id']
        del session_objects[qa_id]

    response = make_response()
    response.status_code = 200
    return response

@app.route('/qa')
def my_api():
    # Try to retrieve values from session store. As all session objects need to be JSON serializable,
    # keep track of non serializable objects in a local store and serialize UUIDs instead.
    memory_id = session.get('memory_id', None)
    if memory_id is None:
        # We use a ConversationBufferMemory here, could be changed to one of the other available langchain memory types
        memory = ConversationBufferWindowMemory(k=5, 
                                                memory_key="chat_history", 
                                                return_messages=True, 
                                                output_key='answer')
        memory_id = str(uuid.uuid4())
        session['memory_id'] = memory_id
        session_objects[memory_id] = memory
    else:
        memory = session_objects[memory_id]

    qa_id = session.get('qa_id', None)
    if qa_id is None:
        qa = ConversationalRetrievalChain.from_llm(llm, 
                                                instance.as_retriever(), 
                                                memory=memory, 
                                                get_chat_history=lambda h : h, 
                                                verbose=True, 
                                                condense_question_prompt=CONDENSE_QUESTION_PROMPT, 
                                                combine_docs_chain_kwargs={"prompt": QA_PROMPT}, 
                                                return_source_documents=True)
        qa_id = str(uuid.uuid4())
        session['qa_id']=qa_id
        session_objects[qa_id] = qa
    else:
        qa = session_objects[qa_id]

    query = request.args.get('query')
    # Process the input string through the Q&A chain
    query_response = qa({"question": query})
    metadata_list = [obj.metadata for obj in query_response["source_documents"]]

    response = {
        'answer' : query_response["answer"],
        'sources' : metadata_list
    }

    response = make_response(jsonify(response), 200)
    response.mimetype = "application/json"
    return response

if __name__ == '__main__':
    app.run('localhost')
