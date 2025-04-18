import pandas as pd
from datetime import datetime
import pytz
import os
from app.models.models import SessionLocal, StoreStatus, BusinessHours, StoreTimezone

def load_csv_data():
    """
    Load CSV data into the database if not already loaded.
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(StoreStatus).count() > 0:
            print("Data already loaded into the database.")
            return
        
        print("Loading data from CSV files...")
        
        # Load store status data
        print("Loading store status data...")
        status_df = pd.read_csv('store_status.csv')
        status_df['timestamp_utc'] = pd.to_datetime(status_df['timestamp_utc'])
        
        # Insert in batches to avoid memory issues
        batch_size = 10000
        total_batches = (len(status_df) // batch_size) + (1 if len(status_df) % batch_size > 0 else 0)
        
        for i in range(0, len(status_df), batch_size):
            batch = status_df.iloc[i:i+batch_size]
            status_records = []
            
            for _, row in batch.iterrows():
                status = StoreStatus(
                    store_id=row['store_id'],
                    timestamp_utc=row['timestamp_utc'],
                    status=row['status']
                )
                status_records.append(status)
            
            db.bulk_save_objects(status_records)
            db.commit()
            print(f"Loaded store status batch {i//batch_size + 1}/{total_batches}")
        
        # Load business hours data
        print("Loading business hours data...")
        hours_df = pd.read_csv('menu_hours.csv')
        hours_records = []
        
        for _, row in hours_df.iterrows():
            hours = BusinessHours(
                store_id=row['store_id'],
                day_of_week=row['dayOfWeek'],
                start_time_local=datetime.strptime(row['start_time_local'], '%H:%M:%S').time(),
                end_time_local=datetime.strptime(row['end_time_local'], '%H:%M:%S').time()
            )
            hours_records.append(hours)
            
            # Commit in batches
            if len(hours_records) >= 5000:
                db.bulk_save_objects(hours_records)
                db.commit()
                hours_records = []
        
        # Commit any remaining records
        if hours_records:
            db.bulk_save_objects(hours_records)
            db.commit()
        
        print("Loaded business hours data")
        
        # Load timezone data
        print("Loading timezone data...")
        timezone_df = pd.read_csv('timezones.csv')
        timezone_records = []
        
        for _, row in timezone_df.iterrows():
            timezone = StoreTimezone(
                store_id=row['store_id'],
                timezone_str=row['timezone_str']
            )
            timezone_records.append(timezone)
            
            # Commit in batches
            if len(timezone_records) >= 1000:
                db.bulk_save_objects(timezone_records)
                db.commit()
                timezone_records = []
        
        # Commit any remaining records
        if timezone_records:
            db.bulk_save_objects(timezone_records)
            db.commit()
        
        print("Loaded timezone data")
        
        print("Data loading complete!")
    
    finally:
        db.close() 