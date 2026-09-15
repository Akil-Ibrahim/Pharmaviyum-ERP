"""
PharmaViyum CRM - Load Testing with Locust
=============================================================================
This file contains load testing scenarios for the PharmaViyum CRM API.

Usage:
    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Run headless
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 --run-time 5m

    # Generate HTML report
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 --run-time 5m --html=report.html
=============================================================================
"""

import random

from locust import HttpUser, between, task


class PharmaViyumUser(HttpUser):
    """
    Simulates a typical PharmaViyum CRM user
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """
        Called when a user starts (before any tasks are executed)
        Authenticates and stores the token
        """
        # Login to get JWT token
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"},
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        else:  # Fallback for testing without auth
            self.token = None
            self.headers = {"Content-Type": "application/json"}

    @task(3)
    def get_clients(self):
        """
        Task: Get list of clients
        Weight: 3 (executed 3x more often than weight-1 tasks)
        """
        self.client.get(
            "/api/v1/clients/", headers=self.headers, name="/api/v1/clients/"
        )

    @task(2)
    def get_products(self):
        """
        Task: Get list of products
        Weight: 2
        """
        self.client.get(
            "/api/v1/products/", headers=self.headers, name="/api/v1/products/"
        )

    @task(2)
    def get_sales(self):
        """
        Task: Get list of sales
        Weight: 2
        """
        self.client.get("/api/v1/sales/", headers=self.headers, name="/api/v1/sales/")

    @task(1)
    def create_client(self):
        """
        Task: Create a new client
        Weight: 1
        """
        client_data = {
            "first_name": f"Test{random.randint(1, 1000)}",
            "last_name": f"User{random.randint(1, 1000)}",
            "phone": f"+123456789{random.randint(10, 99)}",
            "email": f"test{random.randint(1, 1000)}@example.com",
        }

        self.client.post(
            "/api/v1/clients/",
            headers=self.headers,
            json=client_data,
            name="/api/v1/clients/ [POST]",
        )

    @task(1)
    def create_sale(self):
        """
        Task: Create a new sale
        Weight: 1
        """
        sale_data = {
            "client_id": random.randint(1, 100),
            "product_id": random.randint(1, 50),
            "quantity": random.randint(1, 5),
            "total_amount": round(random.uniform(10.0, 500.0), 2),
        }

        self.client.post(
            "/api/v1/sales/",
            headers=self.headers,
            json=sale_data,
            name="/api/v1/sales/ [POST]",
        )

    @task(1)
    def health_check(self):
        """
        Task: Health check endpoint
        Weight: 1
        """
        self.client.get("/health", name="/health")


class MortariumAIUser(HttpUser):
    """
    Simulates AI assistant user (Mortarium AI)
    """

    wait_time = between(3, 7)  # Longer wait time for AI queries

    def on_start(self):
        """Authenticate for AI endpoints"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "ai_user", "password": "ai_password"},
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        else:
            self.token = None
            self.headers = {"Content-Type": "application/json"}

    @task(3)
    def ask_ai_question(self):
        """
        Task: Ask a question to Mortarium AI
        Weight: 3
        """
        questions = [
            "What are the top selling products this month?",
            "Show me sales statistics for last week",
            "Which clients made the most purchases?",
            "What is the total revenue for today?",
            "Show me low stock products",
        ]

        query_data = {"question": random.choice(questions), "context": "pharmacy_sales"}

        self.client.post(
            "/api/v1/ai/query",
            headers=self.headers,
            json=query_data,
            name="/api/v1/ai/query [POST]",
        )
