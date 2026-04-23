from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

app = FastAPI()

# Initialize Groq API client
groq_api_key = os.getenv("API_KEY")


# Function to load vector database

def load_vector_db(vector_db_path):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_db = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
    return vector_db

# Initialize vector database
vector_db_path = "vector_db"
vector_db = load_vector_db(vector_db_path)
print("Vector database loaded successfully\n")

# Setup re-ranking
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model="llama-3.1-8b-instant"
)
compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vector_db.as_retriever(search_kwargs={"k": 5})
)

# Define the template for responding with document context
template = """

You are an NCERT tutor.

Answer the question using ONLY the context below.

Context:
{context}

Question:
{question}

Student Level:
{level}

Instructions:
1. First explain the concept according to the student level.
2. Then give 3 short Key Points.
3. Then create 3 MCQ questions with options and correct answers.

Format the response exactly like this:

Explanation:
(write explanation)

Key Points:
• Point 1
• Point 2
• Point 3

Quiz:

Q1. Question
A) Option
B) Option
C) Option
D) Option
Answer: correct option

Q2. Question
A) Option
B) Option
C) Option
D) Option
Answer: correct option

Q3. Question
A) Option
B) Option
C) Option
D) Option
Answer: correct option


"""
prompt = ChatPromptTemplate.from_template(template)

class Query(BaseModel):
    question: str
    level: str


class DocumentInfo(BaseModel):
    page: str
    link: str
    snippet: str


class Response(BaseModel):
    answer: str
    diagram: str
    retrieved_documents: List[DocumentInfo]

@app.post("/ask", response_model=Response)
async def ask_question(query: Query):
    try:
        # Retrieve and re-rank documents
        retrieved_docs = compression_retriever.get_relevant_documents(query.question)
        
        # Collect the links and areas (metadata) where the text was found
        doc_info = []
        for doc in retrieved_docs:
            page_number = doc.metadata.get('page', 'N/A')
            doc_link = doc.metadata.get('source', 'N/A')
            doc_info.append(DocumentInfo(
                page=str(page_number),
                link=doc_link,
                snippet=doc.page_content
            ))
        
        # Combine the content of the retrieved documents
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Prepare the prompt with the retrieved context
        formatted_prompt = prompt.format(
        context=context,
    question=query.question,
    level=query.level
)
        # Generate the response using Groq API
        response = llm.invoke(formatted_prompt)
        
        # Extract the content from the AIMessage
        answer = response.content if hasattr(response, 'content') else str(response)
        
        # Generate diagram based on question
        topic = query.question.lower().replace("what is", "").strip()
        diagram_url = f"https://source.unsplash.com/600x400/?{topic},biology,diagram"
        return Response(
    answer=answer,
    diagram=diagram_url,
    retrieved_documents=doc_info
)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)