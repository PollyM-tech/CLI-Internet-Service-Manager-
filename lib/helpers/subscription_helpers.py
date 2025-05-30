from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, or_
from lib.models import Subscription, Customer, Plan

def validate_subscription_input(customer_id, plan_id, duration):
    errors = []
    if not customer_id.isdigit():
        errors.append("Customer ID must be a number")
    if not plan_id.isdigit():
        errors.append("Plan ID must be a number")
    if not duration.isdigit() or int(duration) < 1:
        errors.append("Duration must be at least 1 month")
    return errors

def create_subscription(db):
    print("\n➕ Create New Subscription")
    
    customers = db.query(Customer).order_by(Customer.name).all()
    if not customers:
        print("❌ No customers available")
        return
    
    print("\nAvailable Customers:")
    for cust in customers:
        active_subs = len([s for s in cust.subscriptions if s.status == 'active'])
        print(f"{cust.id}. {cust.name} (Router: {cust.router_id}) - {active_subs} active plans")

    plans = db.query(Plan).order_by(Plan.price).all()
    if not plans:
        print("❌ No plans available")
        return
    
    print("\nAvailable Plans:")
    for plan in plans:
        print(f"{plan.id}. {plan.name} ({plan.speed}) - KES {plan.price:,.2f}")

    cust_id = input("\nCustomer ID: ").strip()
    plan_id = input("Plan ID: ").strip()
    duration = input("Duration (months) [1]: ").strip() or "1"

    errors = validate_subscription_input(cust_id, plan_id, duration)
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"- {error}")
        return

    customer = db.get(Customer, int(cust_id))
    plan = db.get(Plan, int(plan_id))

    if not customer:
        print("❌ Customer not found")
        return
    if not plan:
        print("❌ Plan not found")
        return

    start_date = date.today()
    end_date = start_date + relativedelta(months=int(duration))

    try:
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            router_id=customer.router_id,
            status='active',
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        )
        db.add(subscription)
        db.commit()
        print(f"\n✅ Subscription created successfully!")
        print(f"Customer: {customer.name}")
        print(f"Plan: {plan.name} ({plan.speed})")
        print(f"Duration: {duration} months")
        print(f"Start: {start_date}")
        print(f"End: {end_date}")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating subscription: {str(e)}")

def list_subscriptions(db, status='active'):
    query = db.query(Subscription)
    
    if status == 'active':
        query = query.filter(
            and_(
                Subscription.status == 'active',
                or_(
                    Subscription.end_date == None,
                    Subscription.end_date >= date.today()
                )
            )
        )
    elif status == 'expired':
        query = query.filter(
            and_(
                Subscription.status == 'active',
                Subscription.end_date < date.today()
            )
        )

    subscriptions = query.order_by(Subscription.start_date).all()
    
    print(f"\n📋 Subscriptions ({status})")
    print("-" * 60)
    for sub in subscriptions:
        customer = db.get(Customer, sub.customer_id)
        plan = db.get(Plan, sub.plan_id)
        days_left = (sub.end_date - date.today()).days if sub.end_date else None
        
        print(f"\nID: {sub.id}")
        print(f"Customer: {customer.name} (Router: {sub.router_id})")
        print(f"Plan: {plan.name} ({plan.speed}) - KES {plan.price:,.2f}")
        print(f"Status: {sub.status}")
        print(f"Period: {sub.start_date} to {sub.end_date or 'Ongoing'}")
        if days_left is not None:
            print(f"Days Remaining: {days_left}")
    print("-" * 60)
    print(f"Total: {len(subscriptions)} subscriptions")

def update_subscription(db):
    list_subscriptions(db, 'all')
    sub_id = input("\nEnter Subscription ID to update: ").strip()
    
    subscription = db.get(Subscription, int(sub_id)) if sub_id.isdigit() else None
    if not subscription:
        print("❌ Subscription not found")
        return

    print("\n1. Update Status")
    print("2. Extend Duration")
    choice = input("\nWhat to update? (1-2): ").strip()

    if choice == "1":
        print("\n1. Active")
        print("2. Suspended")
        print("3. Terminated")
        status_choice = input("New Status (1-3): ").strip()
        
        status_map = {'1': 'active', '2': 'suspended', '3': 'terminated'}
        if status_choice in status_map:
            subscription.status = status_map[status_choice]
            subscription.updated_at = datetime.now()
            
            if status_choice == '1' and subscription.end_date and subscription.end_date < date.today():
                extend = input("Subscription expired. Extend by how many months? (0 to keep expired): ").strip()
                if extend.isdigit() and int(extend) > 0:
                    subscription.end_date = date.today() + relativedelta(months=int(extend))
            
            db.commit()
            print("\n✅ Status updated successfully!")
        else:
            print("❌ Invalid choice")

    elif choice == "2":
        if not subscription.end_date:
            print("❌ Cannot extend - subscription has no end date")
            return
            
        months = input(f"Extend beyond {subscription.end_date} by how many months? ").strip()
        if not months.isdigit() or int(months) < 1:
            print("❌ Must extend by at least 1 month")
            return
            
        subscription.end_date += relativedelta(months=int(months))
        subscription.updated_at = datetime.now()
        db.commit()
        print(f"\n✅ Extended to {subscription.end_date}")

    else:
        print("❌ Invalid choice")

def delete_subscription(db):
    list_subscriptions(db, 'active')
    sub_id = input("\nEnter Subscription ID to cancel: ").strip()
    
    subscription = db.get(Subscription, int(sub_id)) if sub_id.isdigit() else None
    if not subscription:
        print("❌ Subscription not found")
        return

    confirm = input(f"\n⚠️ Cancel subscription {sub_id}? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("❌ Cancellation aborted")
        return

    try:
        subscription.status = 'terminated'
        subscription.updated_at = datetime.now()
        db.commit()
        print("\n✅ Subscription cancelled successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error cancelling subscription: {str(e)}")

def check_expiring_subscriptions(db):
    today = date.today()
    deadline = today + relativedelta(days=7)
    
    expiring = db.query(Subscription).join(Customer).filter(
        and_(
            Subscription.status == 'active',
            Subscription.end_date.between(today, deadline),
            or_(
                Subscription.last_reminder_sent == None,
                Subscription.last_reminder_sent < today
            )
        )
    ).all()

    if not expiring:
        print("\nNo subscriptions need reminders right now")
        return

    print(f"\n🔔 Found {len(expiring)} subscriptions needing reminders:")
    for sub in expiring:
        customer = sub.customer
        plan = sub.plan
        days_left = (sub.end_date - today).days
        
        print(f"\n- {customer.name}: {plan.name} expires in {days_left} days")
        if customer.email:
            print(f"  Email: {customer.email}")
            print("  [Email reminder would be sent here]")
            sub.last_reminder_sent = today
        else:
            print("  ❌ No email on file - cannot send reminder")
    
    db.commit()
    print("\n✅ Reminder flags updated")
