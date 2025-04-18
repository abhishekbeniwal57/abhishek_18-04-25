from sqlalchemy import Column, String, Integer, DateTime, Time, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Define database URL
DATABASE_URL = "sqlite:///./app/store_monitor.db"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class StoreStatus(Base):
    __tablename__ = "store_status"

    id = Column(Integer, primary_key=True)
    store_id = Column(String(50), nullable=False, index=True)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    status = Column(String(10), nullable=False)
    
    def __repr__(self):
        return f"<StoreStatus store_id={self.store_id} timestamp={self.timestamp_utc} status={self.status}>"

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True)
    store_id = Column(String(50), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time_local = Column(Time, nullable=False)
    end_time_local = Column(Time, nullable=False)
    
    def __repr__(self):
        return f"<BusinessHours store_id={self.store_id} day={self.day_of_week} hours={self.start_time_local}-{self.end_time_local}>"

class StoreTimezone(Base):
    __tablename__ = "store_timezone"

    id = Column(Integer, primary_key=True)
    store_id = Column(String(50), nullable=False, unique=True, index=True)
    timezone_str = Column(String(50), nullable=False)
    
    def __repr__(self):
        return f"<StoreTimezone store_id={self.store_id} timezone={self.timezone_str}>"

class Report(Base):
    __tablename__ = "report"

    id = Column(String(50), primary_key=True)
    status = Column(String(10), default="Running")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    file_path = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<Report id={self.id} status={self.status}>"

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 