




use gzqp_bigdata_dev;




select *
from gzqp_bigdata_dev.tmp_sz;

-- 创建清洗后的表，移除字段名中的空格并修正数据类型
CREATE TABLE tmp_sz_cleaned
(
    trade_date     DATE NULL COMMENT '交易日期',
    open_price     DECIMAL(10,3) NULL COMMENT '开盘价',
    close_price    DECIMAL(10,3) NULL COMMENT '收盘价',
    change_amount  DECIMAL(10,3) NULL COMMENT '涨跌额',
    change_percent DECIMAL(8,3) NULL COMMENT '涨跌幅(%)',
    low_price      DECIMAL(10,3) NULL COMMENT '最低价',
    high_price     DECIMAL(10,3) NULL COMMENT '最高价',
    volume         BIGINT NULL COMMENT '成交量(手)',
    turnover_10k   DECIMAL(15,2) NULL COMMENT '成交金额(万元)',
    turnover_rate  DECIMAL(8,3) NULL COMMENT '换手率(%)'
);

-- 插入并清洗数据
INSERT INTO tmp_sz_cleaned
(trade_date, open_price, close_price, change_amount, change_percent, low_price, high_price, volume, turnover_10k, turnover_rate)
SELECT
    STR_TO_DATE(date, '%Y-%m-%d') as trade_date,
    CAST(`open` AS DECIMAL(10,3)) as open_price,
    CAST(`close` AS DECIMAL(10,3)) as close_price,
    CAST(`change` AS DECIMAL(10,3)) as change_amount,
    CASE
        WHEN `change_percent` = '-' OR `change_percent` IS NULL THEN NULL
        ELSE CAST(REPLACE(`change_percent`, '%', '') AS DECIMAL(8,3))
        END as change_percent,
    CAST(`low` AS DECIMAL(10,3)) as low_price,
    CAST(`high` AS DECIMAL(10,3)) as high_price,
    CAST(`volume` AS BIGINT) as volume,
    CAST(`turnover_10k` AS DECIMAL(15,2)) as turnover_10k,
    CASE
        WHEN `turnover_rate` = '-' OR `turnover_rate` IS NULL THEN NULL
        ELSE CAST(REPLACE(`turnover_rate`, '%', '') AS DECIMAL(8,3))
        END as turnover_rate
FROM tmp_sz;



select *
from tmp_sz_cleaned;



-- 1. 月份统计（含涨跌幅排名和上涨概率排名）
SELECT
    month,
    avg_monthly_change_percent,
    RANK() OVER (ORDER BY avg_monthly_change_percent DESC) AS change_rank,
    up_percentage,
    RANK() OVER (ORDER BY up_percentage DESC) AS up_probability_rank,
    up_count,
    total_count
FROM (
         SELECT
             DATE_FORMAT(trade_date, '%Y-%m') AS month,
             AVG(change_percent) AS avg_monthly_change_percent,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY DATE_FORMAT(trade_date, '%Y-%m')
     ) t
ORDER BY change_rank;

-- 2. 号数统计（含双排名）
SELECT
    day_of_month,
    avg_daily_change_percent,
    RANK() OVER (ORDER BY avg_daily_change_percent DESC) AS change_rank,
    up_percentage,
    RANK() OVER (ORDER BY up_percentage DESC) AS up_probability_rank,
    up_count,
    total_count
FROM (
         SELECT
             DAYOFMONTH(trade_date) AS day_of_month,
             AVG(change_percent) AS avg_daily_change_percent,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY DAYOFMONTH(trade_date)
     ) t
ORDER BY change_rank;

-- 3. 综合统计（月份+号数，含排名）
SELECT
    month,
    day_of_month,
    avg_change_percent,
    RANK() OVER (PARTITION BY month ORDER BY avg_change_percent DESC) AS month_day_change_rank,
    up_percentage,
    RANK() OVER (PARTITION BY month ORDER BY up_percentage DESC) AS month_day_up_rank,
    up_count,
    total_count
FROM (
         SELECT
             DATE_FORMAT(trade_date, '%Y-%m') AS month,
             DAYOFMONTH(trade_date) AS day_of_month,
             AVG(change_percent) AS avg_change_percent,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY DATE_FORMAT(trade_date, '%Y-%m'), DAYOFMONTH(trade_date)
     ) t
ORDER BY month, month_day_change_rank;

-- 4. 历史月份趋势分析（含排名）
SELECT
    month,
    avg_change,
    RANK() OVER (ORDER BY avg_change DESC) AS avg_change_rank,
    std_dev,
    min_change,
    max_change,
    up_percentage,
    RANK() OVER (ORDER BY up_percentage DESC) AS up_probability_rank,
    up_count,
    total_count
