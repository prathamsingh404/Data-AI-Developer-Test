import pandas as pd
import numpy as np
import os
import sqlite3
import re

# Set paths
workspace_dir = r"d:\Antigravity\AI assignmnet"
campaign_path = os.path.join(workspace_dir, "Campaign_Raw.csv")
shopify_path = os.path.join(workspace_dir, "Raw_Shopify_Sales.csv")
data_dir = os.path.join(workspace_dir, "data")
os.makedirs(data_dir, exist_ok=True)

db_path = os.path.join(data_dir, "growify.db")
campaign_db_path = os.path.join(data_dir, "cleaned_campaigns.db")
shopify_db_path = os.path.join(data_dir, "cleaned_Shopify.db")

# Report variables
report_logs = []

def log_report(msg):
    print(msg)
    report_logs.append(msg)

def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip().lower() in ['nan', 'null', '']:
        return pd.NaT
    # Try different formats
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    # Fallback to pandas generic parser
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except Exception:
        return pd.NaT

def clean_campaigns():
    log_report("--- PROCESSING CAMPAIGN DATA ---")
    df = pd.read_csv(campaign_path)
    initial_rows = len(df)
    log_report(f"Initial Campaign rows: {initial_rows}")
    
    # 1. Deduplication
    # Exact duplicate row check
    dup_count = df.duplicated().sum()
    df = df.drop_duplicates()
    log_report(f"Removed {dup_count} duplicate rows.")
    
    # 2. Date Formatting and Handling
    df['ParsedDate'] = df['Date'].apply(parse_date)
    missing_date_count = df['ParsedDate'].isnull().sum()
    log_report(f"Rows missing reporting Date: {missing_date_count}")
    
    # Justified strategy: drop rows with missing date as they cannot be mapped to the timeline.
    # But write them to an audit table first.
    audit_missing_date = df[df['ParsedDate'].isnull()].copy()
    df = df.dropna(subset=['ParsedDate'])
    df['Date'] = df['ParsedDate'].dt.strftime('%Y-%m-%d')
    df = df.drop(columns=['ParsedDate'])
    
    # 3. Clean Categorical columns
    # Data Source name
    df['Data Source name'] = df['Data Source name'].fillna('Brand A')  # default
    df['Data Source name'] = df['Data Source name'].str.strip().str.title()
    df['Data Source name'] = df['Data Source name'].replace({'Brand a': 'Brand A', 'Brand b': 'Brand B', 'Nan': 'Brand A'})
    
    # Campaign Effective Status
    df['Campaign Effective Status'] = df['Campaign Effective Status'].fillna('PAUSED')
    df['Campaign Effective Status'] = df['Campaign Effective Status'].str.strip().str.upper()
    
    # Country and Region Casing
    df['Country Funnel'] = df['Country Funnel'].fillna('India')
    df['Country Funnel'] = df['Country Funnel'].str.strip().str.title()
    df['Country Funnel'] = df['Country Funnel'].replace({'India': 'India', 'United States': 'United States', 'Usa': 'United States', 'Uk': 'United Kingdom', 'United Kingdom': 'United Kingdom', 'Uae': 'United Arab Emirates', 'United Arab Emirates': 'United Arab Emirates', 'Canada': 'Canada', 'Australia': 'Australia'})
    
    df['Geo Location Segment'] = df['Geo Location Segment'].fillna(df['Country Funnel'])
    df['Geo Location Segment'] = df['Geo Location Segment'].str.strip().str.title()
    
    # 4. Clean Numeric Columns (correcting negative values)
    numeric_cols = [
        'FB Spent Funnel (INR)', 'Amount Spent (INR)', 'Clicks (all)', 'Impressions',
        'Page Likes', 'Landing Page Views', 'Link Clicks', 'Adds to Cart',
        'Checkouts Initiated', 'Adds of Payment Info', 'Purchases',
        'Purchases Conversion Value (INR)', 'Website Contacts',
        'Messaging Conversations Started', 'Adds to Cart Conversion Value (INR)',
        'Checkouts Initiated Conversion Value (INR)', 'Adds of Payment Info Conversion Value (INR)'
    ]
    
    neg_corrections = 0
    for col in numeric_cols:
        if col in df.columns:
            # Check how many negative values
            neg_mask = df[col] < 0
            neg_count = neg_mask.sum()
            if neg_count > 0:
                neg_corrections += neg_count
                df[col] = df[col].abs()
            # Fill NaN with 0
            df[col] = df[col].fillna(0.0)
            
    log_report(f"Corrected {neg_corrections} negative value signs across numeric fields.")
    
    # 5. Parsing Campaign Naming Conventions
    # Campaign Naming: Growify | TOF / MOF / BOF / Retarget | Region Name
    # Ad Set Naming: Walkins / Whatsapp / Ecomm / Brand Visibility | Persona Name / LAL
    # Ad Naming: CA/EP | Video / SI / Carousel / Flexible / Collection | CampaignShoot / Influencer / UGC / StoreVideo | Category | Collection
    
    def parse_campaign_name(name):
        if pd.isna(name):
            return "Unknown", "Unknown", "Unknown"
        name_str = str(name).lower()
        
        # 1. Brand/Agency
        brand = "Growify" if "growify" in name_str else "Unknown"
        
        # 2. Funnel Stage
        if "tof" in name_str:
            stage = "TOF"
        elif "mof" in name_str:
            stage = "MOF"
        elif "bof" in name_str:
            stage = "BOF"
        elif "retarget" in name_str or "rt" in name_str:
            stage = "Retarget"
        elif "mof + bof" in name_str or "mof+bof" in name_str:
            stage = "MOF+BOF"
        else:
            stage = "Unknown"
            
        # 3. Region
        if "india" in name_str or "ind" in name_str:
            region = "India"
        elif "united states" in name_str or "usa" in name_str or "us" in name_str:
            region = "United States"
        elif "united kingdom" in name_str or "uk" in name_str:
            region = "United Kingdom"
        elif "united arab emirates" in name_str or "uae" in name_str:
            region = "United Arab Emirates"
        elif "canada" in name_str or "can" in name_str:
            region = "Canada"
        elif "australia" in name_str or "aus" in name_str:
            region = "Australia"
        else:
            region = "India" # default fallback based on dataset majority
            
        return brand, stage, region

    def parse_adset_name(name):
        if pd.isna(name):
            return "Unknown", "Unknown"
        name_str = str(name).lower()
        
        # 1. Channel / Type
        if "walkins" in name_str:
            channel = "Walkins"
        elif "whatsapp" in name_str or "whtsapp" in name_str:
            channel = "Whatsapp"
        elif "ecomm" in name_str or "e-comm" in name_str:
            channel = "Ecomm"
        elif "brand visibility" in name_str or "visibility" in name_str:
            channel = "Brand Visibility"
        elif "market places" in name_str or "marketplace" in name_str:
            channel = "Market Places"
        else:
            channel = "Unknown"
            
        # 2. Target Audience
        if "lal" in name_str:
            target = "LAL"
        elif "engaged" in name_str:
            target = "Engaged Shoppers"
        elif "open" in name_str:
            target = "Open"
        elif "rt" in name_str:
            target = "Retargeting"
        else:
            target = "Unknown"
            
        return channel, target

    def parse_ad_name(name):
        if pd.isna(name):
            return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"
        name_str = str(name).lower()
        
        # 1. Ad Source Type (CA/EP/Catalogue)
        if "ca" in name_str or "custom" in name_str:
            source = "CA"
        elif "ep" in name_str or "existing" in name_str:
            source = "EP"
        elif "catalogue" in name_str or "catalog" in name_str:
            source = "Catalogue"
        else:
            source = "CA"  # Default to Custom Ads
            
        # 2. Format (Video/SI/Carousel/Flexible/Collection/Reel)
        if "video" in name_str or "reel" in name_str:
            ad_format = "Video"
        elif "si" in name_str or "single image" in name_str:
            ad_format = "SI"
        elif "carousel" in name_str:
            ad_format = "Carousel"
        elif "flexible" in name_str:
            ad_format = "Flexible"
        elif "collection" in name_str:
            ad_format = "Collection"
        else:
            ad_format = "Unknown"
            
        # 3. Concept / Creator
        if "influencer" in name_str or "priya" in name_str or "karishma" in name_str or "alpa" in name_str:
            concept = "Influencer"
        elif "ugc" in name_str:
            concept = "UGC"
        elif "storevideo" in name_str:
            concept = "StoreVideo"
        elif "campaignshoot" in name_str:
            concept = "CampaignShoot"
        else:
            concept = "Brand Creative"
            
        # 4. Category
        if "kurta" in name_str:
            category = "Kurta"
        elif "festive" in name_str:
            category = "Festive"
        elif "saree" in name_str:
            category = "Saree"
        elif "dress" in name_str:
            category = "Dress"
        elif "eoss" in name_str:
            category = "EOSS"
        else:
            category = "Unknown"
            
        # 5. Collection
        if "womens" in name_str or "women" in name_str:
            collection = "Womens"
        elif "mens" in name_str or "men" in name_str:
            collection = "Mens"
        elif "apparel" in name_str:
            collection = "Apparel"
        elif "stole" in name_str:
            collection = "Stoles"
        elif "best seller" in name_str:
            collection = "Best Seller"
        else:
            collection = "General"
            
        return source, ad_format, concept, category, collection

    # Impute missing Campaign Names
    # Find mapping from Ad Set Name/Ad Name to Campaign Name
    mapping = df.dropna(subset=['Campaign Name']).groupby(['Ad Set Name', 'Ad Name'])['Campaign Name'].first().to_dict()
    
    def fill_campaign_name(row):
        c_name = row['Campaign Name']
        if pd.isna(c_name) or str(c_name).strip().lower() == 'nan':
            key = (row['Ad Set Name'], row['Ad Name'])
            return mapping.get(key, 'Growify | Unknown Campaign | Sales')
        return c_name
        
    df['Campaign Name'] = df.apply(fill_campaign_name, axis=1)
    
    # Parse Campaign Name
    campaign_parsed = df['Campaign Name'].apply(parse_campaign_name)
    df['Brand'] = [x[0] for x in campaign_parsed]
    df['Funnel Stage'] = [x[1] for x in campaign_parsed]
    df['Region'] = [x[2] for x in campaign_parsed]
    
    # Parse Ad Set Name
    adset_parsed = df['Ad Set Name'].apply(parse_adset_name)
    df['Adset Channel'] = [x[0] for x in adset_parsed]
    df['Adset Target'] = [x[1] for x in adset_parsed]
    
    # Parse Ad Name
    ad_parsed = df['Ad Name'].apply(parse_ad_name)
    df['Ad Source Type'] = [x[0] for x in ad_parsed]
    df['Ad Format'] = [x[1] for x in ad_parsed]
    df['Ad Concept'] = [x[2] for x in ad_parsed]
    df['Ad Category'] = [x[3] for x in ad_parsed]
    df['Ad Collection'] = [x[4] for x in ad_parsed]
    
    # 6. Recalculate Metrics (and audit discrepancies)
    # Original CTR / CPC etc don't exist in CSV, we will calculate them.
    # Handle division by zero.
    df['CTR'] = np.where(df['Impressions'] > 0, df['Clicks (all)'] / df['Impressions'], 0.0)
    df['CPC'] = np.where(df['Clicks (all)'] > 0, df['Amount Spent (INR)'] / df['Clicks (all)'], 0.0)
    df['CPM'] = np.where(df['Impressions'] > 0, (df['Amount Spent (INR)'] / df['Impressions']) * 1000.0, 0.0)
    df['ROI'] = np.where(df['Amount Spent (INR)'] > 0, df['Purchases Conversion Value (INR)'] / df['Amount Spent (INR)'], 0.0)
    
    # Detect severe discrepancies: e.g. Clicks > Impressions or Clicks > 0 but Impressions == 0
    severe_discrepancies = df[(df['Clicks (all)'] > df['Impressions']) | ((df['Clicks (all)'] > 0) & (df['Impressions'] == 0))]
    log_report(f"Flagged {len(severe_discrepancies)} rows with severe metric discrepancies (e.g. Clicks > Impressions).")
    
    # Save audit of missing dates
    audit_missing_date.to_csv(os.path.join(data_dir, "audit_campaigns_missing_date.csv"), index=False)
    
    # Final row count
    log_report(f"Final Campaign rows: {len(df)}")
    return df

