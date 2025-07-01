import streamlit as st
import requests
import time
from typing import Dict, Any

# Page config
st.set_page_config(
    page_title="AI Code Explainer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced Custom CSS styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #ffffff 0%, #000000 100%);
        min-height: 100vh;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: #ffffff;
        border-radius: 20px;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }

    .main-header {
        text-align: center;
        padding: 2rem 1rem;
        background: #333333;
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 2px solid #ffffff;
    }

    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
    }

    .main-header p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #222222;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #222222;
        background-color: #e6e6e6;
        padding: 0.5rem;
        border-radius: 10px;
    }

    .code-container, .explanation-container {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .stButton > button {
        background: #000000;
        color: white;
        border: 2px solid #ffffff;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
    }

    .stButton > button:hover {
        background: #ffffff;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('''
<div class="main-header">
    <h1>AI Code Explainer</h1>
    <p>Transform complex code into clear, understandable explanations!</p>
</div>
''', unsafe_allow_html=True)

# Sidebar Configuration
st.markdown('<div class="section-header">Configuration Settings</div>', unsafe_allow_html=True)
api_key = st.secrets.get("ibm", {}).get("api_key", "")
project_id = st.secrets.get("ibm", {}).get("project_id", "")

if api_key and project_id:
    st.success("Credentials loaded from secrets")
else:
    st.warning("Please enter your credentials")
    api_key = st.text_input("IBM API Key", type="password")
    project_id = st.text_input("Project ID")

region = st.selectbox("Region", ["us-south", "eu-de", "eu-gb", "jp-tok"])
model_choice = st.selectbox("AI Model", [
    "meta-llama/llama-3-2-3b-instruct",
    "google/flan-ul2",
    "mistralai/mixtral-8x7b-instruct-v01"
])
programming_language = st.selectbox("Programming Language", [
    "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Other"
])
detail_level = st.select_slider("Detail Level", ["Beginner", "Intermediate", "Advanced"], value="Beginner")

# Sample code snippets
sample_codes = {
    "Python - Fibonacci": '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))''',

    "JavaScript - Array Filter": '''const numbers = [1,2,3,4,5,6,7,8,9,10];
const evenNumbers = numbers.filter(num => num % 2 === 0);
console.log(evenNumbers);''',

    "Python - Class Example": '''class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height''',

    "Custom": "Enter your own code..."
}

# Layout
st.markdown('<div class="section-header">Code Input</div>', unsafe_allow_html=True)
sample_choice = st.selectbox("Choose a sample or enter custom code:", list(sample_codes.keys()))

code_input = st.text_area("Enter your code:", value="" if sample_choice == "Custom" else sample_codes[sample_choice], height=300)

def get_explanation_prompt(code: str, language: str, detail_level: str) -> str:
    return f"""Please explain this {language} code in plain English, suitable for a {detail_level.lower()} programmer.

Code:
```{language.lower()}
{code}
```

1. Overview
2. Step-by-step explanation
3. Key concepts
4. Possible improvements
"""

def get_access_token(api_key: str) -> str:
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get access token: {response.text}")

def explain_code_with_watsonx(code: str, language: str, detail_level: str, api_key: str, project_id: str, region: str, model: str) -> str:
    try:
        access_token = get_access_token(api_key)
        url = f"https://{region}.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        prompt = get_explanation_prompt(code, language, detail_level)
        body = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 1000,
                "temperature": 0.3,
                "repetition_penalty": 1.1
            },
            "model_id": model,
            "project_id": project_id
        }
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            return response.json()['results'][0]['generated_text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# Explanation output
st.markdown('<div class="section-header">AI Explanation</div>', unsafe_allow_html=True)
if st.button("Explain Code", disabled=not code_input or not api_key or not project_id):
    if code_input.strip():
        with st.spinner("Analyzing your code..."):
            explanation = explain_code_with_watsonx(code_input, programming_language, detail_level, api_key, project_id, region, model_choice)
            st.markdown('<div class="explanation-container">', unsafe_allow_html=True)
            st.markdown("**AI Explanation:**")
            st.write(explanation)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please enter some code to explain.")
