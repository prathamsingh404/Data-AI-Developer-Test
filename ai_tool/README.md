# Growify Marketing AI Insight Tool - LLM over SQL

This directory contains the Streamlit-based AI Insight Tool, which leverages an LLM (Gemini) over a SQLite database to answer performance marketing questions using natural language.

---

## Architecture & Design Decisions

1. **Text-to-SQL Architecture (Bonus Feature)**:
   Rather than using static, hardcoded SQL query templates (which limit flexibility), the tool dynamically compiles natural language questions into SQLite queries. It sends the database schema and the user's question to the LLM to generate the targeted SQL statement.
2. **Auto-Correcting SQL Loop**:
   If the generated SQL fails execution (due to syntax, casing, or column-naming mistakes), the application automatically captures the error message, feeds it back to the LLM as context, and executes a second corrected query. This prevents runtime failures.
3. **Context & Conversation Memory**:
   The tool maintains session state (`st.session_state.messages`) and feeds the last few exchanges back to the LLM. This allows users to ask follow-up questions (e.g. "Which region was it?" after asking "Which region had the highest spend?").
4. **Context Window Optimization**:
   The database executes the generated SQL first. Only the resulting rows are returned and injected into the LLM context prompt to generate a final answer. This avoids blowing up the token context window with the entire database.
5. **Interactive Visualization**:
   If the SQL output includes at least one categorical column and one numeric column, the application dynamically renders interactive Plotly visualizations (bar charts or line charts) to accompany the textual explanation.

---

## Core AI Analysis Modules

The application sidebar contains direct shortcuts to generate the 4 marketing analysis reports required by the agency:
- **🏆 Winners Report**: Identifies top 3 creatives by ROAS, top 2 audience segments by CVR, best region, and the most efficient funnel stage.
- **📉 Losers Report**: Surfaces underperforming campaigns (ROAS < 1.5), highest CPA targets, and dead ad creatives (running >14 days with declining CTR).
- **💧 Funnel Leakage**: Highlights leak points in the funnel, such as campaigns with high CTR (> 3%) but low CVR (< 0.5%), or high ATC rates with low purchases.
- **🎯 Action Plan (Primary Output)**: Provides prioritized, data-driven recommendations on what to Pause, Scale, Fix, or Test, formatted for account managers.

---

## Installation & Setup

1. **Prerequisites**:
   Ensure you have installed the required libraries from the root directory:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create a `.env` file in the root directory or set the environment variable:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   The application also supports other client configurations if using OpenAI or Anthropic.

3. **Run the App**:
   From the workspace root directory, launch the Streamlit application:
   ```bash
   streamlit run ai_tool/app.py
   ```

---

## 10 Example Questions to Try

### Creative Intelligence
1. *"Which creative formats generate the highest ROAS?"*
2. *"List the top 3 creatives by ROAS along with their spend and funnel stage."*
3. *"Which ad creatives have been running for more than 14 days and have a declining CTR?"*

### Audience Intelligence
4. *"What is the CPC and ROAS breakdown by region?"*
5. *"Compare the performance of Lookalike (LAL) vs Open audience targeting."*
6. *"Which countries drive the highest average order value (AOV) in Shopify?"*

### Funnel Leaks & Financials
7. *"Which campaign had the worst CPC in March?"*
8. *"Summarise UK region performance and point out any leaks."*
9. *"List campaigns with CTR greater than 3% but CVR less than 0.5%."*
10. *"What is the blended blended ROI of Brand A vs Brand B?"*