def clean_shopify():
    log_report("\n--- PROCESSING SHOPIFY SALES DATA ---")
    df = pd.read_csv(shopify_path)
    initial_rows = len(df)
    log_report(f"Initial Shopify rows: {initial_rows}")
    
    # 1. Deduplication
    dup_count = df.duplicated().sum()
    df = df.drop_duplicates()
    log_report(f"Removed {dup_count} duplicate rows.")
    
    # 2. Date Formatting and Imputation
    df['ParsedDate'] = df['Date'].apply(parse_date)
    
    # Impute missing date using Order Created At or Transaction Timestamp
    missing_date_mask = df['ParsedDate'].isnull()
    missing_date_before = missing_date_mask.sum()
    
    def impute_date(row):
        if not pd.isna(row['Order Created At']):
            return parse_date(row['Order Created At'][:10])
        elif not pd.isna(row['Transaction Timestamp']):
            return parse_date(row['Transaction Timestamp'][:10])
        return pd.NaT
        
    df.loc[missing_date_mask, 'ParsedDate'] = df[missing_date_mask].apply(impute_date, axis=1)
    
    missing_date_after = df['ParsedDate'].isnull().sum()
    log_report(f"Shopify missing dates imputed: {missing_date_before - missing_date_after} rows. Remaining null: {missing_date_after}")
    
    # Drop rows that still have missing date (if any)
    df = df.dropna(subset=['ParsedDate'])
    df['Date'] = df['ParsedDate'].dt.strftime('%Y-%m-%d')
    df = df.drop(columns=['ParsedDate'])
    
    # 3. Clean Categorical Columns
    df['Data Source name'] = df['Data Source name'].fillna('Brand A')
    df['Data Source name'] = df['Data Source name'].str.strip().str.title()
    df['Data Source name'] = df['Data Source name'].replace({'Brand a': 'Brand A', 'Brand b': 'Brand B', 'Nan': 'Brand A'})
    
    df['Currency'] = df['Currency'].fillna('INR').str.strip().str.upper()
    df['Sales Channel'] = df['Sales Channel'].fillna('Online Store').str.strip().str.title()
    df['Country Funnel'] = df['Country Funnel'].fillna('India').str.strip().str.title()
    df['Billing Country'] = df['Billing Country'].fillna(df['Country Funnel']).str.strip().str.title()
    df['Shipping Country'] = df['Shipping Country'].fillna(df['Billing Country']).str.strip().str.title()
    
    # Normalize Country codes/names
    country_mapping = {
        'India': 'India', 'India ': 'India', 'India': 'India', 'India': 'India',
        'United States': 'United States', 'Usa': 'United States', 'United States ': 'United States',
        'United Kingdom': 'United Kingdom', 'Uk': 'United Kingdom', 'United Kingdom ': 'United Kingdom',
        'United Arab Emirates': 'United Arab Emirates', 'Uae': 'United Arab Emirates',
        'Canada': 'Canada', 'Australia': 'Australia', 'Singapore': 'Singapore', 'Saudi Arabia': 'Saudi Arabia'
    }
    df['Billing Country'] = df['Billing Country'].map(lambda x: country_mapping.get(x, x))
    df['Shipping Country'] = df['Shipping Country'].map(lambda x: country_mapping.get(x, x))
    
    # 4. Clean Numeric Columns (correcting negative values and sign flips)
    # Net Sales = Gross Sales - Discounts - Returns.
    # Total Sales = Net Sales.
    # If Net Sales or Total Sales are negative but Gross is positive, it is a sign flip.
    # If Gross is 0, then a negative Net/Total Sales is expected (refund/return).
    
    df['Gross Sales (INR)'] = df['Gross Sales (INR)'].fillna(0.0).abs()
    df['Discounts (INR)'] = df['Discounts (INR)'].fillna(0.0).abs()
    df['Returns (INR)'] = df['Returns (INR)'].fillna(0.0).abs()
    
    # Recalculate Net Sales
    df['Net Sales (INR)'] = df['Gross Sales (INR)'] - df['Discounts (INR)'] - df['Returns (INR)']
    
    # If Gross Sales is 0 and Returns > 0, Net Sales is negative (correct return)
    # Recalculate Total Sales = Net Sales
    df['Total Sales (INR)'] = df['Net Sales (INR)']
    
    # Clean Orders and Items Sold
    df['Orders'] = df['Orders'].fillna(0.0).abs()
    df['Items Sold'] = df['Items Sold'].fillna(0.0).abs()
    df['Items Returned'] = df['Items Returned'].fillna(0.0).abs()
    df['Row Count'] = df['Row Count'].fillna(1.0).abs()
    
    # Recalculate Return Rate
    df['Return Rate'] = np.where(df['Gross Sales (INR)'] > 0, df['Returns (INR)'] / df['Gross Sales (INR)'], 0.0)
    df['Average Order Value (INR)'] = np.where(df['Orders'] > 0, df['Total Sales (INR)'] / df['Orders'], 0.0)
    
    # Normalize IDs
    df['Order ID'] = df['Order ID'].fillna(-1).abs().astype(int)
    df['Customer ID'] = df['Customer ID'].fillna(-1).abs().astype(int)
    df['Product ID'] = df['Product ID'].fillna(-1).abs().astype(int)
    
    # Clean up names
    df['Product Title'] = df['Product Title'].fillna('Unknown Product')
    df['SKU'] = df['SKU'].fillna('Unknown SKU')
    df['Customer Sale Type'] = df['Customer Sale Type'].fillna('First-time').str.strip().str.title()
    
    log_report(f"Recalculated Shopify metrics (Net Sales, Total Sales, Return Rate, AOV).")
    log_report(f"Final Shopify rows: {len(df)}")
    return df

