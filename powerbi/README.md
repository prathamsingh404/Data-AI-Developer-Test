# Power BI ODBC & DAX Integration

This folder contains the documentation and references for importing the Growify Marketing data pipeline into Power BI.

### Setup Instructions:
1. **ODBC Configuration**: Connect to the local SQLite database file located at `../data/growify.db` using the standard SQLite ODBC Driver.
2. **Schema Relationships**:
   - Establish a 1-to-many relationship from `date_dimension (date_key)` to both `campaign_performance (date_key)` and `shopify_sales (date_key)`.
3. **DAX Measures**:
   - Copy-paste the exact DAX metrics provided in [Task_3_PowerBI_DAX_Measures.txt](../Task_3_PowerBI_DAX_Measures.txt) into a calculated measures table in Power BI to construct all necessary KPIs (Spend, Sales, ROI, ROAS, and Month-over-Month growth metrics).
