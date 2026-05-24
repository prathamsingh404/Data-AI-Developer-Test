-- ==========================================
-- Growify Performance Marketing Star Schema
-- ==========================================
-- This database serves as the Single Source of Truth (SSOT) 
-- for both the Power BI dashboard and the AI Insight Chatbot.
-- It follows a relational star schema structure.

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
    Date TEXT,                             -- FK to date_dimension(date_key)
    "Data Source name" TEXT,               -- Normalized brand name (e.g. Brand A)
    "Campaign Name" TEXT,                  -- Raw campaign string
    "Campaign Effective Status" TEXT,      -- PAUSED / ACTIVE
    "Ad Set Name" TEXT,                    -- Raw adset string
    "Ad Name" TEXT,                        -- Raw ad string
    "Country Funnel" TEXT,                 -- Target country
    "Geo Location Segment" TEXT,           -- Target geo region
    "FB Spent Funnel (INR)" REAL,
    "Amount Spent (INR)" REAL,             -- Primary Spend Metric
    "Clicks (all)" REAL,
    "Impressions" REAL,
    "Page Likes" REAL,
    "Landing Page Views" REAL,
    "Link Clicks" REAL,
    "Adds to Cart" REAL,
    "Checkouts Initiated" REAL,
    "Adds of Payment Info" REAL,
    "Purchases" REAL,                      -- Ad Conversions
    "Purchases Conversion Value (INR)" REAL,-- Ad Conversion Revenue
    "Website Contacts" REAL,
    "Messaging Conversations Started" REAL,
    "Adds to Cart Conversion Value (INR)" REAL,
    "Checkouts Initiated Conversion Value (INR)" REAL,
    "Adds of Payment Info Conversion Value (INR)" REAL,
    "Row Count" REAL,
    Brand TEXT,                            -- Parsed Brand (Growify)
    "Funnel Stage" TEXT,                   -- Parsed Stage (TOF/MOF/BOF/Retarget)
    Region TEXT,                           -- Parsed Region (India/US/UK/UAE/etc)
    "Adset Channel" TEXT,                  -- Parsed Channel (Ecomm/Walkins/etc)
    "Adset Target" TEXT,                   -- Parsed Target (LAL/Open/Engaged/etc)
    "Ad Source Type" TEXT,                 -- Parsed Creative Source (CA/EP/etc)
    "Ad Format" TEXT,                      -- Parsed Creative Format (Video/SI/etc)
    "Ad Concept" TEXT,                     -- Parsed Creative Concept/Influencer
    "Ad Category" TEXT,                    -- Parsed Creative Category (Kurta/Festive/etc)
    "Ad Collection" TEXT,                  -- Parsed Creative Collection (Womens/Mens/etc)
    CTR REAL,                              -- Calculated CTR (Clicks / Impressions)
    CPC REAL,                              -- Calculated CPC (Spend / Clicks)
    CPM REAL,                              -- Calculated CPM (Spend / Impressions * 1000)
    ROI REAL,                              -- Calculated Ad ROI (Conv Value / Spend)
    FOREIGN KEY(Date) REFERENCES date_dimension(date_key)
);

-- 3. Shopify Sales Fact Table (fact_shopify_sales)
-- Holds transactional order-level data representing total actual business revenue.
CREATE TABLE IF NOT EXISTS shopify_sales (
    "Data Source name" TEXT,               -- Normalized brand name (e.g. Brand A)
    Date TEXT,                             -- FK to date_dimension(date_key)
    Currency TEXT,                         -- Normalized Currency (INR)
    "Sales Channel" TEXT,                  -- Channel (Online Store, etc)
    "Transaction Timestamp" TEXT,
    "Order Created At" TEXT,
    "Order Updated At" TEXT,
    "Order ID" INTEGER PRIMARY KEY,        -- Unique transaction ID
    "Order Name" TEXT,                     -- e.g. #1001
    "Country Funnel" TEXT,
    "Geo Location Segment" TEXT,
    "Billing Country" TEXT,
    "Billing Province" TEXT,
    "Billing City" TEXT,
    "Order Tags" TEXT,
    "Product ID" INTEGER,
    "Product Title" TEXT,
    "Product Tags" TEXT,
    "Product Type" TEXT,
    "Variant Title" TEXT,
    "Gross Sales (INR)" REAL,
    "Net Sales (INR)" REAL,                -- Gross - Discounts - Returns
    "Total Sales (INR)" REAL,              -- Primary Sales Metric (equal to Net)
    Orders REAL,                           -- Order flag (0 or 1)
    "Returns (INR)" REAL,
    "Return Rate" REAL,                    -- Returns / Gross
    "Items Sold" REAL,
    "Items Returned" REAL,
    "Average Order Value (INR)" REAL,      -- Total Sales / Orders
    "New Customer Orders" REAL,
    "Returning Customer Orders" REAL,
    "Average Items Per Order" REAL,
    "Discounts (INR)" REAL,
    "Row Count" REAL,
    SKU TEXT,
    "Customer Sale Type" TEXT,
    "Customer ID" INTEGER,
    "Shipping Country" TEXT,
    FOREIGN KEY(Date) REFERENCES date_dimension(date_key)
);

-- ==========================================
-- INDEXING OPTIMIZATIONS
-- ==========================================
-- Indexes are added to speed up queries filtered or joined by Date, Funnel Stage, Region, and Brand.

-- Index for date joins/filtering in facts
CREATE INDEX IF NOT EXISTS idx_campaign_date ON campaign_performance(Date);
CREATE INDEX IF NOT EXISTS idx_shopify_date ON shopify_sales(Date);

-- Index for parsed campaign dimension filters
CREATE INDEX IF NOT EXISTS idx_campaign_parsed ON campaign_performance(Brand, "Funnel Stage", Region);
CREATE INDEX IF NOT EXISTS idx_campaign_ad_details ON campaign_performance("Ad Format", "Ad Category");
