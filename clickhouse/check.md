-- ============================================================
-- SCRIPT KIỂM TRA LỖI MATERIALIZED VIEW TRONG CLICKHOUSE
-- ============================================================

-- 1. Kiểm tra lỗi MV trong system.part_log (insert errors)
SELECT
    event_time,
    database,
    table,
    part_name,
    exception,
    error
FROM system.part_log
WHERE event_type = 'NewPart'
  AND error != 0
  AND event_time >= now() - INTERVAL 24 HOUR
ORDER BY event_time DESC
LIMIT 50;

-- ============================================================

-- 2. Kiểm tra lỗi trong system.query_log liên quan đến MV
SELECT
    event_time,
    user,
    query_kind,
    databases,
    tables,
    exception_code,
    exception,
    query
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND hasAny(tables, (
      SELECT groupArray(concat(database, '.', name))
      FROM system.tables
      WHERE engine = 'MaterializedView'
  ))
  AND event_time >= now() - INTERVAL 24 HOUR
ORDER BY event_time DESC
LIMIT 50;

-- ============================================================

-- 3. Kiểm tra MV nào đang bị broken/detached
SELECT
    database,
    name                        AS materialized_view,
    engine,
    is_temporary,
    create_table_query,
    dependencies_table          AS source_table,
    data_paths
FROM system.tables
WHERE engine = 'MaterializedView'
  AND (
      -- MV không có target table hợp lệ
      as_select IS NOT NULL
      AND dependencies_table NOT IN (
          SELECT concat(database, '.', name)
          FROM system.tables
      )
  )
ORDER BY database, name;

-- ============================================================

-- 4. Kiểm tra lỗi MV qua system.text_log (mức WARNING/ERROR)
SELECT
    event_time,
    level,
    logger_name,
    message
FROM system.text_log
WHERE level IN ('Warning', 'Error', 'Fatal')
  AND (
      lower(message) LIKE '%materialized%'
      OR lower(message) LIKE '%mv%trigger%'
      OR lower(message) LIKE '%push to view%'
      OR lower(message) LIKE '%executing push%'
  )
  AND event_time >= now() - INTERVAL 24 HOUR
ORDER BY event_time DESC
LIMIT 100;

-- ============================================================

-- 5. Tổng hợp: Danh sách tất cả MV và trạng thái target table
SELECT
    t.database,
    t.name                              AS mv_name,
    t.dependencies_table                AS source_table,
    t.as_select                         AS target_table_ref,
    if(
        t2.name IS NOT NULL, 'OK', 'MISSING TARGET TABLE'
    )                                   AS target_status,
    t.create_table_query
FROM system.tables t
LEFT JOIN system.tables t2
    ON t2.database = splitByChar('.', t.as_select)[1]
    AND t2.name    = splitByChar('.', t.as_select)[2]
WHERE t.engine = 'MaterializedView'
ORDER BY target_status DESC, t.database, t.name;

-- ============================================================

-- 6. Kiểm tra MV trigger lỗi gần đây nhất qua query_log (chi tiết)
SELECT
    event_time,
    query_duration_ms,
    read_rows,
    written_rows,
    exception_code,
    exception,
    databases,
    tables,
    query
FROM system.query_log
WHERE type IN ('ExceptionBeforeStart', 'ExceptionWhileProcessing')
  AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
ORDER BY event_time DESC
LIMIT 30;