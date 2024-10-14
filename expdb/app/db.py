from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Base  # Import Base from models/__init__.py
from .config import get_config

config = get_config()

# Create the engine for PostgreSQL
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Function to initialize the database (creates tables)
def init_db():
    Base.metadata.create_all(engine)

def flush_db():
    Base.metadata.drop_all(engine)