def generate_date_dimension(start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date)
    df = pd.DataFrame({'date': dates})
    df['date_key'] = df['date'].dt.strftime('%Y-%m-%d')
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['week'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.month_name()
    df['quarter'] = df['date'].dt.quarter
    df['year'] = df['date'].dt.year
    df = df.drop(columns=['date'])
    return df

def save_to_sql(campaign_df, shopify_df):
    log_report("\n--- SAVING TO SQL DATABASES ---")
    
    # Find min and max dates across both datasets for date dimension
    c_dates = pd.to_datetime(campaign_df['Date'])
    s_dates = pd.to_datetime(shopify_df['Date'])
    min_date = min(c_dates.min(), s_dates.min())
    max_date = max(c_dates.max(), s_dates.max())
    
    log_report(f"Generating date dimension from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    date_dim_df = generate_date_dimension(min_date, max_date)
    
    # Save to growify.db (unified)
    conn = sqlite3.connect(db_path)
    campaign_df.to_sql('campaign_performance', conn, if_exists='replace', index=False)
    shopify_df.to_sql('shopify_sales', conn, if_exists='replace', index=False)
    date_dim_df.to_sql('date_dimension', conn, if_exists='replace', index=False)
    conn.close()
    log_report(f"Saved all tables to unified database: {db_path}")
    
    # Save to cleaned_campaigns.db
    conn_c = sqlite3.connect(campaign_db_path)
    campaign_df.to_sql('campaign_performance', conn_c, if_exists='replace', index=False)
    date_dim_df.to_sql('date_dimension', conn_c, if_exists='replace', index=False)
    conn_c.close()
    log_report(f"Saved campaigns to: {campaign_db_path}")
    
    # Save to cleaned_Shopify.db
    conn_s = sqlite3.connect(shopify_db_path)
    shopify_df.to_sql('shopify_sales', conn_s, if_exists='replace', index=False)
    date_dim_df.to_sql('date_dimension', conn_s, if_exists='replace', index=False)
    conn_s.close()
    log_report(f"Saved shopify sales to: {shopify_db_path}")

if __name__ == "__main__":
    campaign_cleaned = clean_campaigns()
    shopify_cleaned = clean_shopify()
    save_to_sql(campaign_cleaned, shopify_cleaned)
    
    # Write quality report logs
    with open(os.path.join(workspace_dir, "python", "data_quality_report.md"), "w") as f:
        f.write("# Data Quality & Process Report\n\n")
        f.write("This report documents the issues found in the raw datasets and how they were cleaned.\n\n")
        f.write("## Process Logs\n")
        for log in report_logs:
            f.write(f"- {log}\n")
            
        f.write("\n## Imputation & Cleaning Log\n")
        f.write("1. **Deduplication**: Removed exact duplicates across both datasets.\n")
        f.write("2. **Date Imputation**: Reconstructed missing shopify sales dates from Order Created At timestamps. Campaign records with missing dates were excluded.\n")
        f.write("3. **Casing & Standardization**: String fields (platform, channel, region, status, country) normalized to uniform cases.\n")
        f.write("4. **Sign Corrections**: Negative metrics like spend, clicks, impressions, and orders corrected via absolute values.\n")
        f.write("5. **Star Schema Parse**: Expanded Campaign Name, Ad Set Name, and Ad Name fields using keyword matching parser.\n")
        f.write("6. **Metric Recalculations**: Recomputed CTR, CPC, CPM, and ROI in campaigns, and Net Sales, Total Sales, Return Rate, and AOV in Shopify sales.\n")
    
    print("\nData cleaning pipeline completed successfully!")
