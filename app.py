from expdb.app import create_app
from expdb.app.populate_dev import populate_dev_data

from expdb.config import get_config


CONFIG = get_config()

# Initialize and run the Flask app
if __name__ == '__main__':
    if CONFIG.DEBUG:
        print("Running in DEBUG mode with DEV DB!")
        populate_dev_data()
    app = create_app()
    app.run(debug=True)
