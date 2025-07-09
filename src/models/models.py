# src/models/models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TimeLapseData(Base):
    __tablename__ = "time_lapse_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    image_path = Column(String(255))