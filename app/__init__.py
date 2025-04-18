from fastapi import FastAPI
from app.models.models import engine, Base

def create_app():
    # Create FastAPI app
    app = FastAPI(title="Store Monitoring API")
    
    # Include API router
    from app.api.routes import router as api_router
    app.include_router(api_router)
    
    # Create startup event
    @app.on_event("startup")
    async def startup_event():
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # Load data from CSV files
        from app.utils.helpers import load_csv_data
        load_csv_data()
    
    return app 