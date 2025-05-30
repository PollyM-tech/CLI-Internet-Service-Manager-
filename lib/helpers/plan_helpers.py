from datetime import datetime
from lib.models import Plan

def validate_plan_data(name, speed, price):
    """Validate plan input data"""
    errors = []
    if not name:
        errors.append("Plan name is required")
    if not speed:
        errors.append("Speed description is required")
    try:
        price = float(price)
        if not (2000 <= price <= 100000):
            errors.append("Price must be between KES 2000-100000")
    except ValueError:
        errors.append("Invalid price format")
    return errors

def create_plan(db):
    """Create a new internet plan"""
    print("\n➕ Create New Plan")
    name = input("Plan Name: ").strip()
    speed = input("Speed (e.g. '10Mbps'): ").strip()
    desc = input("Description (optional): ").strip() or None
    price = input("Monthly Price (KES): ").strip()

    errors = validate_plan_data(name, speed, price)
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"- {error}")
        return

    try:
        plan = Plan(
            name=name,
            speed=speed,
            description=desc,
            price=float(price),
            created_at=datetime.now()
        )
        db.add(plan)
        db.commit()
        print(f"\n✅ Plan '{name}' created successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating plan: {str(e)}")

def list_plans(db, detailed=False):
    """List all available plans"""
    plans = db.query(Plan).order_by(Plan.price).all()
    
    if not plans:
        print("\nNo plans available")
        return

    print(f"\n📶 Internet Plans ({len(plans)} total)")
    for plan in plans:
        if detailed:
            print(f"\nID: {plan.id}")
            print(f"Name: {plan.name}")
            print(f"Speed: {plan.speed}")
            print(f"Price: KES {plan.price:,.2f}")
            print(f"Description: {plan.description or 'N/A'}")
            print(f"Created: {plan.created_at.date()}")
            print(f"Active Subs: {len(plan.subscriptions)}")
        else:
            print(f"{plan.id}. {plan.name} ({plan.speed}) - KES {plan.price:,.2f}")

def update_plan(db):
    """Update plan details"""
    list_plans(db, False)
    plan_id = input("\nEnter Plan ID to update: ").strip()
    
    plan = db.get(Plan, int(plan_id)) if plan_id.isdigit() else None
    if not plan:
        print("❌ Invalid Plan ID")
        return

    print(f"\nEditing: {plan.name} (ID: {plan.id})")
    new_name = input(f"Name [{plan.name}]: ").strip() or plan.name
    new_speed = input(f"Speed [{plan.speed}]: ").strip() or plan.speed
    new_desc = input(f"Description [{plan.description}]: ").strip() or plan.description
    new_price = input(f"Price [KES {plan.price}]: ").strip() or str(plan.price)

    errors = validate_plan_data(new_name, new_speed, new_price)
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"- {error}")
        return

    try:
        plan.name = new_name
        plan.speed = new_speed
        plan.description = new_desc
        plan.price = float(new_price)
        plan.updated_at = datetime.now()
        db.commit()
        print("\n✅ Plan updated successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error updating plan: {str(e)}")

def delete_plan(db):
    """Delete a plan after confirmation"""
    list_plans(db, False)
    plan_id = input("\nEnter Plan ID to delete: ").strip()
    
    plan = db.get(Plan, int(plan_id)) if plan_id.isdigit() else None
    if not plan:
        print("❌ Invalid Plan ID")
        return

    if plan.subscriptions:
        print("❌ Cannot delete - plan has active subscriptions")
        return

    confirm = input(f"\n⚠️ Delete {plan.name} (ID: {plan.id})? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("❌ Deletion cancelled")
        return

    try:
        db.delete(plan)
        db.commit()
        print("\n✅ Plan deleted successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error deleting plan: {str(e)}")
