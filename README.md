# DocBot
A langchain / OpenAI powered Q & A chatbot implementation

This is our work in progress documentation bot. Available are the following:

**embedding.py** - the script used to chunk, embed and store our documentation files in a local Chroma database. Paths are hardwired currently, needs adaption to your needs.

**chatserver.py** - the core of the server, uses a simple session management to keep track of user sessions and chat history

**static\index.html** - a simple web page used to test the bot
