-- ==========================================
-- Growify Performance Marketing Star Schema
-- ==========================================
-- This database serves as the Single Source of Truth (SSOT) 
-- for both the Power BI dashboard and the AI Insight Chatbot.
-- It follows a relational star schema structure.

PRAGMA foreign_keys = ON;

-- 1. Date Dimension Table (dim_date)
-- Serves as the primary time-series axis, resolving inconsistencies between ad and sales timelines.
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

-- 2. Campaign Performance Fact/Dimension Table (fact_campaign_performance)
-- Holds ad delivery and conversion value metrics at the daily-ad level.
-- Includes parsed naming convention sub-fields for granular slicing.
CREATE TABLE IF NOT EXISTS campaign_performance (
    date_key TEXT NOT NULL,                -- FK to date_dimension(date_key)
    data_source_name TEXT NOT NULL,        -- Normalized brand name (e.g. Brand A)
    campaign_name TEXT NOT NULL,           -- Raw campaign string
    campaign_effective_status TEXT,        -- PAUSED / ACTIVE
    adset_name TEXT,                       -- Raw adset string
    ad_name TEXT,                          -- Raw ad string
    country_funnel TEXT,                   -- Target country
    geo_location_segment TEXT,             -- Target geo region
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
    brand TEXT,                            -- Parsed Brand (Growify)
    funnel_stage TEXT,                     -- Parsed Stage (TOF/MOF/BOF/Retarget)
    region TEXT,                           -- Parsed Region (India/US/UK/UAE/etc)
    adset_channel TEXT,                    -- Parsed Channel (Ecomm/Walkins/etc)
    adset_target TEXT,                     -- Parsed Target (LAL/Open/Engaged/etc)
    ad_source_type TEXT,                   -- Parsed Creative Source (CA/EP/etc)
    ad_format TEXT,                        -- Parsed Creative Format (Video/SI/etc)
    ad_concept TEXT,                       -- Parsed Creative Concept/Influencer
    ad_category TEXT,                      -- Parsed Creative Category (Kurta/Festive/etc)
    ad_collection TEXT,                    -- Parsed Creative Collection (Womens/Mens/etc)
    ctr REAL DEFAULT 0,                    -- Calculated CTR (Clicks / Impressions) * 100
    cpc REAL DEFAULT 0,                    -- Calculated CPC (Spend / Clicks)
    cpm REAL DEFAULT 0,                    -- Calculated CPM (Spend / Impressions * 1000)
    roas REAL DEFAULT 0,                   -- Calculated Ad ROAS (Conv Value / Spend)
    FOREIGN KEY(date_key) REFERENCES date_dimension(date_key),
    CHECK (ctr >= 0),
    CHECK (cpc >= 0),
    CHECK (cpm >= 0),
    CHECK (roas >= 0)
);

-- 3. Shopify Sales Fact Table (fact_shopify_sales)
-- Holds transactional order-level data representing total actual business revenue.
CREATE TABLE IF NOT EXISTS shopify_sales (
    data_source_name TEXT NOT NULL,        -- Normalized brand name (e.g. Brand A)
    date_key TEXT NOT NULL,                -- FK to date_dimension(date_key)
    currency TEXT,                         -- Normalized Currency (INR)
    sales_channel TEXT,                    -- Channel (Online Store, etc)
    transaction_timestamp TEXT,
    order_created_at TEXT,
    order_updated_at TEXT,
    order_id INTEGER,                      -- Unique transaction ID (not PK due to line items)
    order_name TEXT,                       -- e.g. #1001
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
    net_sales_inr REAL DEFAULT 0,          -- Gross - Discounts - Returns
    total_sales_inr REAL DEFAULT 0,        -- Primary Sales Metric (equal to Net)
    orders REAL DEFAULT 0,                 -- Order flag (0 or 1)
    returns_inr REAL DEFAULT 0,
    return_rate REAL DEFAULT 0,            -- Returns / Gross
    items_sold REAL DEFAULT 0,
    items_returned REAL DEFAULT 0,
    average_order_value_inr REAL DEFAULT 0,-- Total Sales / Orders
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

-- ==========================================
-- INDEXING OPTIMIZATIONS
-- ==========================================
-- Indexes are added to speed up queries filtered or joined by Date, Funnel Stage, Region, and Brand.

-- Index for date joins/filtering in facts
CREATE INDEX IF NOT EXISTS idx_campaign_date ON campaign_performance(date_key);
CREATE INDEX IF NOT EXISTS idx_shopify_date ON shopify_sales(date_key);

-- Index for parsed campaign dimension filters
CREATE INDEX IF NOT EXISTS idx_campaign_parsed ON campaign_performance(brand, funnel_stage, region);
CREATE INDEX IF NOT EXISTS idx_campaign_ad_details ON campaign_performance(ad_format, ad_category);
