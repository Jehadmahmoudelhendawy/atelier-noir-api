## Setup

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate       
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```


### 5. Create the PostgreSQL database

```sql
CREATE DATABASE assistify_db;
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Seed initial data (products + offers from chatData.js)

```bash
python manage.py seed_data
```

### 8. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 9. Start the development server

```bash
python manage.py runserver

