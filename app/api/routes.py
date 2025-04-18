from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
import os
from app.models.models import Report, get_db
from app.services.report_service import generate_report

# Create API router
router = APIRouter()

@router.get("/trigger_report")
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger the generation of a new report.
    
    Returns:
        dict: A dictionary containing the report ID
    """
    # Generate a unique report ID
    report_id = str(uuid.uuid4())
    
    # Create a new report record
    new_report = Report(id=report_id)
    db.add(new_report)
    db.commit()
    
    # Start report generation in a background task
    background_tasks.add_task(generate_report, report_id, db)
    
    return {"report_id": report_id}

@router.get("/get_report")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a report or download the report if it's ready.
    
    Args:
        report_id (str): The ID of the report to get
        
    Returns:
        dict or FileResponse: The report status or the report file
    """
    if not report_id:
        raise HTTPException(status_code=400, detail="report_id is required")
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    print(f"Report status: {report.status}, File path: {report.file_path}")
    
    if report.status == "Running":
        return {"status": "Running"}
    
    if report.status == "Complete":
        # Check if file exists
        if report.file_path and os.path.exists(report.file_path):
            return FileResponse(
                path=report.file_path, 
                filename="report.csv", 
                media_type="text/csv"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Report file not found at {report.file_path}")
    
    raise HTTPException(status_code=500, detail="Report generation failed") 