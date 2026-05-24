-- ========================================================
-- QUERY 1: Power BI Feed Query
-- Aggregated performance by platform, channel, region, and month
-- ========================================================
SELECT 
    cp."Data Source name" AS Platform,
    cp."Adset Channel" AS Channel,
    cp.Region AS Region,
    dt.year AS Year,
    dt.month AS MonthNumber,
    dt.month_name AS MonthName,
    SUM(cp."Amount Spent (INR)") AS Total_Spend,
    SUM(cp."Clicks (all)") AS Total_Clicks,
    SUM(cp.Impressions) AS Total_Impressions,
    SUM(cp.Purchases) AS Total_Conversions,
    SUM(cp."Purchases Conversion Value (INR)") AS Total_Revenue,
    -- Recalculated aggregated metrics
    CASE 
        WHEN SUM(cp.Impressions) > 0 THEN SUM(cp."Clicks (all)") / SUM(cp.Impressions) 
        ELSE 0 
    END AS Aggregated_CTR,
    CASE 
        WHEN SUM(cp."Clicks (all)") > 0 THEN SUM(cp."Amount Spent (INR)") / SUM(cp."Clicks (all)") 
        ELSE 0 
    END AS Aggregated_CPC,
    CASE 
        WHEN SUM(cp."Amount Spent (INR)") > 0 THEN SUM(cp."Purchases Conversion Value (INR)") / SUM(cp."Amount Spent (INR)") 
        ELSE 0 
    END AS Aggregated_ROAS
FROM campaign_performance cp
JOIN date_dimension dt ON cp.Date = dt.date_key
GROUP BY 
    cp."Data Source name",
    cp."Adset Channel",
    cp.Region,
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
    cp.Date,
    cp."Data Source name" AS Platform,
    cp."Campaign Name" AS Campaign,
    cp."Funnel Stage" AS Funnel_Stage,
    cp.Region AS Region,
    cp."Ad Name" AS Ad_Name,
    cp."Amount Spent (INR)" AS Spend,
    cp."Clicks (all)" AS Clicks,
    cp.Impressions,
    cp.Purchases,
    cp."Purchases Conversion Value (INR)" AS Purchases_Value,
    cp.CTR,
    cp.CPC,
    cp.CPM,
    cp.ROI
FROM campaign_performance cp
WHERE 
    cp.Date BETWEEN '2026-03-01' AND '2026-03-31'  -- Dynamic Date Range
    AND cp."Data Source name" LIKE '%Brand A%'        -- Dynamic Platform filter
    AND cp.Region = 'India'                           -- Dynamic Region filter
    AND cp."Campaign Name" LIKE '%TOF%'               -- Dynamic Campaign filter
ORDER BY cp.Date ASC;
