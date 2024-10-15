from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from .models import Base  # Import Base from models/__init__.py
# from ..config import get_config

# Create a global Base instance
Base = declarative_base()
# config = get_config()
# engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# Base.metadata.drop_all(engine)

# Import the models so they are registered with Base
from .subject import Subject
from .study import Study
from .timecourse import Data, DataType, Modality, Timecourse, TransformData
