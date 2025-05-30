"""
Test Data Generator for Internet Service Manager CLI
"""
import os
import sys
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
from unittest.mock import patch
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load test environment
load_dotenv(".env.testing")

from lib.models import Customer, Plan, Subscription, get_db, InvalidEmailError, InvalidPhoneError, InvalidSubscriptionDateError
from lib.helpers.validation_helpers import validate_customer_data, validate_plan_data, validate_subscription_input
from lib.helpers.customer_helpers import create_customer, list_customers, update_customer, delete_customer
from lib.helpers.plan_helpers import create_plan, list_plans, update_plan, delete_plan
from lib.helpers.subscription_helpers import create_subscription, list_subscriptions, update_subscription, delete_subscription

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Faker.seed(0)
fake = Faker()

class TestDataGenerator:
    def __init__(self):
        self.db = None

    def _with_db(self, operation):
        """Execute operation with a database session."""
        try:
            with get_db() as db:
                self.db = db
                result = operation()
                return result
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            self.db = None

    def generate_test_cases(self):
        """Generate test cases for all helper functions."""
        return {
            "customer_validation": self._customer_validation_cases(),
            "plan_validation": self._plan_validation_cases(),
            "subscription_validation": self._subscription_validation_cases(),
            "edge_cases": self._edge_cases()
        }

    def _customer_validation_cases(self):
        return [
            {"name": "John Doe", "email": "john@example.com", "router_id": "1234567890", "expected": []},
            {"name": "", "email": "invalid", "router_id": "123", "expected": ["Name is required", "Valid email is required", "Router ID must be 10 digits"]}
        ]

    def _plan_validation_cases(self):
        return [
            {"name": "Basic Plan", "speed": "10 Mbps", "price": "5000", "expected": []},
            {"name": "", "speed": "", "price": "abc", "expected": ["Plan name is required", "Speed description is required", "Invalid price format"]}
        ]

    def _subscription_validation_cases(self):
        return [
            {"customer_id": "1", "plan_id": "1", "duration": "12", "expected": []},
            {"customer_id": "abc", "plan_id": "xyz", "duration": "0", "expected": ["Customer ID must be a number", "Plan ID must be a number", "Duration must be at least 1 month"]}
        ]

    def _edge_cases(self):
        return [
            {"phone": "+254712345678", "expected_valid": True},
            {"phone": "0712345678", "expected_valid": True},
            {"phone": "12345", "expected_valid": False},
            {"email": "test@example.com", "expected_valid": True},
            {"email": "invalid", "expected_valid": False},
            {"price": "5000", "expected_valid": True},
            {"price": "1000", "expected_valid": False},
            {"start_date": datetime.now().date(), "expected_valid": True},
            {"start_date": datetime.now().date() - timedelta(days=1), "expected_valid": True},
            {"start_date": "invalid", "expected_valid": False}
        ]

    def create_test_database(self):
        """Create a clean test database with controlled data."""
        def _create():
            try:
                self.db.query(Subscription).delete()
                self.db.query(Customer).delete()
                self.db.query(Plan).delete()
                self.db.commit()

                plans = [
                    Plan(name="Test Basic", speed="5 Mbps", price=2000, duration_months=1),
                    Plan(name="Test Premium", speed="50 Mbps", price=5000, duration_months=1)
                ]
                self.db.add_all(plans)
                self.db.commit()

                customers = [
                    Customer(
                        name=f"Test Customer {i+1}",
                        email=f"test{i+1}@example.com",
                        router_id=1000000000 + i,
                        phone=f"+2547{i+1}2345678"
                    ) for i in range(5)
                ]
                self.db.add_all(customers)
                self.db.commit()

                statuses = ["active", "suspended", "expired"]
                for i, customer in enumerate(customers):
                    self.db.add(
                        Subscription(
                            customer_id=customer.id,
                            plan_id=plans[i % len(plans)].id,
                            router_id=customer.router_id + 1000,
                            status=statuses[i % len(statuses)],
                            start_date=datetime.now().date() - timedelta(days=30),
                            end_date=datetime.now().date() + timedelta(days=30 * (i + 1)),
                            last_reminder_sent=None
                        )
                    )
                self.db.commit()

                print("✅ Test database created with:")
                print(f"- {len(plans)} plans")
                print(f"- {len(customers)} customers")
                print(f"- {len(customers)} subscriptions")
                logger.info(f"Test database created: {len(plans)} plans, {len(customers)} customers, {len(customers)} subscriptions")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to create test database: {str(e)}")
                raise
        self._with_db(_create)

    def run_validation_tests(self):
        """Run automated validation tests."""
        def _run():
            test_cases = self.generate_test_cases()
            
            print("\n🔍 Running Validation Tests")
            print("=" * 40)
            
            print("\nCustomer Validation:")
            for case in test_cases["customer_validation"]:
                result = validate_customer_data(case["name"], case["email"], case["router_id"])
                assert result == case["expected"], f"Failed: {case}"
                print(f"✓ {case['name'][:20] or 'Empty'}... Passed")
                logger.info(f"Customer validation test passed: {case['name']}")

            print("\nPlan Validation:")
            for case in test_cases["plan_validation"]:
                result = validate_plan_data(case["name"], case["speed"], case["price"])
                assert result == case["expected"], f"Failed: {case}"
                print(f"✓ {case['name'][:20] or 'Empty'}... Passed")
                logger.info(f"Plan validation test passed: {case['name']}")

            print("\nSubscription Validation:")
            for case in test_cases["subscription_validation"]:
                result = validate_subscription_input(case["customer_id"], case["plan_id"], case["duration"])
                assert result == case["expected"], f"Failed: {case}"
                print(f"✓ Customer ID {case['customer_id']}... Passed")
                logger.info(f"Subscription validation test passed: Customer ID {case['customer_id']}")

            print("\n✅ All validation tests passed!")
            logger.info("All validation tests passed")
        self._with_db(_run)

    def run_edge_case_tests(self):
        """Run edge case validation tests."""
        def _run():
            print("\n🔍 Running Edge Case Tests")
            print("=" * 40)
            edge_cases = self._edge_cases()
            
            for case in edge_cases:
                try:
                    if "phone" in case:
                        Customer().validate_phone("phone", case["phone"])
                        assert case["expected_valid"], f"Phone {case['phone']} should be invalid"
                        print(f"✓ Phone: {case['phone']}... Passed")
                        logger.info(f"Phone edge case test passed: {case['phone']}")
                    elif "email" in case:
                        Customer().validate_email("email", case["email"])
                        assert case["expected_valid"], f"Email {case['email']} should be invalid"
                        print(f"✓ Email: {case['email']}... Passed")
                        logger.info(f"Email edge case test passed: {case['email']}")
                    elif "price" in case:
                        errors = validate_plan_data("Test", "10 Mbps", case["price"])
                        assert (len(errors) == 0) == case["expected_valid"], f"Price {case['price']} failed: {errors}"
                        print(f"✓ Price: {case['price']}... Passed")
                        logger.info(f"Price edge case test passed: {case['price']}")
                    elif "start_date" in case:
                        Subscription().validate_start_date("start_date", case["start_date"])
                        assert case["expected_valid"], f"Start date {case['start_date']} should be invalid"
                        print(f"✓ Start date: {case['start_date']}... Passed")
                        logger.info(f"Start date edge case test passed: {case['start_date']}")
                except (InvalidPhoneError, InvalidEmailError, InvalidSubscriptionDateError) as e:
                    assert not case["expected_valid"], f"Validation for {case} should be valid but raised {str(e)}"
                    print(f"✓ {case}... Passed (expectedly invalid)")
                    logger.info(f"Edge case test passed (invalid): {case}")
                except Exception as e:
                    logger.error(f"Unexpected error in edge case test {case}: {str(e)}")
                    raise
            
            print("\n✅ All edge case tests passed!")
            logger.info("All edge case tests passed")
        self._with_db(_run)

    def test_crud_operations(self):
        """Test CRUD operations for customers, plans, and subscriptions."""
        def _test():
            print("\n🔍 Running CRUD Tests")
            print("=" * 40)

            self.db.query(Subscription).delete()
            self.db.query(Customer).delete()
            self.db.query(Plan).delete()
            self.db.commit()

            try:
                with patch("builtins.input", side_effect=["John Doe", "john.doe@example.com", "", "Nairobi", "1234567890"]):
                    create_customer(self.db)
                customers = self.db.query(Customer).order_by(Customer.name).all()
                assert len(customers) == 1, "Customer creation failed"
                print("✓ Customer creation: John Doe created")
                logger.info("Customer CRUD test: creation passed")

                with patch("builtins.input", side_effect=["1", "Jane Doe", "jane.doe@example.com", "", "Nairobi"]):
                    update_customer(self.db)
                customer = self.db.query(Customer).first()
                assert customer.name == "Jane Doe", "Customer update failed"
                print("✓ Customer update: Name changed to Jane Doe")
                logger.info("Customer CRUD test: update passed")

                with patch("builtins.input", side_effect=["1", "y"]):
                    delete_customer(self.db)
                assert self.db.query(Customer).count() == 0, "Customer deletion failed"
                print("✓ Customer deletion: Done")
                logger.info("Customer CRUD test: deletion passed")
            except Exception as e:
                logger.error(f"Customer CRUD test failed: {str(e)}")
                raise

            try:
                with patch("builtins.input", side_effect=["Basic Plan", "10 Mbps", "", "5000"]):
                    create_plan(self.db)
                plans = self.db.query(Plan).order_by(Plan.price).all()
                assert len(plans) == 1, "Plan creation failed"
                print("✓ Plan creation: Basic Plan created")
                logger.info("Plan CRUD test: creation passed")

                with patch("builtins.input", side_effect=["1", "", "", "", "6000"]):
                    update_plan(self.db)
                plan = self.db.query(Plan).first()
                assert float(plan.price) == 6000, "Plan update failed"
                print("✓ Plan update: Price updated to KES 6000")
                logger.info("Plan CRUD test: update passed")

                with patch("builtins.input", side_effect=["1", "y"]):
                    delete_plan(self.db)
                assert self.db.query(Plan).count() == 0, "Plan deletion failed"
                print("✓ Plan deletion: Done")
                logger.info("Plan CRUD test: deletion passed")
            except Exception as e:
                logger.error(f"Plan CRUD test failed: {str(e)}")
                raise

            try:
                self.db.add(Customer(name="Test User", email="test@example.com", router_id=1234567890))
                self.db.add(Plan(name="Basic", speed="10 Mbps", price=5000))
                self.db.commit()
                with patch("builtins.input", side_effect=["1", "1", "1244567890", "12"]):
                    create_subscription(self.db)
                subscriptions = self.db.query(Subscription).all()
                assert len(subscriptions) == 1, "Subscription creation failed"
                print("✓ Subscription creation: Created for customer ID 1")
                logger.info("Subscription CRUD test: creation passed")

                with patch("builtins.input", side_effect=["1", "", "", "suspended"]):
                    update_subscription(self.db)
                subscription = self.db.query(Subscription).first()
                assert subscription.status == "suspended", "Subscription update failed"
                print("✓ Subscription update: Status changed to suspended")
                logger.info("Subscription CRUD test: update passed")

                with patch("builtins.input", side_effect=["1", "y"]):
                    delete_subscription(self.db)
                subscription = self.db.query(Subscription).first()
                assert subscription.status == "terminated", "Subscription deletion failed"
                print("✓ Subscription deletion: Status set to terminated")
                logger.info("Subscription CRUD test: deletion passed")
            except Exception as e:
                logger.error(f"Subscription CRUD test failed: {str(e)}")
                raise

            print("\n✅ All CRUD tests passed!")
            logger.info("All CRUD tests passed")
        self._with_db(_test)

if __name__ == "__main__":
    logger.info("Starting test data generator")
    generator = TestDataGenerator()
    
    print("Internet Service Manager - Test Data Generator")
    print("1. Create Test Database")
    print("2. Run Validation Tests")
    print("3. Run Edge Case Tests")
    print("4. Run CRUD Tests")
    print("5. Generate Test Cases")
    
    choice = input("Select option (1-5): ").strip()
    
    if choice == "1":
        generator.create_test_database()
    elif choice == "2":
        generator.run_validation_tests()
    elif choice == "3":
        generator.run_edge_case_tests()
    elif choice == "4":
        generator.test_crud_operations()
    elif choice == "5":
        test_cases = generator.generate_test_cases()
        print("\nGenerated Test Cases:")
        print(test_cases)
        logger.info("Generated test cases")
    else:
        print("Invalid choice")
        logger.error("Invalid choice selected")