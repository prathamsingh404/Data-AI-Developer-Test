-- ========================================================
-- QUERY 1: Power BI Feed Query
-- Aggregated performance by platform, channel, region, and month
-- ========================================================
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
    -- Recalculated aggregated metrics
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

-- ========================================================
-- QUERY 2: AI Tool / Chatbot Flexible Context Feed Query
-- Flexible enough to filter by date range, platform, region, or campaign name.
-- This template serves as the base for the chatbot's dynamic SQL generator.
-- ========================================================
-- Example with placeholder filters (the AI tool will dynamically construct/fill these):
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
    cp.date_key BETWEEN '2026-03-01' AND '2026-03-31'  -- Dynamic Date Range
    AND cp.data_source_name LIKE '%Brand A%'        -- Dynamic Platform filter
    AND cp.region = 'India'                           -- Dynamic Region filter
    AND cp.campaign_name LIKE '%TOF%'               -- Dynamic Campaign filter
ORDER BY cp.date_key ASC;
