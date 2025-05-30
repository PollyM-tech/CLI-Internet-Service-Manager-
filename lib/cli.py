"""
Internet Service Manager CLI - Production Grade
"""

import sys
import re
from datetime import date
from typing import Callable, Optional
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

from models import (
    Base, Customer, Plan, Subscription,
    InvalidEmailError, InvalidPhoneError,
    InvalidSpeedError, InvalidSubscriptionDateError,
    get_db
)

class InternetServiceCLI:
    def __init__(self):
        self.session = None

    def run(self):
        self.print_banner()
        try:
            while True:
                self.main_menu()
        except KeyboardInterrupt:
            self.exit_gracefully()
        except Exception as e:
            self.print_error(f"Fatal error: {str(e)}")
            sys.exit(1)

    def execute_with_session(self, operation: Callable):
        try:
            with get_db() as db:
                self.session = db
                operation()
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            if self.session:
                self.session.rollback()
        finally:
            self.session = None

    def print_banner(self):
        print(f"\n{Fore.CYAN}🌐 Internet Service Manager CLI 🌐")
        print(f"{Fore.YELLOW}Enterprise Grade | v3.0{Style.RESET_ALL}\n")

    def print_success(self, msg: str):
        print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")

    def print_error(self, msg: str):
        print(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")

    def confirm_action(self, prompt: str) -> bool:
        response = input(f"{prompt} (y/n): ").strip().lower()
        return response in ('y', 'yes')

    def get_valid_input(self, prompt: str, validator: Callable, error_msg: str, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            value = input(prompt).strip()
            try:
                if validator(value):
                    return value
                self.print_error(error_msg)
            except Exception as e:
                self.print_error(str(e))
            attempts += 1
        raise ValueError(f"Maximum attempts ({max_attempts}) exceeded")

    def main_menu(self):
        print("\n=== MAIN MENU ===")
        print("1. Customer Management")
        print("2. Plan Management")
        print("3. Subscription Management")
        print("4. System Tools")
        print("5. Exit")

        choice = input("> Select option (1-5): ").strip()
        {
            "1": lambda: self.execute_with_session(self.customer_menu),
            "2": lambda: self.execute_with_session(self.plan_menu),
            "3": lambda: self.execute_with_session(self.subscription_menu),
            "4": lambda: self.execute_with_session(self.system_tools_menu),
            "5": self.exit_gracefully
        }.get(choice, self.invalid_choice)()

    def invalid_choice(self):
        self.print_error("Invalid selection. Please try again.")

    # === Customer Operations ===
    def customer_menu(self):
        from lib.helpers import (
            create_customer, list_customers, search_customers,
            update_customer, delete_customer
        )
        while True:
            print("\n📋 CUSTOMER MENU")
            print("1. Add Customer")
            print("2. List Customers")
            print("3. Search Customers")
            print("4. Update Customer")
            print("5. Delete Customer")
            print("6. Back to Main")
            choice = input("> ").strip()
            if choice == "6":
                break
            {
                "1": lambda: create_customer(self.session),
                "2": lambda: list_customers(self.session, True),
                "3": lambda: search_customers(self.session),
                "4": lambda: update_customer(self.session),
                "5": lambda: delete_customer(self.session),
            }.get(choice, self.invalid_choice)()

    # === Plan Operations ===
    def plan_menu(self):
        from lib.helpers import (
            create_plan, list_plans,
            update_plan, delete_plan
        )
        while True:
            print("\n📶 PLAN MENU")
            print("1. Create Plan")
            print("2. List Plans")
            print("3. Update Plan")
            print("4. Delete Plan")
            print("5. Back to Main")
            choice = input("> ").strip()
            if choice == "5":
                break
            {
                "1": lambda: create_plan(self.session),
                "2": lambda: list_plans(self.session, True),
                "3": lambda: update_plan(self.session),
                "4": lambda: delete_plan(self.session),
            }.get(choice, self.invalid_choice)()

    # === Subscription Operations ===
    def subscription_menu(self):
        from lib.helpers import (
            create_subscription, list_subscriptions,
            update_subscription, delete_subscription,
            check_expiring_subscriptions
        )
        while True:
            print("\n🔗 SUBSCRIPTION MENU")
            print("1. Create Subscription")
            print("2. List Active Subscriptions")
            print("3. Update Subscription")
            print("4. Cancel Subscription")
            print("5. Check Expiring")
            print("6. Back to Main")
            choice = input("> ").strip()
            if choice == "6":
                break
            {
                "1": lambda: create_subscription(self.session),
                "2": lambda: list_subscriptions(self.session),
                "3": lambda: update_subscription(self.session),
                "4": lambda: delete_subscription(self.session),
                "5": lambda: check_expiring_subscriptions(self.session),
            }.get(choice, self.invalid_choice)()

    # === System Tools ===
    def system_tools_menu(self):
        while True:
            print("\n🛠️ SYSTEM TOOLS")
            print("1. Seed Database")
            print("2. Back to Main")
            choice = input("> ").strip()
            if choice == "2":
                break
            if choice == "1":
                self.seed_database()

    def seed_database(self):
        if not self.confirm_action("Wipe and reseed database?"):
            return
        try:
            from faker import Faker
            fake = Faker()

            # Clear all data
            for table in reversed(Base.metadata.sorted_tables):
                self.session.execute(table.delete())

            # Add plans
            plans = [
                Plan(name="Basic", speed="10 Mbps", price=2500),
                Plan(name="Standard", speed="50 Mbps", price=6000),
                Plan(name="Premium", speed="100 Mbps", price=9999)
            ]
            self.session.add_all(plans)
            self.session.commit()

            # Add customers and subscriptions
            for _ in range(20):
                router_id = fake.unique.uuid4()[:10]  # Generate string router_id
                cust = Customer(
                    name=fake.name(),
                    email=fake.unique.email(),
                    router_id=router_id,
                    phone=f"+2547{fake.random_number(digits=8)}",
                    address=fake.address()
                )
                self.session.add(cust)
                self.session.flush()
                plan = fake.random_element(plans)
                self.session.add(
                    Subscription(
                        customer_id=cust.id,
                        plan_id=plan.id,
                        router_id=router_id,  # Use same string router_id
                        status=fake.random_element(('active', 'canceled', 'paused')),
                        start_date=date.today()
                    )
                )

            self.session.commit()
            self.print_success("Database seeded with 20 test records")
        except Exception as e:
            self.session.rollback()
            self.print_error(f"Seeding failed: {str(e)}")

    def exit_gracefully(self):
        print("\n🛑 Shutting down...")
        if self.session:
            self.session.close()
        sys.exit(0)

if __name__ == "__main__":
    try:
        cli = InternetServiceCLI()
        cli.run()
    except Exception as e:
        print(f"Fatal startup error: {str(e)}")
        sys.exit(1)