





















use gzqp_bigdata_dev;
drop view stock_market_analysis;

-- 创建关联视图
CREATE VIEW stock_market_analysis AS
SELECT
    s.datetime as trade_datetime,
    s.`open` as stock_open,
    s.`close` as stock_close,
    s.price_change_rate as stock_change_rate,
    m.open_price as market_open,
    m.close_price as market_close,
    m.change_percent as market_change_percent,
    s.volume as stock_volume,
    m.volume as market_volume
FROM tmp_sto s
         LEFT JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date)
WHERE m.trade_date IS NOT NULL;



-- 计算个股与大盘涨跌幅的相关系数
SELECT
    CORR(s.price_change_rate, m.change_percent) as correlation_coefficient,
    COUNT(*) as sample_size
FROM tmp_sto s
         JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date);

-- 分析同涨同跌概率
SELECT
    COUNT(*) as total_days,
    SUM(CASE WHEN s.price_change_rate > 0 AND m.change_percent > 0 THEN 1 ELSE 0 END) as both_up_days,
    SUM(CASE WHEN s.price_change_rate < 0 AND m.change_percent < 0 THEN 1 ELSE 0 END) as both_down_days,
    SUM(CASE WHEN s.price_change_rate > 0 AND m.change_percent < 0 THEN 1 ELSE 0 END) as stock_up_market_down,
    SUM(CASE WHEN s.price_change_rate < 0 AND m.change_percent > 0 THEN 1 ELSE 0 END) as stock_down_market_up,

    ROUND(SUM(CASE WHEN s.price_change_rate > 0 AND m.change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as both_up_rate,
    ROUND(SUM(CASE WHEN s.price_change_rate < 0 AND m.change_percent < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as both_down_rate
FROM tmp_sto s
         JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date);


-- 分析个股是否领先于大盘
SELECT
    -- 个股领先大盘上涨的情况
    SUM(CASE WHEN s.price_change_rate > 1 AND LEAD(m.change_percent) OVER (ORDER BY s.datetime) > 0.5 THEN 1 ELSE 0 END) as stock_lead_up,

    -- 大盘领先个股上涨的情况
    SUM(CASE WHEN m.change_percent > 1 AND LEAD(s.price_change_rate) OVER (ORDER BY s.datetime) > 0.5 THEN 1 ELSE 0 END) as market_lead_up
FROM tmp_sto s
         JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date);


-- 比较波动幅度
SELECT
    STDDEV(s.price_change_rate) as stock_volatility,
    STDDEV(m.change_percent) as market_volatility,
    STDDEV(s.price_change_rate) / STDDEV(m.change_percent) as volatility_ratio
FROM tmp_sto s
         JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date);


-- 计算Beta系数
SELECT
    COVAR(s.price_change_rate, m.change_percent) / VARIANCE(m.change_percent) as beta_coefficient
FROM tmp_sto s
         JOIN tmp_sz_cleaned m ON
    s.`year` = YEAR(m.trade_date) AND
    s.`month` = MONTH(m.trade_date) AND
    s.`day` = DAY(m.trade_date);

# 分析结论解读：
# 相关系数接近1：个股与大盘高度相关
# Beta系数>1：个股波动大于大盘（进攻型）
# Beta系数<1：个股波动小于大盘（防御型）
# 同涨同跌概率高：个股受系统性风险影响大
# 领先滞后关系：可判断个股是否具有先行指标作用


