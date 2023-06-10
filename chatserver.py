from flask import Flask, request,make_response,session, send_from_directory
from flask_session import Session
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import uuid
import os
import shutil

app = Flask(__name__)

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
instance = Chroma(persist_directory="C:\\temp\\OpenAIPlayground - V2\\combitEN", embedding_function=embeddings)

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

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')



@app.route('/api')
def my_api():
    # Try to retrieve values from session store. As all session objects need to be JSON serializable,
    # keep track of non serializable objects in a local store and serialize UUIDs instead.
    memory_id = session.get('memory_id', None)
    if memory_id is None:
        # We use a ConversationBufferMemory here, could be changed to one of the other available langchain memory types
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')        
        memory_id = str(uuid.uuid4())
        session['memory_id'] = memory_id
        session_objects[memory_id] = memory
    else:
        memory = session_objects[memory_id]

    qa_id = session.get('qa_id', None)
    if qa_id is None:
        qa = ConversationalRetrievalChain.from_llm(llm, instance.as_retriever(), memory=memory, get_chat_history=lambda h : h, verbose=True, condense_question_prompt=CONDENSE_QUESTION_PROMPT, combine_docs_chain_kwargs={"prompt": QA_PROMPT})
        qa_id = str(uuid.uuid4())
        session['qa_id']=qa_id
        session_objects[qa_id] = qa
    else:
        qa = session_objects[qa_id]

    query = request.args.get('query')
    # Process the input string through the Q&A chain
    query_response = qa({"question": query})

    response = make_response(query_response["answer"], 200)
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.run('localhost')