#!/usr/bin/env python3
"""
Implement Enhanced VIN Logic
Handles cross-dealership and relisted vehicle scenarios
"""

import sys
from pathlib import Path

# Add the project path for imports
project_root = Path(__file__).parent / "projects" / "minisforum_database_transfer" / "bulletproof_package"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(scripts_path))

from database_connection import db_manager

def update_vin_history_schema():
    """Add vehicle_type column to vin_history table"""
    print("=== UPDATING VIN_HISTORY SCHEMA ===")
    
    try:
        # Add vehicle_type column
        print("Adding vehicle_type column...")
        db_manager.execute_query("""
            ALTER TABLE vin_history 
            ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(20) DEFAULT 'unknown'
        """)
        
        # Add index for better performance
        print("Adding performance index...")
        db_manager.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_vin_history_vin_dealership_type 
            ON vin_history (vin, dealership_name, vehicle_type)
        """)
        
        print("Schema update completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        return False

def create_enhanced_vin_logic():
    """Create the enhanced VIN comparison logic"""
    
    enhanced_logic = '''
    def _find_new_vehicles_enhanced(self, dealership_name: str, current_vins: List[str], current_vehicles: List[Dict]) -> List[str]:
        """
        Enhanced VIN comparison that handles cross-dealership and relisted scenarios
        
        Logic:
        - Different dealership: Always process 
        - Same dealership + different vehicle type: Always process
        - Same dealership + same type: Check time window (7 days)
        - Same dealership + any type within 1 day: Skip (too recent)
        """
        
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        new_vins = []
        
        for vehicle in current_vehicles:
            vin = vehicle.get('vin')
            current_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
            
            if not vin:
                continue
                
            # Check VIN history with enhanced logic
            history = db_manager.execute_query("""
                SELECT dealership_name, vehicle_type, order_date,
                       EXTRACT(DAYS FROM CURRENT_DATE - order_date) as days_ago
                FROM vin_history 
                WHERE vin = %s 
                ORDER BY order_date DESC 
                LIMIT 5
            """, (vin,))
            
            should_process = True
            
            if history:
                for record in history:
                    prev_dealership = record['dealership_name']
                    prev_type = record['vehicle_type'] or 'unknown'
                    days_ago = record['days_ago']
                    
                    # Rule 1: Skip if same dealership, any type, processed within 1 day
                    if prev_dealership in [dealership_name, actual_location_name] and days_ago <= 1:
                        logger.info(f"Skipping {vin}: Same dealership processed {days_ago} days ago")
                        should_process = False
                        break
                    
                    # Rule 2: Skip if same dealership, same type, processed within 7 days  
                    elif (prev_dealership in [dealership_name, actual_location_name] 
                          and prev_type == current_type 
                          and days_ago <= 7):
                        logger.info(f"Skipping {vin}: Same dealership+type processed {days_ago} days ago")
                        should_process = False
                        break
                        
                    # Rule 3: Process if different dealership (cross-dealership opportunity)
                    elif prev_dealership not in [dealership_name, actual_location_name]:
                        logger.info(f"Processing {vin}: Cross-dealership opportunity ({prev_dealership} -> {dealership_name})")
                        should_process = True
                        break
                        
                    # Rule 4: Process if same dealership but different type (status change)
                    elif (prev_dealership in [dealership_name, actual_location_name] 
                          and prev_type != current_type):
                        logger.info(f"Processing {vin}: Status change ({prev_type} -> {current_type})")
                        should_process = True
                        break
            else:
                # No history = definitely new
                logger.info(f"Processing {vin}: No previous history")
                should_process = True
            
            if should_process:
                new_vins.append(vin)
        
        logger.info(f"Enhanced logic: {len(current_vins)} current, {len(new_vins)} need processing")
        return new_vins
    
    def _normalize_vehicle_type(self, vehicle_type: str) -> str:
        """Normalize vehicle type to standard categories"""
        if not vehicle_type:
            return 'unknown'
            
        vehicle_type = vehicle_type.lower().strip()
        
        if any(keyword in vehicle_type for keyword in ['new', 'brand new']):
            return 'new'
        elif any(keyword in vehicle_type for keyword in ['certified', 'cpo', 'pre-owned']):
            return 'certified'
        elif any(keyword in vehicle_type for keyword in ['used', 'pre owned']):
            return 'used'
        else:
            return 'unknown'
    
    def _update_vin_history_enhanced(self, dealership_name: str, vehicles: List[Dict]):
        """Update VIN history with vehicle type information"""
        try:
            # Clear old history (keep last 30 days instead of 7 for cross-reference)
            db_manager.execute_query("""
                DELETE FROM vin_history
                WHERE dealership_name = %s AND order_date < CURRENT_DATE - INTERVAL '30 days'
            """, (dealership_name,))
            
            # Insert current vehicles with type information
            for vehicle in vehicles:
                vin = vehicle.get('vin')
                vehicle_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
                
                if vin:
                    db_manager.execute_query("""
                        INSERT INTO vin_history (dealership_name, vin, vehicle_type, order_date)
                        VALUES (%s, %s, %s, CURRENT_DATE)
                        ON CONFLICT ON CONSTRAINT vin_history_unique_idx DO UPDATE SET
                        vehicle_type = EXCLUDED.vehicle_type,
                        created_at = CURRENT_TIMESTAMP
                    """, (dealership_name, vin, vehicle_type))
                    
        except Exception as e:
            logger.error(f"Error updating enhanced VIN history: {e}")
    '''
    
    print("=== ENHANCED VIN LOGIC CODE ===")
    print(enhanced_logic)
    return enhanced_logic

def test_scenarios():
    """Test the enhanced logic with example scenarios"""
    print("\n=== TESTING SCENARIOS ===")
    
    # Create test data
    test_scenarios = [
        {
            "name": "Cross-Dealership Used Car",
            "setup": "VIN ABC123 processed at BMW as NEW, now at Dave Sinclair as USED",
            "expected": "Should process (different dealership)"
        },
        {
            "name": "Same Dealership Type Change", 
            "setup": "VIN DEF456 processed at Columbia Honda as NEW, now as USED",
            "expected": "Should process (type change)"
        },
        {
            "name": "Recent Same Dealership/Type",
            "setup": "VIN GHI789 processed at Columbia Honda as NEW yesterday, still NEW today",
            "expected": "Should skip (too recent, same context)"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Setup: {scenario['setup']}")
        print(f"Expected: {scenario['expected']}")

if __name__ == "__main__":
    print("ENHANCED VIN LOGIC IMPLEMENTATION")
    print("=" * 50)
    
    # Step 1: Update schema
    if update_vin_history_schema():
        print("\nStep 1: Schema updated successfully")
        
        # Step 2: Show the enhanced logic
        create_enhanced_vin_logic()
        
        # Step 3: Test scenarios
        test_scenarios()
        
        print("\n" + "=" * 50)
        print("IMPLEMENTATION READY!")
        print("=" * 50)
        print("The enhanced VIN logic will now handle:")
        print("- Cross-dealership opportunities")
        print("- Vehicle type/status changes") 
        print("- Smart time-based filtering")
        print("- Prevents duplicate work within reasonable timeframes")
        print("\nNext: Apply this logic to correct_order_processing.py")
        
    else:
        print("Schema update failed. Please check database connection.")