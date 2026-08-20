from pyspark import pipelines as dp
from pyspark.sql.functions import current_timestamp, col


@dp.table(
    name="bronze_taxi",
    comment="Raw taxi data ingested from CSV via Auto Loader",
    table_properties={"delta.columnMapping.mode": "name"}
)
def bronze_taxi():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("pathGlobFilter", "taxi_data.csv")
        .load("/Volumes/students_data/diarmuid-gallagher/technologist-volume/")
        .withColumn("_ingest_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )
