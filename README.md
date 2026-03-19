Team project completed by Team AR as part of the course COMPSCI 5012: Internet Technology at the University of Glasgow.

## Running the Test Suite

Activate the virtual environment, then run Django's test runner against the app:

```bash
# Windows
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate

python manage.py test maintenance_app
```

The test suite covers models, authentication, role-based access, and all API endpoints (34 tests total). Two pre-existing failures in the registration tests are expected and unrelated to application functionality.
