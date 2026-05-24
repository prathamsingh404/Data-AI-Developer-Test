import streamlit as st
import pandas as pd
import numpy as np
import os
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from dotenv import load_dotenv

# Load env variables (for GEMINI_API_KEY)
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Growify Marketing AI Insights",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS with premium glassmorphism
st.markdown("""
<style>
    .reportview-container {
        background: #0f111a;
    }
    .main {
        background-color: #0f111a;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    .sidebar .sidebar-content {
        background-color: #1a1d2d;
    }
    h1, h2, h3 {
        color: #6366f1;
        font-weight: 700;
    }
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    .card {
        background: rgba(26, 29, 45, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .chat-bubble-user {
        background-color: #312e81;
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 10px;
        color: #f8fafc;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-ai {
        background-color: #1e1b4b;
        border: 1px solid #4338ca;
        padding: 15px;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 10px;
        color: #f8fafc;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "growify.db")

# Helper to run SQL queries safely
def run_query(sql_query):
    # SQL Injection protection - Prevent destructive operations
    forbidden_keywords = ['DROP', 'DELETE', 'ALTER', 'UPDATE', 'INSERT', 'CREATE', 'REPLACE']
    upper_query = sql_query.upper()
    for kw in forbidden_keywords:
        if re.search(rf'\b{kw}\b', upper_query):
            return None, f"Security Error: The query contains forbidden keyword '{kw}' and was blocked."
            
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

# LLM Client wrapper supporting both Gemini and Groq
def get_llm_response(prompt):
    provider = st.session_state.get("llm_provider", "Gemini")
    
    if provider == "Groq":
        api_key = st.session_state.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None, "Groq API key is missing. Please configure it in the sidebar or environment variables."
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-specdec",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'], None
        except Exception as e:
            return None, f"Groq API call failed: {str(e)}"
            
    else:
        # Default to Gemini
        api_key = st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None, "Gemini API key is missing. Please configure it in the sidebar or environment variables."

        # Method 1: Try new google-genai library
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text, None
        except Exception as e_new:
            # Method 2: Fallback to google-generativeai library
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                return response.text, None
            except Exception as e_old:
                return None, f"Failed to call Gemini API. New SDK Error: {str(e_new)}. Old SDK Error: {str(e_old)}"

# Database schema summary to pass to the LLM
DB_SCHEMA = """
Database: growify.db
Tables:

1. campaign_performance:
   - date_key (TEXT, Format: YYYY-MM-DD)
   - data_source_name (TEXT, values: "Brand A", "Brand B")
   - campaign_name (TEXT)
   - campaign_effective_status (TEXT, values: "ACTIVE", "PAUSED")
   - adset_name (TEXT)
   - ad_name (TEXT)
   - country_funnel (TEXT, target country)
   - geo_location_segment (TEXT)
   - fb_spent_funnel_inr (REAL)
   - amount_spent_inr (REAL, primary ad spend)
   - clicks (REAL)
   - impressions (REAL)
   - page_likes (REAL)
   - landing_page_views (REAL)
   - link_clicks (REAL)
   - adds_to_cart (REAL)
   - checkouts_initiated (REAL)
   - adds_of_payment_info (REAL)
   - purchases (REAL, ad conversion count)
   - purchases_conversion_value_inr (REAL, ad conversion revenue value)
   - ctr (REAL, Click-Through Rate = (Clicks / Impressions) * 100)
   - cpc (REAL, Cost Per Click = Spend / Clicks)
   - cpm (REAL, Cost Per Mille = Spend / Impressions * 1000)
   - roas (REAL, ROAS = Purchases Conversion Value / Spend)
   - brand (TEXT, e.g. "Growify")
   - funnel_stage (TEXT, values: "TOF", "MOF", "BOF", "Retarget", "MOF+BOF", "Unknown")
   - region (TEXT, e.g. "India", "United States", "United Kingdom", "United Arab Emirates", "Canada", "Australia")
   - adset_channel (TEXT, values: "Walkins", "Whatsapp", "Ecomm", "Brand Visibility", "Market Places", "Unknown")
   - adset_target (TEXT, values: "LAL", "Engaged Shoppers", "Open", "Retargeting", "Unknown")
   - ad_source_type (TEXT, values: "CA", "EP", "Catalogue")
   - ad_format (TEXT, values: "Video", "SI", "Carousel", "Flexible", "Collection", "Unknown")
   - ad_concept (TEXT, e.g. "Influencer", "UGC", "StoreVideo", "CampaignShoot", "Brand Creative")
   - ad_category (TEXT, e.g. "Kurta", "Festive", "Saree", "Dress", "EOSS", "Unknown")
   - ad_collection (TEXT, e.g. "Womens", "Mens", "Apparel", "Stoles", "Best Seller", "General")

2. shopify_sales:
   - data_source_name (TEXT, values: "Brand A", "Brand B")
   - date_key (TEXT, Format: YYYY-MM-DD)
   - currency (TEXT, values: "INR")
   - sales_channel (TEXT)
   - order_id (INTEGER PRIMARY KEY)
   - order_name (TEXT, e.g. "#1001")
   - gross_sales_inr (REAL)
   - net_sales_inr (REAL)
   - total_sales_inr (REAL, actual sales revenue)
   - orders (REAL, 1.0 for valid order, 0.0 for return/refund)
   - returns_inr (REAL)
   - return_rate (REAL, Returns / Gross Sales)
   - items_sold (REAL)
   - items_returned (REAL)
   - average_order_value_inr (REAL, Total Sales / Orders)
   - discounts_inr (REAL)
   - sku (TEXT)
   - customer_sale_type (TEXT, values: "First-Time", "Returning")
   - customer_id (INTEGER)
   - billing_country (TEXT)
   - shipping_country (TEXT, primary market locator)

3. date_dimension:
   - date_key (TEXT, Primary Key, format YYYY-MM-DD)
   - day (INTEGER)
   - day_name (TEXT)
   - week (INTEGER)
   - month (INTEGER)
   - month_name (TEXT)
   - quarter (INTEGER)
   - year (INTEGER)
"""

# Compile user question into SQL with auto-correction
def text_to_sql(user_question, chat_history_context=""):
    system_prompt = f"""
You are an expert SQL engineer. Your task is to translate a marketing analyst's natural language question into a single, valid SQLite SQL query that runs on the schema below:

{DB_SCHEMA}

RULES:
1. Return ONLY the SQL query inside a markdown code block starting with ```sql and ending with ```. Do not explain the query. Do not add text before or after the code block.
2. Ensure you query the correct columns using the snake_case definitions provided. Only output SELECT queries.
3. Use case-insensitive matches where appropriate (using LIKE) for string matching.
4. For date comparisons, date columns are TEXT in 'YYYY-MM-DD' format. Use 'YYYY-MM-DD' literals.
5. If calculating aggregated ratios, handle division-by-zero using CASE or COALESCE.
6. Context from previous chat messages:
{chat_history_context}

Question: {user_question}
"""
    response_text, error = get_llm_response(system_prompt)
    if error:
        return None, f"Error generating SQL: {error}"
    
    # Extract SQL from markdown code block
    sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        sql = sql_match.group(1).strip()
    else:
        sql = response_text.strip()
        
    return sql, None

# Synthesize query results into natural language answer
def sql_to_text(user_question, sql_query, query_results, chat_history_context=""):
    results_str = query_results.to_string(index=False)
    
    system_prompt = f"""
You are an expert Marketing Performance Analyst at Growify, a performance marketing agency.
Your objective is to answer the user's question using the SQL query and the exact dataset results returned from the database.

User Question: {user_question}
Executed SQL Query: {sql_query}
Query Results:
{results_str}

RULES:
1. Provide a professional, direct, and actionable answer in plain English. No jargon, no hedging.
2. Refer to the data signals directly (e.g., mention exact figures, spend, ROAS, and campaign names).
3. Frame recommendations in terms of scaling what works, pausing losers, fixing leaks, or testing new segments.
4. Address the user directly as a colleague/account manager.
5. Context from previous chat messages:
{chat_history_context}
"""
    response_text, error = get_llm_response(system_prompt)
    if error:
        return f"Error synthesizing answer: {error}"
    return response_text

# Initialize session state for chatbot
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar options and report actions
st.sidebar.title(" Growify Control Panel")
st.sidebar.markdown("---")

st.sidebar.subheader("API Configuration")
provider = st.sidebar.selectbox("LLM Provider", ["Gemini", "Groq"], index=0)
st.session_state["llm_provider"] = provider

if provider == "Gemini":
    gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
    st.session_state["gemini_api_key"] = gemini_key
else:
    groq_key = st.sidebar.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    st.session_state["groq_api_key"] = groq_key

st.sidebar.markdown("---")

# Predefined analytical reports
st.sidebar.subheader(" Core AI Analysis Modules")

winners_clicked = st.sidebar.button(" Report 1: Winners Report")
losers_clicked = st.sidebar.button(" Report 2: Losers Report")
leakage_clicked = st.sidebar.button(" Report 3: Funnel Leakage")
action_clicked = st.sidebar.button(" Report 4: Action Plan")

st.sidebar.markdown("---")
st.sidebar.subheader(" Sample Questions to Try:")
st.sidebar.info("""
- "Which campaign had the worst CPC in March?"
- "Summarise UK region performance"
- "What is the overall ROAS of Brand A?"
- "Which creative formats perform best by ROAS?"
- "Which countries drive the highest average order value?"
""")

# Quick header stats from database
st.title(" Growify Marketing AI Analyst")
st.write("Ask questions about ad spend, Facebook campaign metrics, and actual Shopify sales revenue.")

db_exists = os.path.exists(DB_PATH)
if db_exists:
    # Compute quick stats
    spend_df, _ = run_query('SELECT SUM("Amount Spent (INR)") as total_spend FROM campaign_performance')
    sales_df, _ = run_query('SELECT SUM("Total Sales (INR)") as total_sales FROM shopify_sales')
    
    total_spend = spend_df['total_spend'].iloc[0] if spend_df is not None else 0
    total_sales = sales_df['total_sales'].iloc[0] if sales_df is not None else 0
    overall_roas = total_sales / total_spend if total_spend > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="card">
            <h4 style="margin:0;color:#94a3b8;">Aggregated Ad Spend</h4>
            <h2 style="margin:5px 0 0 0;color:#e2e8f0;">₹{total_spend:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card">
            <h4 style="margin:0;color:#94a3b8;">Shopify Sales Revenue</h4>
            <h2 style="margin:5px 0 0 0;color:#10b981;">₹{total_sales:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card">
            <h4 style="margin:0;color:#94a3b8;">Overall Blended ROAS</h4>
            <h2 style="margin:5px 0 0 0;color:#6366f1;">{overall_roas:.2f}x</h2>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning(" Cleaned database file 'growify.db' was not found in 'data/' directory. Please run the clean_data.py pipeline first.")

# Process Predefined Report Clicks
report_prompt = None
if winners_clicked:
    report_prompt = "Generate the Winners Report. Show the top 3 creatives by ROAS, top 2 audience segments by CVR, best performing region by ROAS, and the most efficient funnel stage."
elif losers_clicked:
    report_prompt = "Generate the Losers Report. Show the bottom 3 campaigns by ROAS (with spend and days running), dead creatives (running >14 days with declining CTR), highest CPA audience segments, and platforms underperforming (ROAS < 1.5)."
elif leakage_clicked:
    report_prompt = "Generate the Funnel Leakage Report. Find campaigns with high CTR (> 3%) but low CVR (< 0.5%) pointing to landing page issues, and campaigns with high ATC but low purchase rates pointing to pricing or trust barriers."
elif action_clicked:
    report_prompt = "Generate the prioritized Action Plan. Output a numbered list of instructions (Pause, Scale, Fix, Test) tied to named data signals. Avoid jargon and be highly specific."

if report_prompt:
    st.session_state.messages.append({"role": "user", "content": report_prompt})

# Render chat history
for message in st.session_state.messages:
    role_class = "chat-bubble-user" if message["role"] == "user" else "chat-bubble-ai"
    st.markdown(f'<div class="{role_class}">{message["content"]}</div>', unsafe_allow_html=True)

# User input input box
user_input = st.chat_input("Ask about campaign performance, leaks, audience, or budget optimizations...")

# If we have user input (either typed or from report button)
if user_input or report_prompt:
    query_to_process = user_input if user_input else report_prompt
    
    # If it was entered via chat box, add to session
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)
    
    # Generate SQL
    with st.spinner("Compiling natural language to SQL..."):
        # Format past context
        context_str = ""
        for m in st.session_state.messages[-4:-1]: # last 3 messages context
            context_str += f"{m['role']}: {m['content']}\n"
            
        sql_query, error = text_to_sql(query_to_process, context_str)
        
    if error:
        st.error(error)
    elif sql_query:
        # Display Generated SQL inside an expander for transparency
        with st.expander(" Generated SQL Query", expanded=False):
            st.code(sql_query, language="sql")
            
        # Execute Query
        with st.spinner("Querying database..."):
            query_results, query_error = run_query(sql_query)
            
            # Simple Auto-correction Loop: If SQL fails, send error back to LLM to correct
            if query_error:
                st.warning(f"Initial SQL failed: {query_error}. Attempting auto-correction...")
                correction_prompt = f"""
The SQL query you generated failed with this error: {query_error}
Query was: {sql_query}
Please correct the SQL query to fix the error. Return ONLY the corrected code block.
"""
                corrected_sql, _ = text_to_sql(correction_prompt, context_str)
                if corrected_sql:
                    sql_query = corrected_sql
                    with st.expander(" Corrected SQL Query", expanded=True):
                        st.code(sql_query, language="sql")
                    query_results, query_error = run_query(sql_query)
            
        if query_error:
            st.error(f"SQL Execution Failed: {query_error}")
        elif query_results is not None:
            # Display raw query results inside expander
            with st.expander(" SQL Query Result Rows", expanded=False):
                st.dataframe(query_results)
                
            # Synthesize Answer
            with st.spinner("Synthesizing analysis into recommendation..."):
                answer = sql_to_text(query_to_process, sql_query, query_results, context_str)
                
            # Render AI Answer
            st.markdown(f'<div class="chat-bubble-ai">{answer}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Visual Graph Helper: If the result table has a date or category and numbers, plot it!
            numeric_cols = query_results.select_dtypes(include=[np.number]).columns.tolist()
            text_cols = query_results.select_dtypes(include=['object']).columns.tolist()
            
            if len(numeric_cols) > 0 and len(text_cols) > 0 and len(query_results) > 1:
                # Pick primary columns for graphing
                x_col = text_cols[0]
                y_col = numeric_cols[0]
                
                # If date is present, use date as x axis
                date_cols = [c for c in text_cols if 'date' in c.lower()]
                if date_cols:
                    x_col = date_cols[0]
                    
                with st.expander(" Interactive Visualization", expanded=True):
                    # Sort if timeline
                    if x_col in date_cols:
                        query_results = query_results.sort_values(by=x_col)
                        fig = px.line(query_results, x=x_col, y=y_col, title=f"{y_col} trend over time", template="plotly_dark")
                    else:
                        fig = px.bar(query_results, x=x_col, y=y_col, color=y_col, title=f"{y_col} by {x_col}", template="plotly_dark")
                        
                    st.plotly_chart(fig, use_container_width=True)
