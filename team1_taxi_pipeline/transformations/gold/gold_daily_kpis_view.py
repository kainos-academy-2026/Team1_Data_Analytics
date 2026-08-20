from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="gold_daily_kpis_view",
    comment="Daily KPI aggregations: revenue, trip duration, trip count, and distance"
)
def gold_daily_kpis():
    fact_df = spark.read.table("fact_trip")
    dim_date_df = spark.read.table("dim_date")

    return (
        fact_df
        .join(dim_date_df, F.col("trip_booked_for_date_key") == F.col("date_key"), "inner")
        .groupBy("full_date", "day_name")
        .agg(
            F.sum("fare_amount").alias("total_revenue"),
            F.round(F.avg("trip_duration_minutes"), 2).alias("avg_trip_duration_min"),
            F.count("trip_key").alias("total_trips"),
            F.round(F.avg("distance"), 2).alias("avg_distance_km")
        )
        .orderBy("full_date")
    )
