from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dp.materialized_view(
    name="dim_zone",
    comment="Zone dimension table derived from pickup and destination zones"
)
def dim_zone():
    silver_df = spark.read.table("silver_taxi")

    pickup_zones = silver_df.select(
        F.col("pickup_zone").alias("zone_code"),
        F.col("pickup_latitude").alias("latitude"),
        F.col("pickup_longitude").alias("longitude")
    )

    dest_zones = silver_df.select(
        F.col("destination_zone").alias("zone_code"),
        F.col("destination_latitude").alias("latitude"),
        F.col("destination_longitude").alias("longitude")
    )

    all_zones = (
        pickup_zones.union(dest_zones)
        .filter(F.col("zone_code").isNotNull())
        .distinct()
    )

    # Deduplicate by zone_code, taking first lat/lon
    w = Window.partitionBy("zone_code").orderBy("latitude")

    return (
        all_zones
        .withColumn("rn", F.row_number().over(w))
        .filter(F.col("rn") == 1)
        .drop("rn")
        .withColumn("zone_key", F.monotonically_increasing_id().cast("int"))
    )
