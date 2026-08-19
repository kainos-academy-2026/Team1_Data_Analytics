# use OSS pyspark package for declarative pipelines
from pyspark import pipelines as dp

@dp.table(
  name="ingest_taxis",
  comment="Streaming table ingesting data from students_data.team1_taxi.bronze_taxi",
  table_properties={"delta.columnMapping.mode": "name"}
)
def ingest_taxis():
  return (
    spark.readStream
      .table("students_data.team1_taxi.bronze_taxi")
  )