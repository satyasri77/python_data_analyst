import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import contextlib

# --- SETUP ---
st.set_page_config(page_title="Open Data Agent", layout="wide")
st.title("🤖 Open Source Data Agent")

# Sidebar for API Key
with st.sidebar:
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file and api_key:
    df = pd.read_csv(uploaded_file)
    st.write("### Data Preview", df.head(3))
    
    # Prompting the LLM
    user_query = st.text_input("What would you like to know or visualize?")

    if user_query:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System instructions to ensure the AI only gives us code
        prompt = f"""
        You are a Python Data Analyst. The user has a dataframe named 'df'.
        Columns: {list(df.columns)}
        Task: {user_query}
        
        Provide ONLY the Python code using pandas or matplotlib/seaborn. 
        Do not explain anything. Do not use backticks like ```python. 
        Just raw code. If a plot is needed, use plt.show() - I will capture it.
        """
        
        with st.spinner("Agent is thinking..."):
            response = model.generate_content(prompt)
            generated_code = response.text.strip()
            
            # Remove markdown formatting if the LLM added it
            if "```" in generated_code:
                generated_code = generated_code.split("```")[1].replace("python", "").strip()

        # --- THE EXECUTION ENGINE ---
        st.write("### Agent's Logic:")
        st.code(generated_code)

        try:
            st.write("### Result:")
            # We execute the code in a local environment where 'df' is available
            exec_globals = {"df": df, "pd": pd, "st": st}
            
            # Using a sub-container to catch plots
            import matplotlib.pyplot as plt
            exec(generated_code, exec_globals)
            
            # If the code generated a matplotlib figure, show it
            if plt.get_fignums():
                st.pyplot(plt.gcf())
                plt.clf() # Clear for next run
                
        except Exception as e:
            st.error(f"Execution Error: {e}")

elif not api_key:
    st.info("Please enter your Gemini API key in the sidebar to begin.")