FROM (
         SELECT
             DATE_FORMAT(trade_date, '%Y-%m') AS month,
             AVG(change_percent) AS avg_change,
             STDDEV(change_percent) AS std_dev,
             MIN(change_percent) AS min_change,
             MAX(change_percent) AS max_change,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY DATE_FORMAT(trade_date, '%Y-%m')
     ) t
ORDER BY avg_change_rank;





-- 1. 按月初(1-10日)、月中(11-20日)、月末(21-31日)分组统计
SELECT
    CASE
        WHEN day_of_month BETWEEN 1 AND 10 THEN '月初(1-10日)'
        WHEN day_of_month BETWEEN 11 AND 20 THEN '月中(11-20日)'
        ELSE '月末(21-31日)'
        END AS month_period,
    AVG(avg_daily_change_percent) AS avg_change_percent,
    AVG(up_percentage) AS avg_up_percentage,
    SUM(up_count) AS total_up_days,
    SUM(total_count) AS total_days,
    ROUND(SUM(up_count) * 100.0 / SUM(total_count), 2) AS overall_up_percentage,
    RANK() OVER (ORDER BY AVG(avg_daily_change_percent) DESC) AS change_rank,
    RANK() OVER (ORDER BY AVG(up_percentage) DESC) AS up_probability_rank
FROM (
         SELECT
             DAYOFMONTH(trade_date) AS day_of_month,
             AVG(change_percent) AS avg_daily_change_percent,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY DAYOFMONTH(trade_date)
     ) t
GROUP BY
    CASE
        WHEN day_of_month BETWEEN 1 AND 10 THEN '月初(1-10日)'
        WHEN day_of_month BETWEEN 11 AND 20 THEN '月中(11-20日)'
        ELSE '月末(21-31日)'
        END
ORDER BY change_rank;

-- 2. 按月分段+月份双重维度分析
SELECT
    month,
    CASE
        WHEN day_of_month BETWEEN 1 AND 10 THEN '月初'
        WHEN day_of_month BETWEEN 11 AND 20 THEN '月中'
        ELSE '月末'
        END AS month_period,
    AVG(change_percent) AS avg_change_percent,
    ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
    COUNT(*) AS record_count,
    RANK() OVER (PARTITION BY month ORDER BY AVG(change_percent) DESC) AS period_rank_in_month,
    RANK() OVER (ORDER BY AVG(change_percent) DESC) AS overall_rank
FROM (
         SELECT
             DATE_FORMAT(trade_date, '%Y-%m') AS month,
             DAYOFMONTH(trade_date) AS day_of_month,
             change_percent
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
     ) t
GROUP BY month,
         CASE
             WHEN day_of_month BETWEEN 1 AND 10 THEN '月初'
             WHEN day_of_month BETWEEN 11 AND 20 THEN '月中'
             ELSE '月末'
             END
ORDER BY month, period_rank_in_month;

-- 3. 按月分段+年份维度分析
SELECT
    year,
    month_period,
    AVG(avg_change_percent) AS avg_change_percent,
    AVG(up_percentage) AS avg_up_percentage,
    SUM(up_count) AS total_up_days,
    SUM(total_count) AS total_days
FROM (
         SELECT
             YEAR(trade_date) AS year,
             CASE
                 WHEN DAYOFMONTH(trade_date) BETWEEN 1 AND 10 THEN '月初'
                 WHEN DAYOFMONTH(trade_date) BETWEEN 11 AND 20 THEN '月中'
                 ELSE '月末'
                 END AS month_period,
             AVG(change_percent) AS avg_change_percent,
             ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
             SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) AS up_count,
             COUNT(*) AS total_count
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
         GROUP BY YEAR(trade_date),
                  CASE
                      WHEN DAYOFMONTH(trade_date) BETWEEN 1 AND 10 THEN '月初'
                      WHEN DAYOFMONTH(trade_date) BETWEEN 11 AND 20 THEN '月中'
                      ELSE '月末'
                      END
     ) t
GROUP BY year, month_period
ORDER BY year, month_period;

-- 4. 按月分段+星期维度分析（分析周几在月各时段表现）
SELECT
    month_period,
    day_of_week,
    AVG(change_percent) AS avg_change_percent,
    ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS up_percentage,
    COUNT(*) AS record_count
FROM (
         SELECT
             CASE
                 WHEN DAYOFMONTH(trade_date) BETWEEN 1 AND 10 THEN '月初'
                 WHEN DAYOFMONTH(trade_date) BETWEEN 11 AND 20 THEN '月中'
                 ELSE '月末'
                 END AS month_period,
             DAYOFWEEK(trade_date) AS day_of_week,
             change_percent
         FROM tmp_sz_cleaned
         WHERE change_percent IS NOT NULL
     ) t
GROUP BY month_period, day_of_week
ORDER BY month_period, day_of_week;







