from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dp.materialized_view(
    name="silver_taxi",
    comment="Cleaned and deduplicated taxi data with proper types and standardised values"
)
def silver_taxi():
    bronze_df = spark.read.table("bronze_taxi")

    # Step 1: Select, rename, and cast columns
    silver_clean = bronze_df.select(
        F.col("`Booking ID`").cast("string").alias("booking_id"),
        F.trim(F.col("`Source`")).alias("trip_status"),
        F.to_timestamp(F.col("`Pickup Due`"), "dd/MM/yyyy HH:mm").alias("pickup_due_ts"),
        F.to_timestamp(F.col("`Time Dispatched`"), "dd/MM/yyyy HH:mm").alias("time_dispatched_ts"),
        F.to_timestamp(F.col("`Time Vehicle Arrived`"), "dd/MM/yyyy HH:mm").alias("time_vehicle_arrived_ts"),
        F.to_timestamp(F.col("`Time Picked Up`"), "dd/MM/yyyy HH:mm").alias("time_picked_up_ts"),
        F.to_timestamp(F.col("`Completed`"), "dd/MM/yyyy HH:mm").alias("completed_ts"),
        F.trim(F.col("`Driver`")).alias("driver"),
        F.trim(F.col("`Vehicle`")).alias("vehicle"),
        F.trim(F.col("`Payment Type`")).alias("payment_type"),
        F.col("`Priority`").cast("int").alias("priority"),
        F.trim(F.col("`Capabilities`")).alias("capabilities"),
        F.trim(F.col("`Booking source`")).alias("booking_source"),
        F.regexp_replace(F.col("`Price`"), ",", "").cast("double").alias("price"),
        F.regexp_replace(F.col("`Distance`"), ",", "").cast("double").alias("distance"),
        F.trim(F.col("`Pickup Zone`")).alias("pickup_zone"),
        F.trim(F.col("`Destination Zone`")).alias("destination_zone"),
        F.col("`Pickup Latitude`").cast("double").alias("pickup_latitude"),
        F.col("`Pickup Longitude`").cast("double").alias("pickup_longitude"),
        F.col("`Destination Latitude`").cast("double").alias("destination_latitude"),
        F.col("`Destination Longitude`").cast("double").alias("destination_longitude"),
        F.trim(F.col("`Booked by`")).alias("booked_by")
    )

    # Step 2: Replace empty strings with NULL
    string_cols = [
        "booking_id", "trip_status", "payment_type",
        "booking_source", "pickup_zone", "destination_zone"
    ]
    for c in string_cols:
        silver_clean = silver_clean.withColumn(
            c,
            F.when(F.trim(F.col(c)) == "", F.lit(None)).otherwise(F.col(c))
        )

    # Step 3: Change trips with a capability of 'Z' to have a payment type of 'card'
    silver_clean = silver_clean.withColumn(
        "payment_type",
        F.when(F.col("capabilities") == "Z", F.lit("card")).otherwise(F.col("payment_type"))
    )

    # Step 4: Remove rows where pickup date is in the future (data quality issue)
    silver_clean = silver_clean.filter(
        F.col("pickup_due_ts").isNull() | (F.col("pickup_due_ts") <= F.current_timestamp())
    )
    future_removed = bronze_df.count() - silver_clean.count()
    print(f"Rows removed with future pickup dates: {future_removed}")


    # Step 5: Deduplicate by booking_id, keeping the latest record
    w = Window.partitionBy("booking_id").orderBy(
        F.col("completed_ts").desc_nulls_last(),
        F.col("time_picked_up_ts").desc_nulls_last(),
        F.col("time_dispatched_ts").desc_nulls_last()
    )
    silver_dedup = (
        silver_clean
        .withColumn("rn", F.row_number().over(w))
        .filter(F.col("rn") == 1)
        .drop("rn")
    )

    # Step 6: Standardise text values with initcap
    silver_conformed = (
        silver_dedup
        .withColumn("payment_type", F.initcap(F.trim(F.col("payment_type"))))
        .withColumn("booking_source", F.initcap(F.trim(F.col("booking_source"))))
        .withColumn("pickup_zone", F.initcap(F.trim(F.col("pickup_zone"))))
        .withColumn("destination_zone", F.initcap(F.trim(F.col("destination_zone"))))
        .withColumn("trip_status", F.initcap(F.trim(F.col("trip_status"))))
    )

    return silver_conformed
