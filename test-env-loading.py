#!/usr/bin/env python3
"""
Test script to verify environment variable loading priority.
Run this from your project directory to see which .env is being used.
"""

import sys
from pathlib import Path

# Add toolkit to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config

def test_env_loading():
    """Test and display environment loading information"""
    print("=" * 60)
    print("🔍 API Toolkit Environment Loading Test")
    print("=" * 60)

    # Show where env was loaded from
    env_source = Config.get_env_source()
    if env_source:
        print(f"\n✅ Environment loaded from:")
        print(f"   {env_source}")
    else:
        print("\n⚠️  No .env file found in any location!")
        print("\nSearched locations (in priority order):")
        print(f"   1. {Path.cwd() / '.env'} (project root)")
        print(f"   2. {Path(__file__).parent / '.env'} (toolkit root)")
        print(f"   3. {Path.home() / '.api-toolkit.env'} (home directory)")

    # Check which services have credentials
    print("\n" + "=" * 60)
    print("📋 Service Configuration Status")
    print("=" * 60)

    services = Config.list_services()
    for service in services:
        print(f"\n{service.upper()}:")
        status = Config.check_environment(service)

        if 'error' in status:
            print(f"  ⚠️  {status['error']}")
            continue

        for var, is_set in status.items():
            icon = "✅" if is_set else "❌"
            print(f"  {icon} {var}: {'SET' if is_set else 'NOT SET'}")

    print("\n" + "=" * 60)
    print("💡 Recommendation")
    print("=" * 60)
    print("\nFor best results:")
    print("  1. Keep ONE .env file in your project root")
    print("  2. Add api-toolkit/ to your .gitignore")
    print("  3. Use Config.get_env_source() to debug loading issues")
    print("\n")

if __name__ == "__main__":
    test_env_loading()
