from datetime import datetime
from sqlalchemy import or_, String
from lib.models import Customer

def validate_customer_data(name, email, router_id):
    errors = []
    if not name:
        errors.append("Name is required")
    if not email or "@" not in email:
        errors.append("Valid email is required")
    if not router_id.isdigit() or len(router_id) != 10:
        errors.append("Router ID must be 10 digits")
    return errors

def create_customer(db):
    print("\n➕ Add New Customer")
    name = input("Full Name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (optional): ").strip() or None
    address = input("Address: ").strip()
    router_id = input("Router ID (10 digits): ").strip()

    errors = validate_customer_data(name, email, router_id)
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"- {error}")
        return

    try:
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            router_id=int(router_id),
            created_at=datetime.now()
        )
        db.add(customer)
        db.commit()
        print(f"\n✅ Customer '{name}' created successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating customer: {str(e)}")

def list_customers(db, detailed=False):
    customers = db.query(Customer).order_by(Customer.name).all()
    
    if not customers:
        print("\nNo customers found")
        return

    print(f"\n📋 Customer List ({len(customers)} total)")
    for cust in customers:
        if detailed:
            print(f"\nID: {cust.id}")
            print(f"Name: {cust.name}")
            print(f"Email: {cust.email}")
            print(f"Phone: {cust.phone or 'N/A'}")
            print(f"Router ID: {cust.router_id}")
            print(f"Address: {cust.address}")
            print(f"Created: {cust.created_at.date()}")
            print(f"Active Subs: {len([s for s in cust.subscriptions if s.status == 'active'])}")
        else:
            print(f"{cust.id}. {cust.name} ({cust.email})")

def search_customers(db):
    term = input("\n🔍 Search term: ").strip()
    if not term:
        print("❌ Please enter a search term")
        return

    results = db.query(Customer).filter(
        or_(
            Customer.name.ilike(f"%{term}%"),
            Customer.email.ilike(f"%{term}%"),
            Customer.router_id.cast(String).ilike(f"%{term}%")
        )
    ).all()

    if not results:
        print("\nNo matching customers found")
        return

    print(f"\n🔍 Found {len(results)} matching customers:")
    list_customers(db.query(Customer).filter(Customer.id.in_([c.id for c in results])), False)

def update_customer(db):
    list_customers(db, False)
    cust_id = input("\nEnter Customer ID to update: ").strip()
    
    customer = db.get(Customer, int(cust_id)) if cust_id.isdigit() else None
    if not customer:
        print("❌ Invalid Customer ID")
        return

    print(f"\nEditing: {customer.name} (ID: {customer.id})")
    new_name = input(f"Name [{customer.name}]: ").strip() or customer.name
    new_email = input(f"Email [{customer.email}]: ").strip() or customer.email
    new_phone = input(f"Phone [{customer.phone}]: ").strip() or customer.phone
    new_address = input(f"Address [{customer.address}]: ").strip() or customer.address

    errors = validate_customer_data(new_name, new_email, str(customer.router_id))
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"- {error}")
        return

    try:
        customer.name = new_name
        customer.email = new_email
        customer.phone = new_phone
        customer.address = new_address
        customer.updated_at = datetime.now()
        db.commit()
        print("\n✅ Customer updated successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error updating customer: {str(e)}")

def delete_customer(db):
    list_customers(db, False)
    cust_id = input("\nEnter Customer ID to delete: ").strip()
    
    customer = db.get(Customer, int(cust_id)) if cust_id.isdigit() else None
    if not customer:
        print("❌ Invalid Customer ID")
        return

    confirm = input(f"\n⚠️ Delete {customer.name} (ID: {customer.id})? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("❌ Deletion cancelled")
        return

    try:
        db.delete(customer)
        db.commit()
        print("\n✅ Customer deleted successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error deleting customer: {str(e)}")
