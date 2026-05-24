# Marketing AI Insight Tool: Text-to-SQL Architecture

This directory details the functionality of the Python application built for Task 4, which leverages a Large Language Model (LLM) to perform natural language analysis against a structured SQLite database.

## System Architecture and Capabilities

1. **Dynamic Text-to-SQL Execution**
   The application avoids rigid, pre-defined templates. Instead, it dynamically injects the database schema (`growify.db`) into the LLM context alongside the user's analytical query. The LLM returns a valid SQLite statement which the application executes natively.

2. **Automated Error Correction Mechanism**
   If a generated SQL statement fails during execution (e.g., syntax errors, invalid column references), the application traps the exception, passes the error traceback context back to the LLM, and attempts a secondary query generation. This ensures system robustness without requiring user intervention.

3. **Contextual Memory**
   The application maintains a rolling session history, allowing users to ask follow-up questions referencing previous answers (e.g., querying for specific campaign metrics after a general regional summary).

4. **Data Visualization Handling**
   Following successful SQL execution, the application analyzes the output datatypes. If valid categorical and numeric distributions are detected, the tool dynamically renders interactive Plotly visualizations to augment the tabular data.

## Integrated Analytical Modules

The interface provides predefined queries tailored to marketing performance analysis:
- **Winners Report**: Identifies top performing creatives by Return on Ad Spend (ROAS) and optimal audience segments by Conversion Rate (CVR).
- **Losers Report**: Flags underperforming campaigns, non-converting high CPA targets, and stale creatives exhibiting declining engagement metrics.
- **Funnel Leakage Analysis**: Analyzes drop-offs between high Click-Through Rate (CTR) and low CVR, isolating issues related to landing page friction or checkout abandonment.
- **Action Plan Generation**: Synthesizes output data into actionable, prioritized operational directives (Pause, Scale, Fix, Test).

## Setup and Execution

Ensure the main database pipeline (`Task_1_Data_Cleaning.py`) has been executed first to generate the necessary `data/growify.db` file.

1. **Environment Configuration**: Set the API key variable within a local `.env` file in the root directory.
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

2. **Launch Application**: Execute the Streamlit server from the command line.
   ```
   streamlit run Task_4_Bonus_AI_Tool.py
   ```
