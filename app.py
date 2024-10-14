from expdb.app import create_app

# Initialize and run the Flask app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
