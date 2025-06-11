import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import openai

# --------------------------
# 1. SETUP CONFIGURATION
# --------------------------
DB_USER = 'postgres'
DB_PASSWORD = 'root'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'Mutual_Fund_Data'

# OpenAI API Key (store securely in production)
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Add this to .streamlit/secrets.toml

# --------------------------
# 2. CONNECT TO DATABASE
# --------------------------
@st.cache_resource
def get_engine():
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    return engine

engine = get_engine()

# --------------------------
# 3. FUNCTION: LLM to SQL
# --------------------------
def get_sql_query_from_prompt(prompt):
    system_prompt = (
        "You are a helpful SQL assistant. Convert user queries about mutual funds into PostgreSQL queries.\n"
        "Only use the table 'mutual_funds'. Columns include: scheme_name, category, aum_cr, return_1y, return_3y, return_5y, etc."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    sql_query = response.choices[0].message.content.strip()
    return sql_query

# --------------------------
# 4. FUNCTION: EXECUTE QUERY
# --------------------------
def execute_sql(sql_query):
    try:
        df = pd.read_sql(sql_query, engine)
        return df
    except Exception as e:
        return f"SQL Error: {e}"

# --------------------------
# 5. STREAMLIT UI
# --------------------------
st.set_page_config(page_title="Mutual Fund Chatbot", layout="centered")
st.title("🤖 Mutual Fund SQL Chatbot")
st.markdown("Ask anything about mutual fund performance (e.g., *Top 5 large cap funds by 3-year return*)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat input box
user_input = st.chat_input("Ask a question about mutual funds...")
if user_input:
    st.session_state.messages.append(("user", user_input))
    with st.spinner("Generating SQL and fetching data..."):
        sql = get_sql_query_from_prompt(user_input)
        result = execute_sql(sql)
        st.session_state.messages.append(("bot", result))

# Chat display
for sender, msg in st.session_state.messages:
    with st.chat_message("user" if sender == "user" else "assistant"):
        if isinstance(msg, pd.DataFrame):
            st.dataframe(msg)
        else:
            st.markdown(msg)

