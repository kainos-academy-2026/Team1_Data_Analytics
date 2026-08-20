erDiagram

    FACT_TRIP {
        bigint trip_key PK
        string booking_id

        int trip_booked_for_date_key FK
        int pickup_zone_key FK
        int destination_zone_key FK

        string status
        string payment_type
        string booking_source
        string capabilities

        string driver_id
        string vehicle_id
        string dispatcher_id

        int priority_level

        double fare_amount
        double distance

        timestamp dispatch_timestamp
        timestamp pickup_due_timestamp

        double expected_vs_actual_pickup_minutes_difference
        double dispatch_to_arrival_minutes
        double trip_duration_minutes
    }

    DIM_DATE {
        int date_key PK

        date full_date

        int day
        string day_name

        int week

        int month
        string month_name

        int quarter

        int year

        boolean weekend_flag
    }

    DIM_ZONE {
        int zone_key PK

        string zone_code

        double latitude
        double longitude
    }

    DIM_DATE ||--o{ FACT_TRIP : trip_booked_for_date
    DIM_ZONE ||--o{ FACT_TRIP : pickup_zone
    DIM_ZONE ||--o{ FACT_TRIP : destination_zone