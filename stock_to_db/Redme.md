

股票入库
涉及指标
kdj、macd、bbi、
ma(5，7)、
知行趋势线

Index(['open', 'close', 'high', 'low', 'vol', 'amount', 'year', 'month', 'day',
       'hour', 'minute', 'datetime', 'volume', 'K', 'D', 'J'],
      dtype='object')



CREATE TABLE gzqp_bigdata_dev.`stock_features3` (
                                   `code` varchar(10) NOT NULL,
                                   `trade_date` date NOT NULL,
                                   `open` double NULL,
                                   `close` double NULL,
                                   `high` double NULL,
                                   `low` double NULL,
                                   `vol` bigint NULL,
                                   `amount` bigint NULL,
                                   `zx_short_term_trend` double NULL,
                                   `zx_bull_bear_line` double NULL,
                                   `K` double NULL,
                                   `D` double NULL,
                                   `J` double NULL,
                                   `BBI` double NULL,
                                   `MA5` double NULL,
                                   `MA7` double NULL,
                                   `MA10` double NULL,
                                   `MA20` double NULL,
                                   `MA30` double NULL,
                                   `MA40` double NULL,
                                   `MA45` double NULL,
                                   `MA60` double NULL,
                                   `MA90` double NULL,
                                   `MA250` double NULL,
                                   `DIF` double NULL,
                                   `DEA` double NULL,
                                   `MACD` double NULL,
                                   `zxt` double NULL,
                                   `dzs` double NULL,
                                   `dzt` double NULL
) ENGINE=OLAP
    UNIQUE KEY(`code`, `trade_date`)
DISTRIBUTED BY HASH(`code`, `trade_date`) BUCKETS 10
PROPERTIES (
"replication_allocation" = "tag.location.default: 3",
"min_load_replica_num" = "-1",
"is_being_synced" = "false",
"storage_medium" = "hdd",
"storage_format" = "V2",
"inverted_index_storage_format" = "V1",
"enable_unique_key_merge_on_write" = "true",
"light_schema_change" = "true",
"disable_auto_compaction" = "false",
"enable_single_replica_compaction" = "false",
"group_commit_interval_ms" = "10000",
"group_commit_data_bytes" = "134217728",
"enable_mow_light_delete" = "false"
);