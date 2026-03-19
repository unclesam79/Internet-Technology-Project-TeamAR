Team project completed by Team AR as part of the course COMPSCI 5012: Internet Technology at the University of Glasgow.

## How to Run the Application

Activate the virtual environment, install dependencies, then start the development server:

```bash
# Windows
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

## Running the Test Suite

Activate the virtual environment, then run Django's test runner against the app:

```bash
# Windows
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate

python manage.py test maintenance_app
```

The test suite covers models, authentication, role-based access, and all API endpoints (34 tests total).
