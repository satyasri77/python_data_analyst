import streamlit as st
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="Data Chatbot", layout="centered")

# Initialize session state for chat history and data
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None

# --- STEP 1: API SETUP ---
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("AIzaSyBWmFj37olGM5UMRXvEVlDEikxvYnZyaC0", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    st.info("Get a key at aistudio.google.com")

# --- STEP 2: THE GATEKEEPER (UPLOAD) ---
if st.session_state.df is None:
    st.title("📂 Welcome! Let's analyze some data.")
    st.write("Upload an Excel or CSV file to start the chatbot.")
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)
            st.rerun() # Refresh to show the chatbot
        except Exception as e:
            st.error(f"Error loading file: {e}")
    st.stop() # Stops execution here until a file is uploaded

# --- STEP 3: THE CHATBOT INTERFACE ---
st.title("📊 Data Intelligence Agent")
st.write(f"Active File: `{len(st.session_state.df)} rows loaded`")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "code" in message:
            st.code(message["code"])

# User Input
if prompt := st.chat_input("Ask me to filter, graph, or summarize..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    if not api_key:
        st.error("Please enter an API key in the sidebar!")
    else:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Give the AI the context of the data
        system_context = f"""
        You are a Data Agent. Dataframe 'df' has columns: {list(st.session_state.df.columns)}.
        User query: {prompt}
        
        Rules:
        1. If asked for a graph, use 'matplotlib' or 'pandas' plotting.
        2. Provide Python code inside triple backticks.
        3. Provide a brief text explanation of what you found.
        """
        
        with st.chat_message("assistant"):
            response = model.generate_content(system_context)
            full_text = response.text
            
            # Simple logic to extract code from the response
            code = ""
            if "```python" in full_text:
                code = full_text.split("```python")[1].split("```")[0].strip()
            elif "```" in full_text:
                code = full_text.split("```")[1].split("```")[0].strip()

            st.markdown(full_text)
            
            # Execute code if found
            if code:
                try:
                    # Provide local variables for execution
                    exec_context = {"df": st.session_state.df, "pd": pd, "plt": plt, "st": st}
                    exec(code, exec_context)
                    # Handle plots
                    if plt.get_fignums():
                        st.pyplot(plt.gcf())
                        plt.clf()
                except Exception as e:
                    st.error(f"Failed to run code: {e}")
            
            # Save to history
            history_entry = {"role": "assistant", "content": full_text}
            if code: history_entry["code"] = code
            st.session_state.messages.append(history_entry)
