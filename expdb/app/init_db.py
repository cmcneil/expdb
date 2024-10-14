"""
Initialize the database (creates tables). This should only be run when creating
a new instance of expDB.
"""
from .db import init_db

# Call the function to initialize the database
init_db()

print("Database initialized successfully!")