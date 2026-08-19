CREATE MATERIALIZED VIEW taxi_stats AS
SELECT
  COUNT(*) AS num_trips
FROM ingest_taxis