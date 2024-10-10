from sqlalchemy.orm import declarative_base

# Create a global Base instance
Base = declarative_base()

# Import the models so they are registered with Base
from .subject import Subject
from .study import Study
from .dataset import Dataset