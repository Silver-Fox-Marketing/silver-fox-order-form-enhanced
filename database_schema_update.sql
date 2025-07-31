-- Database Schema Updates for VIN History and Time Tracking
-- Silver Fox Order Processing System

-- First, let's ensure the vin_history table exists with proper structure
CREATE TABLE IF NOT EXISTS vin_history (
    id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) NOT NULL,
    vin VARCHAR(17) NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dealership_name, vin, order_date)
);

-- Add time_scraped column to raw_vehicle_data if it doesn't exist
ALTER TABLE raw_vehicle_data 
ADD COLUMN IF NOT EXISTS time_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index on time_scraped for performance
CREATE INDEX IF NOT EXISTS idx_raw_vehicle_data_time_scraped 
ON raw_vehicle_data(time_scraped);

-- Create index on vin_history for faster lookups
CREATE INDEX IF NOT EXISTS idx_vin_history_dealership_date 
ON vin_history(dealership_name, order_date);

CREATE INDEX IF NOT EXISTS idx_vin_history_vin 
ON vin_history(vin);

-- Update existing raw_vehicle_data records to have a time_scraped value based on import_timestamp
UPDATE raw_vehicle_data 
SET time_scraped = import_timestamp 
WHERE time_scraped IS NULL AND import_timestamp IS NOT NULL;

-- For records with no import_timestamp, set a default recent time
UPDATE raw_vehicle_data 
SET time_scraped = CURRENT_TIMESTAMP - INTERVAL '1 day'
WHERE time_scraped IS NULL;