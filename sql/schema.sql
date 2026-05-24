-- =========================================================================
-- GROWIFY DATA ARCHITECTURE: UNIFIED SQL SCHEMA AND QUERIES
-- =========================================================================
-- This file contains the complete SQL architecture for the Growify project.
-- It defines the Star Schema tables, establishes primary/foreign keys, 
-- applies performance indexes, and provides base queries for Power BI and AI.
-- =========================================================================

PRAGMA foreign_keys = ON;

-- =========================================================================
-- 1. DIMENSION TABLES
-- =========================================================================

-- Table: date_dimension
-- Purpose: Serves as the central time-axis for the Star Schema.
-- Why it's needed: E-commerce sales and marketing spend happen on different 
-- schedules. A shared Date Dimension allows Power BI and the AI tool to 
-- correctly join and aggregate data across both fact tables without missing dates.
CREATE TABLE IF NOT EXISTS date_dimension (
    date_key TEXT PRIMARY KEY,       -- Format: YYYY-MM-DD
    day INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL
);

-- =========================================================================
-- 2. FACT TABLES
-- =========================================================================

-- Table: campaign_performance
-- Purpose: Fact table storing daily ad delivery and conversion metrics.
-- Structure: Lightly denormalized. Instead of breaking out separate dimensions 
-- for Brand, Region, and Ad Format, we keep them in the fact table to minimize 
-- JOIN complexity for the AI tool, improving LLM query generation accuracy.
CREATE TABLE IF NOT EXISTS campaign_performance (
    date_key TEXT NOT NULL,                -- FK to date_dimension
    data_source_name TEXT NOT NULL,        
    campaign_name TEXT NOT NULL,           
    campaign_effective_status TEXT,        
    adset_name TEXT,                       
    ad_name TEXT,                          
    country_funnel TEXT,                   
    geo_location_segment TEXT,             
    fb_spent_funnel_inr REAL DEFAULT 0,
    amount_spent_inr REAL DEFAULT 0,       -- Primary Spend Metric
    clicks REAL DEFAULT 0,
    impressions REAL DEFAULT 0,
    page_likes REAL DEFAULT 0,
    landing_page_views REAL DEFAULT 0,
    link_clicks REAL DEFAULT 0,
    adds_to_cart REAL DEFAULT 0,
    checkouts_initiated REAL DEFAULT 0,
    adds_of_payment_info REAL DEFAULT 0,
    purchases REAL DEFAULT 0,              -- Ad Conversions
    purchases_conversion_value_inr REAL DEFAULT 0, -- Ad Conversion Revenue
    website_contacts REAL DEFAULT 0,
    messaging_conversations_started REAL DEFAULT 0,
    adds_to_cart_conversion_value_inr REAL DEFAULT 0,
    checkouts_initiated_conversion_value_inr REAL DEFAULT 0,
    adds_of_payment_info_conversion_value_inr REAL DEFAULT 0,
    row_count REAL DEFAULT 1,
    
    -- Parsed Dimensions (Kept in-table for simplicity)
    brand TEXT,                            
    funnel_stage TEXT,                     
    region TEXT,                           
    adset_channel TEXT,                    
    adset_target TEXT,                     
    ad_source_type TEXT,                   
    ad_format TEXT,                        
    ad_concept TEXT,                       
    ad_category TEXT,                      
    ad_collection TEXT,                    
    
    -- Calculated Metrics
    ctr REAL DEFAULT 0,                    
    cpc REAL DEFAULT 0,                    
    cpm REAL DEFAULT 0,                    
    roas REAL DEFAULT 0,                   
    
    FOREIGN KEY(date_key) REFERENCES date_dimension(date_key),
    CHECK (ctr >= 0),
    CHECK (cpc >= 0),
    CHECK (cpm >= 0),
    CHECK (roas >= 0)
);

