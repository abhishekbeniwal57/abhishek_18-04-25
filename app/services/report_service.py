import pandas as pd
import pytz
from datetime import datetime, timedelta, time
import os
import csv
import traceback
from sqlalchemy import func
from app.models.models import Report, StoreStatus, BusinessHours, StoreTimezone

def generate_report(report_id: str, db):
    """
    Generate a report of store uptime and downtime.
    
    Args:
        report_id: The unique identifier for the report
        db: The database session
    """
    try:
        print(f"Starting report generation for report_id: {report_id}")
        
        # Check if report exists, if not create one
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            print(f"Creating report record for {report_id}")
            report = Report(id=report_id)
            db.add(report)
            db.commit()
        
        # Get all unique store IDs
        stores_query = db.query(StoreStatus.store_id).distinct()
        
        # Process all stores
        store_ids = [row[0] for row in stores_query]
        print(f"Processing {len(store_ids)} stores")
        
        # Get current timestamp (max timestamp in our data)
        max_timestamp = db.query(func.max(StoreStatus.timestamp_utc)).scalar()
        print(f"Max timestamp in data: {max_timestamp}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output file
        output_file = os.path.join(output_dir, f"report_{report_id}.csv")
        print(f"Report will be saved to: {output_file}")
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'store_id', 
                'uptime_last_hour(in minutes)', 
                'uptime_last_day(in hours)', 
                'update_last_week(in hours)', 
                'downtime_last_hour(in minutes)', 
                'downtime_last_day(in hours)', 
                'downtime_last_week(in hours)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Process each store
            for i, store_id in enumerate(store_ids):
                # Print progress every 100 stores
                if i % 100 == 0:
                    print(f"Processing store {i+1}/{len(store_ids)}")
                
                # Get timezone for the store
                timezone_record = db.query(StoreTimezone).filter(StoreTimezone.store_id == store_id).first()
                timezone_str = timezone_record.timezone_str if timezone_record else 'America/Chicago'
                
                # Get business hours for the store
                business_hours = db.query(BusinessHours).filter(BusinessHours.store_id == store_id).all()
                
                # Compute uptime and downtime
                result = compute_uptime_downtime(store_id, max_timestamp, timezone_str, business_hours, db)
                
                # Write result to CSV
                writer.writerow(result)
        
        # Update report status
        report.status = "Complete"
        report.completed_at = datetime.utcnow()
        report.file_path = os.path.abspath(output_file)
        db.commit()
        print(f"Report generation completed for report_id: {report_id}")
        
    except Exception as e:
        print(f"Error generating report: {e}")
        print(traceback.format_exc())
        
        # Update report as failed
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = "Failed"
                db.commit()
        except Exception as inner_e:
            print(f"Error updating report status: {inner_e}")

def compute_uptime_downtime(store_id, current_timestamp, timezone_str, business_hours_data, db):
    try:
        # Get the store's timezone
        tz = pytz.timezone(timezone_str)
        
        # Define the time intervals
        hour_ago = current_timestamp - timedelta(hours=1)
        day_ago = current_timestamp - timedelta(days=1)
        week_ago = current_timestamp - timedelta(days=7)
        
        # Get store status data for each interval
        hour_data = db.query(StoreStatus).filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= hour_ago,
            StoreStatus.timestamp_utc <= current_timestamp
        ).order_by(StoreStatus.timestamp_utc).all()
        
        day_data = db.query(StoreStatus).filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= day_ago,
            StoreStatus.timestamp_utc <= current_timestamp
        ).order_by(StoreStatus.timestamp_utc).all()
        
        week_data = db.query(StoreStatus).filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= week_ago,
            StoreStatus.timestamp_utc <= current_timestamp
        ).order_by(StoreStatus.timestamp_utc).all()
        
        # Calculate uptime and downtime for each interval
        uptime_last_hour, downtime_last_hour = calculate_uptime_downtime(
            hour_data, hour_ago, current_timestamp, business_hours_data, tz, interval='hour'
        )
        
        uptime_last_day, downtime_last_day = calculate_uptime_downtime(
            day_data, day_ago, current_timestamp, business_hours_data, tz, interval='day'
        )
        
        uptime_last_week, downtime_last_week = calculate_uptime_downtime(
            week_data, week_ago, current_timestamp, business_hours_data, tz, interval='week'
        )
        
        return {
            'store_id': store_id,
            'uptime_last_hour(in minutes)': round(uptime_last_hour, 2),
            'uptime_last_day(in hours)': round(uptime_last_day, 2),
            'update_last_week(in hours)': round(uptime_last_week, 2),
            'downtime_last_hour(in minutes)': round(downtime_last_hour, 2),
            'downtime_last_day(in hours)': round(downtime_last_day, 2),
            'downtime_last_week(in hours)': round(downtime_last_week, 2)
        }
    except Exception as e:
        print(f"Error computing uptime/downtime for store {store_id}: {e}")
        return {
            'store_id': store_id,
            'uptime_last_hour(in minutes)': 0,
            'uptime_last_day(in hours)': 0,
            'update_last_week(in hours)': 0,
            'downtime_last_hour(in minutes)': 0,
            'downtime_last_day(in hours)': 0,
            'downtime_last_week(in hours)': 0
        }

