from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="dim_date",
    comment="Date dimension table derived from silver taxi trip dates, enriched with weather"
)
def dim_date():
    silver_df = spark.read.table("silver_taxi")
    weather_df = spark.read.table("weather_daily")
    
    date_df = (
        silver_df
        .select(F.to_date("pickup_due_ts").alias("trip_date"))
        .distinct()
        .filter(F.col("trip_date").isNotNull())
    )
    
    return (
        date_df
        .withColumn("date_key", F.date_format("trip_date", "yyyyMMdd").cast("int"))
        .withColumn("full_date", F.col("trip_date"))
        .withColumn("day", F.dayofmonth("trip_date"))
        .withColumn("day_name", F.date_format("trip_date", "EEEE"))
        .withColumn("week", F.weekofyear("trip_date"))
        .withColumn("month", F.month("trip_date"))
        .withColumn("month_name", F.date_format("trip_date", "MMMM"))
        .withColumn("quarter", F.quarter("trip_date"))
        .withColumn("year", F.year("trip_date"))
        .withColumn("weekend_flag", F.dayofweek("trip_date").isin(1, 7))
        .join(
            weather_df,
            F.col("trip_date") == F.col("date"),
            "left"
        )
        .drop("trip_date", "date")
    )