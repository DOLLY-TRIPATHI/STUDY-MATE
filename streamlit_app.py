# streamlit_app.py
import streamlit as st
import json
import time
from duckduckgo_search import DDGS
import urllib.parse

from streamlit_lottie import st_lottie
import requests

# Function to load lottie animation from URL
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Lottie animation URL (free from lottiefiles.com)
lottie_learning = load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_jcikwtux.json")

# Display animation at the top
st_lottie(lottie_learning, speed=1, height=150, key="learning")



# At the very top, below imports

st.markdown(
    """
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(to right, #f0f8ff, #e6f7ff);
        color: #000000;
        font-family: 'Segoe UI', sans-serif;
    }
    /* Button style */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        padding: 10px 20px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    /* Input box style */
    .stTextInput>div>div>input {
        border-radius: 10px;
        padding: 10px;
        font-size: 16px;
    }
    /* Card style for answer */
    .answer-card {
        background-color: #f2f2f2;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px #aaaaaa;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Function to fetch images

@st.cache_data
def get_images(query, max_results=2):
    images = []

    try:
        time.sleep(3)   # rate limit avoid

        with DDGS() as ddgs:
            results = ddgs.images(
                query + " labelled biology diagram",
                max_results=max_results
            )

            for r in results:
                if "image" in r:
                    images.append(r["image"])

    except Exception as e:
        st.warning("⚠️ Image service busy. Try again in a few seconds.")

    return images


# Function to create YouTube search link
def get_video_link(query):
    query_str = query.replace(" ", "+")
    return f"https://www.youtube.com/results?search_query={query_str}+explanation"
# Set the FastAPI backend URL
BACKEND_URL = "http://localhost:8000"

# ==================== HEADER ====================
st.markdown("## 📚 StudyMate")
st.markdown("""
<div style='text-align:center; background: linear-gradient(to right, #6a11cb, #2575fc); 
            padding:20px; border-radius:10px; color:white; font-family:Segoe UI'>
    <h1>StudyMate</h1>
    <p style='font-size:18px'>Learn Smarter, Not Harder</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")
st.markdown("**Ask any question and get answers, diagrams, and videos instantly!**")
st.markdown("---")

level = st.selectbox(
    "Select Student Level",
    ["Small Kid", "Middle School", "High School"]
)
# Input box for user question
question = st.text_input("Enter your question:")

if st.button("Ask"):
    if question:
        # Send request to FastAPI backend
        response = requests.post(
    f"{BACKEND_URL}/ask",
    json={
        "question": question,
        "level": level
    }
)        
        if response.status_code == 200:
            data = response.json()
            
            # Display the answer
            st.subheader("📘 Explanation + Notes + Quiz")
           # st.write(data["answer"])
            st.markdown(f'<div class="answer-card">{data["answer"]}</div>', unsafe_allow_html=True)
            
            
            # Display retrieved documents
            st.subheader("Retrieved Documents:")
            for doc in data["retrieved_documents"]:
                with st.expander(f"Document (Page: {doc['page']})"):
                    st.write(f"Link: {doc['link']}")
                    st.write("Snippet:")
                    st.write(doc['snippet'])
            
            # Display related diagram
            st.subheader("🖼 Related Diagrams")
            images = get_images(question,max_results=2) 
            if images:
                for img in images:
                    st.image(img, use_container_width=True)
            else:
                    st.info("No diagrams available right now. Please try again.")
            # Display related video
            st.subheader("🎥 Explanation Video")
            video_url = get_video_link(question)
            st.markdown(f"[Watch related video]({video_url})")
            

            #Download button (answer download)
            st.download_button("📥 Download Answer", data=data["answer"], file_name="answer.txt")
            
            # Previous Questions / History (yahan add karo)
            if "history" not in st.session_state:
                st.session_state.history = []

            st.session_state.history.append({"question": question, "answer": data["answer"]})

            st.subheader("🕘 Previous Questions")
            for q in reversed(st.session_state.history[-5:]):
                with st.expander(q["question"]):
                    st.write(q["answer"])
    else:
            st.error(f"Error: {response.status_code} - {response.text}")
else:
        st.warning("Please enter a question.")

# Add some instructions or information about the system

st.sidebar.header("ℹ️ About")
st.sidebar.info(
    """
    This is an interactive NCERT Q&A Helper.
    - Enter your question in the box
    - Select your level
    - Click 'Ask' to get answers with diagrams and videos
    """
)
st.sidebar.markdown("[Watch Demo Video](https://www.youtube.com/)")