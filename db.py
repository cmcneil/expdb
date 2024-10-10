from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Import Base from models/__init__.py
from config import Config

# Create the engine for PostgreSQL
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Function to initialize the database (creates tables)
def init_db():
    Base.metadata.create_all(engine)
