# 🌐 Lintech ISP Management CLI

A command-line interface (CLI) for managing an Internet Service Provider (ISP). 
-Built with Python, SQLAlchemy, and SQLite, this tool manages customers, plans, subscriptions, and sends renewal reminders.

## Features
- **Customer Management**: Add, list, search, update, and delete customers with `created_at` and `updated_at` timestamps.
- **Plan Management**: Create, list, and delete internet plans with pricing in KES and timestamps.
- **Subscription Management**: Manage subscriptions with `start_date`, `end_date`, `created_at`, `updated_at`, and `last_reminder_sent` timestamps.
- **Admin Utilities**: Send email reminders for subscriptions expiring within 7 days, generate CSV reports, and backup the database.
- **Test Data**: Generate realistic or controlled datasets with timestamps.
- **Logging**: Detailed logs for all operations and errors.

## Requirements
- Python 3.8+
- Dependencies (install via `pipenv install`):
  - SQLAlchemy==2.0.35
  - Alembic==1.13.3
  - Faker==30.3.0
  - python-dotenv==1.0.1
  - python-dateutil==2.9.0
  - colorama==0.4.6
  - prettytable==3.11.0
  - click==8.1.7
  - pytest==8.3.3 (dev)
  - pytest-mock==3.14.0 (dev)
  - ipdb==0.13.13 (dev)

  ## Setup
1. Install depencies
pipenv install --dev
pipenv shell
2. Configure environment variables for email reminders in .env:

EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
3. Initialize the database with Alembic:
cd lib/db
alembic init migrations
- Update alembic.ini:
sqlalchemy.url = sqlite:///../../internet_service.db

- Update migrations/env.py to include:
from models import Base
target_metadata = Base.metadata

- Generate and apply migration:
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

- Seed the database with test data:
python seed.py

## Usage
**Run the CLI:**
python cli.py
Use the menu to manage customers, plans, subscriptions, or send reminders.
#  Testing & Seeding
**Controlled Test Data** 
python test_data.py
- Option 1: Creates 2 plans, 5 customers, 5 subscriptions
- Option 2: Runs validation tests for inputs
- Option 3: Runs edge case tests for phone, email, - - price, and dates
- Option 4: Runs CRUD tests
- Option 5: Generates test case definitions
**Randomized Realistic Data**
python seed.py
- 10 customers, 2 plans, random subscriptions using Faker
- Includes timestamps and phone/email validation


**Debugging**
python debug.py
Inspect logs in the console or implement a debug.py script to view database contents.

# File Structure
cli.py: Main CLI script.
lib/models/: Database models (customer.py, plan.py, subscription.py, database.py).
lib/helpers/: CRUD helper functions.
seed.py: Database seeding with Faker.
test_data.py: Controlled test data and tests.
.env, .env.testing: Environment variables.
alembic/: Database migrations.
Pipfile: Dependency management.

# Database Schema
- view schema: https://dbdiagram.io/d/CLI-Internet-Service-Manager-68343a530240c65c4438b599

- Customer: 
id, router_id, name, email, phone, address, created_at, updated_at.
- Plan: 
id, name, description, price, speed, duration_months, created_at, updated_at.
- Subscription: 
id, customer_id, plan_id, router_id, status, start_date, end_date, created_at, updated_at, last_reminder_sent.

# License
Pauline Moraa
Inspired by real-world ISP workflows in Kenya