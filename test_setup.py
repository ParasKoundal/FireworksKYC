#!/usr/bin/env python3
"""
Test script to validate setup and environment configuration.
"""
import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.9+."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False


def check_dependencies():
    """Check all required packages are installed."""
    print("\nChecking dependencies...")
    required = ["requests", "dotenv", "PIL", "pydantic"]
    all_installed = True

    for package in required:
        try:
            if package == "dotenv":
                import dotenv
            elif package == "PIL":
                import PIL
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (not installed)")
            all_installed = False

    return all_installed


def check_env_file():
    """Check .env file exists and has API key."""
    print("\nChecking .env configuration...")

    env_path = Path(".env")
    if not env_path.exists():
        print("  ✗ .env file not found")
        print("    Run: cp .env.example .env")
        return False

    print("  ✓ .env file exists")

    # Try to load
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        print("  ✗ FIREWORKS_API_KEY not set in .env")
        print("    Add your API key to .env file")
        return False

    if api_key == "your_api_key_here":
        print("  ✗ FIREWORKS_API_KEY still has placeholder value")
        print("    Replace with your actual API key")
        return False

    print(f"  ✓ FIREWORKS_API_KEY configured ({api_key[:6]}...)")
    return True


def check_src_modules():
    """Check all source modules are present."""
    print("\nChecking source modules...")
    modules = [
        "src/__init__.py",
        "src/models.py",
        "src/fireworks_client.py",
        "src/document_processor.py",
        "src/identity_extractor.py",
        "src/validator.py",
        "src/output_formatter.py"
    ]

    all_present = True
    for module in modules:
        if Path(module).exists():
            print(f"  ✓ {module}")
        else:
            print(f"  ✗ {module} (missing)")
            all_present = False

    return all_present


def check_imports():
    """Check that modules can be imported."""
    print("\nChecking module imports...")

    try:
        from src.models import VerificationResult, PersonalInfo, DocumentInfo
        print("  ✓ src.models")
    except Exception as e:
        print(f"  ✗ src.models: {e}")
        return False

    try:
        from src.fireworks_client import FireworksClient
        print("  ✓ src.fireworks_client")
    except Exception as e:
        print(f"  ✗ src.fireworks_client: {e}")
        return False

    try:
        from src.document_processor import DocumentProcessor
        print("  ✓ src.document_processor")
    except Exception as e:
        print(f"  ✗ src.document_processor: {e}")
        return False

    try:
        from src.identity_extractor import IdentityExtractor
        print("  ✓ src.identity_extractor")
    except Exception as e:
        print(f"  ✗ src.identity_extractor: {e}")
        return False

    try:
        from src.validator import IdentityValidator
        print("  ✓ src.validator")
    except Exception as e:
        print(f"  ✗ src.validator: {e}")
        return False

    try:
        from src.output_formatter import OutputFormatter
        print("  ✓ src.output_formatter")
    except Exception as e:
        print(f"  ✗ src.output_formatter: {e}")
        return False

    return True


def check_api_connection():
    """Test connection to Fireworks API."""
    print("\nChecking Fireworks API connection...")

    try:
        from src.fireworks_client import FireworksClient
        from dotenv import load_dotenv
        load_dotenv()

        client = FireworksClient()
        print("  ✓ Client initialized")
        print("  ℹ To test actual API call, run verification on a real document")
        return True

    except Exception as e:
        print(f"  ✗ Failed to initialize client: {e}")
        return False


def create_test_output_dir():
    """Create output directory if it doesn't exist."""
    print("\nChecking output directory...")

    output_dir = Path("output")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print("  ✓ Created output/ directory")
    else:
        print("  ✓ output/ directory exists")

    return True


def main():
    """Run all checks."""
    print("="*60)
    print("KYC Identity Verification System - Setup Validation")
    print("="*60)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Source Modules", check_src_modules),
        ("Module Imports", check_imports),
        ("Output Directory", create_test_output_dir),
        ("API Connection", check_api_connection),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n  ✗ Unexpected error in {name}: {e}")
            results[name] = False

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    print("="*60)
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("\n✅ All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Review QUICKSTART.md for usage examples")
        print("  2. Run: python example.py (to see code examples)")
        print("  3. Run: python main.py --image your_document.jpg")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Create .env file: cp .env.example .env")
        print("  - Add API key to .env file")
        return 1


if __name__ == "__main__":
    sys.exit(main())
