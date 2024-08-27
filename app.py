import streamlit as st
#import dotenv
from dotenv import load_dotenv
from PyPDF2 import PdfReader
#from llama_index.core.node_parser import SentenceSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
#from llama_index.llms import ChatOpenAI'

from langchain.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

from htmlTemplates import css, bot_template,user_template

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunk(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunk):   
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorestore = FAISS.from_texts(texts=text_chunk,embedding=embeddings)
    return vectorestore
               
def get_conversation(vectorestore):

    llm = ChatOpenAI()
    memory = ConversationBufferMemory(
        memory_key = 'chat_history',return_messages=True, max_memory_size=10)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever=vectorestore.as_retriever(),
        memory=memory
    )
    return conversation_chain
    

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
                

 
def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs sources", page_icon=":news:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history= None


    st.header("Sumamrize , review with multiple PDFs sources :news:")

    user_question = st.text_input("Ask a question about your document")
    if user_question:
        handle_userinput(user_question)
        
    st.write(user_template, unsafe_allow_html=True)
    st.write(bot_template.replace("{{MSG}}", "Hello human"), unsafe_allow_html=True)
    
    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'", accept_multiple_files=True)

        if st.button("Process"):
            with st.spinner("Processing"):
                # pdf text
                raw_text = get_pdf_text(pdf_docs)
                st.write(raw_text)
                # get text chunk
                text_chunks = get_text_chunk(raw_text)
           
                vectorstore = get_vectorstore(text_chunks)

                
       
                st.session_state.conversation = get_conversation(vectorstore)




if __name__ == "__main__":
    main()