-- Table: shopify_sales
-- Purpose: Fact table holding transactional order-level data representing 
-- the actual business revenue.
-- Structure: Order ID is kept as a standard integer rather than a strict 
-- Primary Key to accommodate multiple line-items (products) within a single order.
CREATE TABLE IF NOT EXISTS shopify_sales (
    data_source_name TEXT NOT NULL,        
    date_key TEXT NOT NULL,                -- FK to date_dimension
    currency TEXT,                         
    sales_channel TEXT,                    
    transaction_timestamp TEXT,
    order_created_at TEXT,
    order_updated_at TEXT,
    order_id INTEGER,                      -- Unique transaction ID (not PK due to line items)
    order_name TEXT,                       
    country_funnel TEXT,
    geo_location_segment TEXT,
    billing_country TEXT,
    billing_province TEXT,
    billing_city TEXT,
    order_tags TEXT,
    product_id INTEGER,
    product_title TEXT,
    product_tags TEXT,
    product_type TEXT,
    variant_title TEXT,
    gross_sales_inr REAL DEFAULT 0,
    net_sales_inr REAL DEFAULT 0,          
    total_sales_inr REAL DEFAULT 0,        -- Primary Sales Metric (equal to Net)
    orders REAL DEFAULT 0,                 
    returns_inr REAL DEFAULT 0,
    return_rate REAL DEFAULT 0,            
    items_sold REAL DEFAULT 0,
    items_returned REAL DEFAULT 0,
    average_order_value_inr REAL DEFAULT 0,
    new_customer_orders REAL DEFAULT 0,
    returning_customer_orders REAL DEFAULT 0,
    average_items_per_order REAL DEFAULT 0,
    discounts_inr REAL DEFAULT 0,
    row_count REAL DEFAULT 1,
    sku TEXT,
    customer_sale_type TEXT,
    customer_id INTEGER,
    shipping_country TEXT,
    FOREIGN KEY(date_key) REFERENCES date_dimension(date_key)
);

-- =========================================================================
-- 3. INDEXING STRATEGY
-- =========================================================================
-- Indexes are selectively applied to columns frequently used in WHERE, 
-- GROUP BY, and JOIN clauses by Power BI and the AI tool to accelerate reads.

-- Date indexes: Essential for joining fact tables to the date dimension.
CREATE INDEX IF NOT EXISTS idx_campaign_date ON campaign_performance(date_key);
CREATE INDEX IF NOT EXISTS idx_shopify_date ON shopify_sales(date_key);

-- Analytical indexes: These dimensions are the most frequently filtered 
-- in marketing reports (e.g., "Show me TOF performance in India for Brand A").
CREATE INDEX IF NOT EXISTS idx_campaign_parsed ON campaign_performance(brand, funnel_stage, region);

-- Creative indexes: Frequently used to evaluate ad format and category efficiency.
CREATE INDEX IF NOT EXISTS idx_campaign_ad_details ON campaign_performance(ad_format, ad_category);


-- =========================================================================
-- 4. BASE QUERIES (For Power BI / AI Verification)
-- =========================================================================

-- QUERY 1: Aggregated Platform Performance
-- This query pre-calculates the monthly aggregates.
/*
SELECT 
    cp.data_source_name AS Platform,
    cp.adset_channel AS Channel,
    cp.region AS Region,
    dt.year AS Year,
    dt.month AS MonthNumber,
    dt.month_name AS MonthName,
    SUM(cp.amount_spent_inr) AS Total_Spend,
    SUM(cp.clicks) AS Total_Clicks,
    SUM(cp.impressions) AS Total_Impressions,
    SUM(cp.purchases) AS Total_Conversions,
    SUM(cp.purchases_conversion_value_inr) AS Total_Revenue,
    CASE 
        WHEN SUM(cp.impressions) > 0 THEN (SUM(cp.clicks) / SUM(cp.impressions)) * 100 
        ELSE 0 
    END AS Aggregated_CTR,
    CASE 
        WHEN SUM(cp.clicks) > 0 THEN SUM(cp.amount_spent_inr) / SUM(cp.clicks) 
        ELSE 0 
    END AS Aggregated_CPC,
    CASE 
        WHEN SUM(cp.amount_spent_inr) > 0 THEN SUM(cp.purchases_conversion_value_inr) / SUM(cp.amount_spent_inr) 
        ELSE 0 
    END AS Aggregated_ROAS
FROM campaign_performance cp
JOIN date_dimension dt ON cp.date_key = dt.date_key
GROUP BY 
    cp.data_source_name,
    cp.adset_channel,
    cp.region,
    dt.year,
    dt.month,
    dt.month_name
ORDER BY 
    dt.year DESC, 
    dt.month DESC, 
    Total_Spend DESC;
*/

-- QUERY 2: Dynamic Template for AI Context
-- Base query pattern generated by the AI Chatbot when evaluating campaigns.
/*
SELECT 
    cp.date_key AS Date,
    cp.data_source_name AS Platform,
    cp.campaign_name AS Campaign,
    cp.funnel_stage AS Funnel_Stage,
    cp.region AS Region,
    cp.ad_name AS Ad_Name,
    cp.amount_spent_inr AS Spend,
    cp.clicks AS Clicks,
    cp.impressions,
    cp.purchases,
    cp.purchases_conversion_value_inr AS Purchases_Value,
    cp.ctr,
    cp.cpc,
    cp.cpm,
    cp.roas
FROM campaign_performance cp
WHERE 
    cp.date_key BETWEEN '2026-03-01' AND '2026-03-31'  
    AND cp.data_source_name LIKE '%Brand A%'        
    AND cp.region = 'India'                           
    AND cp.campaign_name LIKE '%TOF%'               
ORDER BY cp.date_key ASC;
*/
