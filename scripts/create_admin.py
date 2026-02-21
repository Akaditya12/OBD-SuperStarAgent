#!/usr/bin/env python3
"""
Utility script to create the initial admin user in Supabase.
Run this from the project root:
$ python3 scripts/create_admin.py
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import backend modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from getpass import getpass
import bcrypt
from backend.database import supabase

def main():
    if not supabase:
        print("❌ Error: Supabase client is not initialized.")
        print("Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in backend/config.py or .env")
        sys.exit(1)

    print("=== Create Admin User ===")
    username = input("Enter admin username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    email = input("Enter admin email: ").strip()
    if not email:
        print("Email cannot be empty.")
        sys.exit(1)

    team = input("Enter admin team name (e.g., 'Core'): ").strip()
    if not team:
        team = "Core"

    password = getpass("Enter admin password: ")
    confirm = getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match!")
        sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        sys.exit(1)

    # Hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    user_data = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": "admin",
        "team": team,
        "is_active": True
    }

    try:
        response = supabase.table("users").insert(user_data).execute()
        if response.data:
            print(f"\n✅ Successfully created admin user: {username} ({email})")
            print(f"Role: admin | Team: {team}")
            print("\nYou can now login to the application using these credentials.")
        else:
            print(f"\n❌ Failed to create user (No data returned)")
    except Exception as e:
        print(f"\n❌ Error creating user in Supabase:")
        print(e)
        if "duplicate key value violates unique constraint" in str(e):
            print("A user with this username or email already exists.")

if __name__ == "__main__":
    main()
