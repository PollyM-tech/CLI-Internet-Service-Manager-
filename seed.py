from faker import Faker
from models import Customer, Plan, Subscription, get_db

fake = Faker()

def seed_database(record_count=10):
    with get_db() as db:
        # Create Plans
        plans = [
            Plan(name="Basic", speed="10 Mbps", price=2500),
            Plan(name="Premium", speed="100 Mbps", price=9999)
        ]
        db.add_all(plans)
        db.commit()

        # Create Customers
        customers = []
        for _ in range(record_count):
            customers.append(
                Customer(
                    name=fake.name(),
                    email=fake.unique.email(),
                    router_id=fake.unique.random_number(digits=10),
                    phone=f"+2547{fake.random_number(digits=8)}"
                )
            )
        db.add_all(customers)
        db.commit()

        # Create Subscriptions
        for customer in customers:
            db.add(
                Subscription(
                    customer_id=customer.id,
                    plan_id=fake.random_element(plans).id,
                    router_id=fake.unique.random_number(digits=10),
                    status="active"
                )
            )
        db.commit()

if __name__ == "__main__":
    seed_database()