def calculate_uptime_downtime(status_data, start_time, end_time, business_hours, tz, interval='hour'):
    # If no business hours defined, assume 24/7 operation
    is_24x7 = len(business_hours) == 0
    
    # Convert UTC times to local timezone for business hours comparison
    local_start_time = start_time.replace(tzinfo=pytz.UTC).astimezone(tz)
    local_end_time = end_time.replace(tzinfo=pytz.UTC).astimezone(tz)
    
    # Calculate total business time in the interval
    total_business_minutes = calculate_business_minutes(local_start_time, local_end_time, business_hours, is_24x7)
    
    # If no business hours in this interval, return zeros
    if total_business_minutes == 0:
        if interval == 'hour':
            return 0, 0
        elif interval == 'day':
            return 0, 0
        else:  # week
            return 0, 0
    
    # Interpolate status between observations
    uptime_minutes = 0
    
    # Process status data during business hours only
    if len(status_data) == 0:
        # If no data points, assume all downtime during business hours
        uptime_minutes = 0
    elif len(status_data) == 1:
        # If only one data point, extrapolate to entire interval
        if status_data[0].status == 'active':
            uptime_minutes = total_business_minutes
    else:
        # Multiple data points - interpolate between them
        prev_time = None
        prev_status = None
        
        for i, status_entry in enumerate(status_data):
            status_time = status_entry.timestamp_utc
            status = status_entry.status
            local_time = status_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            
            # Skip if outside business hours
            if not is_24x7 and not is_within_business_hours(local_time, business_hours):
                continue
                
            if prev_time is None:
                # First valid observation - extrapolate backward to start
                if i == 0 and status == 'active':
                    # Calculate minutes from interval start to first observation
                    time_diff = (status_time - start_time).total_seconds() / 60
                    # Adjust for business hours
                    business_time_diff = min(time_diff, total_business_minutes)
                    uptime_minutes += business_time_diff if status == 'active' else 0
            else:
                # Calculate minutes between observations
                time_diff = (status_time - prev_time).total_seconds() / 60
                uptime_minutes += time_diff if prev_status == 'active' else 0
            
            # If last observation, extrapolate forward to end
            if i == len(status_data) - 1:
                time_diff = (end_time - status_time).total_seconds() / 60
                # Adjust for business hours
                business_time_diff = min(time_diff, total_business_minutes - uptime_minutes)
                uptime_minutes += business_time_diff if status == 'active' else 0
            
            prev_time = status_time
            prev_status = status
    
    # Calculate downtime
    downtime_minutes = total_business_minutes - uptime_minutes
    
    # Convert to appropriate units based on interval
    if interval == 'hour':
        return uptime_minutes, downtime_minutes
    elif interval == 'day':
        return uptime_minutes / 60, downtime_minutes / 60
    else:  # week
        return uptime_minutes / 60, downtime_minutes / 60

def calculate_business_minutes(start_time, end_time, business_hours, is_24x7):
    """Calculate the total business minutes within the given time range."""
    if is_24x7:
        # If 24/7 operation, all minutes are business minutes
        return (end_time - start_time).total_seconds() / 60
    
    total_minutes = 0
    current_time = start_time
    
    # Iterate through each day in the interval
    while current_time.date() <= end_time.date():
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        
        # Find business hours for this day
        day_hours = [h for h in business_hours if h.day_of_week == day_of_week]
        
        for hours in day_hours:
            # Convert business hours to datetime objects for this specific date
            business_start = datetime.combine(
                current_time.date(), 
                hours.start_time_local
            ).replace(tzinfo=current_time.tzinfo)
            
            business_end = datetime.combine(
                current_time.date(), 
                hours.end_time_local
            ).replace(tzinfo=current_time.tzinfo)
            
            # Handle business hours that span midnight
            if hours.end_time_local < hours.start_time_local:
                business_end += timedelta(days=1)
            
            # Find overlap with our interval
            interval_start = max(current_time, business_start)
            interval_end = min(end_time, business_end)
            
            # Add minutes if there is an overlap
            if interval_start < interval_end:
                total_minutes += (interval_end - interval_start).total_seconds() / 60
        
        # Move to next day
        next_day = (current_time + timedelta(days=1)).date()
        current_time = datetime.combine(next_day, time.min).replace(tzinfo=current_time.tzinfo)
    
    return total_minutes

def is_within_business_hours(local_time, business_hours):
    """Check if the given local time is within business hours."""
    day_of_week = local_time.weekday()  # 0=Monday, 6=Sunday
    
    # Check if the time falls within any business hours for this day
    for hours in business_hours:
        if hours.day_of_week == day_of_week:
            business_start = datetime.combine(
                local_time.date(), 
                hours.start_time_local
            ).replace(tzinfo=local_time.tzinfo)
            
            business_end = datetime.combine(
                local_time.date(), 
                hours.end_time_local
            ).replace(tzinfo=local_time.tzinfo)
            
            # Handle business hours that span midnight
            if hours.end_time_local < hours.start_time_local:
                business_end += timedelta(days=1)
            
            # Check if current time is within this business hour range
            if business_start <= local_time <= business_end:
                return True
    
    return False 