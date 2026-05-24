# Data Quality & Process Report

This report documents the issues found in the raw datasets and how they were cleaned.

## Process Logs
- --- PROCESSING CAMPAIGN DATA ---
- Initial Campaign rows: 10028
- Removed 310 duplicate rows.
- Rows missing reporting Date: 654
- Corrected 2705 negative value signs across numeric fields.
- Flagged 1035 rows with severe metric discrepancies (e.g. Clicks > Impressions).
- Final Campaign rows: 9064
- 
--- PROCESSING SHOPIFY SALES DATA ---
- Initial Shopify rows: 5680
- Removed 21 duplicate rows.
- Shopify missing dates imputed: 470 rows. Remaining null: 11
- Recalculated Shopify metrics (Net Sales, Total Sales, Return Rate, AOV).
- Final Shopify rows: 5648
- 
--- SAVING TO SQL DATABASES ---
- Generating date dimension from 2025-12-23 to 2026-12-03
- Saved all tables to unified database: d:\Antigravity\AI assignmnet\data\growify.db
- Saved campaigns to: d:\Antigravity\AI assignmnet\data\cleaned_campaigns.db
- Saved shopify sales to: d:\Antigravity\AI assignmnet\data\cleaned_Shopify.db

## Imputation & Cleaning Log
1. **Deduplication**: Removed exact duplicates across both datasets.
2. **Date Imputation**: Reconstructed missing shopify sales dates from Order Created At timestamps. Campaign records with missing dates were excluded.
3. **Casing & Standardization**: String fields (platform, channel, region, status, country) normalized to uniform cases.
4. **Sign Corrections**: Negative metrics like spend, clicks, impressions, and orders corrected via absolute values.
5. **Star Schema Parse**: Expanded Campaign Name, Ad Set Name, and Ad Name fields using keyword matching parser.
6. **Metric Recalculations**: Recomputed CTR, CPC, CPM, and ROI in campaigns, and Net Sales, Total Sales, Return Rate, and AOV in Shopify sales.
