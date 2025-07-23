-- Initial dealership configurations
-- Based on the 39 dealerships mentioned in the planning documents

INSERT INTO dealership_configs (name, filtering_rules, output_rules, qr_output_path) VALUES
-- Example dealership configurations
-- You'll need to customize these based on your specific dealerships
('suntrupfordwest', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard"}',
    'C:\\qr_codes\\suntrupfordwest\\'),
    
('example_dealership_2', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard"}',
    'C:\\qr_codes\\example_dealership_2\\'),
    
('example_dealership_3', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard"}',
    'C:\\qr_codes\\example_dealership_3\\')
    
-- Add remaining 36 dealerships here with their specific configurations
ON CONFLICT (name) DO UPDATE SET
    filtering_rules = EXCLUDED.filtering_rules,
    output_rules = EXCLUDED.output_rules,
    qr_output_path = EXCLUDED.qr_output_path,
    updated_at = CURRENT_TIMESTAMP;

-- Example of filtering rules JSON structure:
/*
{
    "exclude_conditions": ["offlot"],  -- Exclude off-lot vehicles
    "require_stock": true,              -- Must have stock number
    "min_price": 0,                     -- Minimum price filter
    "max_price": 100000,                -- Maximum price filter
    "exclude_makes": [],                -- List of makes to exclude
    "include_only_makes": [],           -- If set, only include these makes
    "exclude_models": [],               -- List of models to exclude
    "year_min": 2020,                   -- Minimum year
    "year_max": 2025                    -- Maximum year
}
*/

-- Example of output rules JSON structure:
/*
{
    "include_qr": true,                 -- Include QR code path in output
    "format": "standard",               -- Output format type
    "fields": [                         -- Custom field selection
        "vin", "stock", "year", "make", 
        "model", "trim", "price"
    ],
    "sort_by": ["make", "model"],      -- Sort order for output
    "group_by": "vehicle_condition"     -- Grouping for output
}
*/