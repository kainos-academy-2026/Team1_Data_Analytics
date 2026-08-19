# **Team 1 Data Analytics Project**

## Entities:
- Trips
- Dates
- Zones

## Grain:
- One row in the primary fact table = one trip that has either been completed, cancelled, or for which there was no fare.

## Time columns:
- dispatch_timestamp
- pickup_due_timestamp

## Natural keys: 
- booking_id
- driver_id
- vehicle_id
- dispatcher_id

## Measures (Derived Values; Additive Facts):
- Fare amount
- Distance
- expected_vs_actual_pickup_minutes_difference
- dispatch_to_arrival_minutes
- trip_duration_minutes


## Attributes (Descriptive):
- Status
- Booking source
- Priority level
- Capabilities
- Dispatch timestamp
- Pickup due timestamp


## TO DO:
 dataset assumptions, architecture, how to run, business questions answered, and which stretch feature(s) you attempted.