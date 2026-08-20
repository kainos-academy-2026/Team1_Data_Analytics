from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="fact_trip",
    comment="Fact table with trip metrics joined to date and zone dimensions"
)
def fact_trip():
    silver_df = spark.read.table("silver_taxi")
    dim_date_df = spark.read.table("dim_date")
    dim_zone_df = spark.read.table("dim_zone")

    # Compute derived trip metrics
    silver_enriched = (
        silver_df
        .withColumn(
            "trip_duration_minutes",
            (F.unix_timestamp("completed_ts") - F.unix_timestamp("time_picked_up_ts")) / 60
        )
        .withColumn(
            "expected_vs_actual_pickup_minutes_difference",
            (F.unix_timestamp("time_picked_up_ts") - F.unix_timestamp("pickup_due_ts")) / 60
        )
        .withColumn(
            "dispatch_to_arrival_minutes",
            (F.unix_timestamp("time_vehicle_arrived_ts") - F.unix_timestamp("time_dispatched_ts")) / 60
        )
        .withColumn("trip_date", F.to_date("pickup_due_ts"))
    )

    # Join with dim_date
    dim_date_keys = dim_date_df.select("date_key", "full_date")
    fact_with_date = (
        silver_enriched
        .join(dim_date_keys, silver_enriched["trip_date"] == dim_date_keys["full_date"], "left")
        .withColumn("trip_booked_for_date_key", F.col("date_key"))
        .drop("date_key", "full_date")
    )

    # Join with dim_zone for pickup
    pickup_zone_keys = dim_zone_df.select(
        F.col("zone_key").alias("pickup_zone_key"),
        F.col("zone_code").alias("pickup_zone_code")
    )
    fact_with_pickup = (
        fact_with_date
        .join(pickup_zone_keys, fact_with_date["pickup_zone"] == pickup_zone_keys["pickup_zone_code"], "left")
        .drop("pickup_zone_code")
    )

    # Join with dim_zone for destination
    dest_zone_keys = dim_zone_df.select(
        F.col("zone_key").alias("destination_zone_key"),
        F.col("zone_code").alias("dest_zone_code")
    )
    fact_with_zones = (
        fact_with_pickup
        .join(dest_zone_keys, fact_with_pickup["destination_zone"] == dest_zone_keys["dest_zone_code"], "left")
        .drop("dest_zone_code")
    )

    # Select final columns
    return (
        fact_with_zones
        .withColumn("trip_key", F.monotonically_increasing_id())
        .select(
            "trip_key", "booking_id", "trip_booked_for_date_key",
            "pickup_zone_key", "destination_zone_key",
            F.col("trip_status").alias("status"),
            "payment_type", "booking_source",
            F.col("driver").alias("driver_id"),
            F.col("vehicle").alias("vehicle_id"),
            F.col("priority").alias("priority_level"),
            "capabilities",
            F.col("price").alias("fare_amount"),
            F.col("time_dispatched_ts").alias("dispatch_timestamp"),
            F.col("pickup_due_ts").alias("pickup_due_timestamp"),
            "distance",
            "expected_vs_actual_pickup_minutes_difference",
            "dispatch_to_arrival_minutes",
            "trip_duration_minutes"
        )
    )
