#!/usr/bin/env python3
"""
Example usage of the KYC Identity Verification System
"""
from pathlib import Path
from src.identity_extractor import IdentityExtractor
from src.output_formatter import OutputFormatter
from src.validator import IdentityValidator


def example_basic_usage():
    """Basic usage example."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Single Document Verification")
    print("="*60)

    # Initialize the extractor
    extractor = IdentityExtractor()

    # Verify a document (replace with actual image path)
    # result = extractor.verify_document("path/to/passport.jpg")

    # For demonstration, we'll show the expected flow
    print("""
    # Initialize extractor
    extractor = IdentityExtractor()

    # Verify document
    result = extractor.verify_document("passport.jpg")

    # Print human-readable result
    print(OutputFormatter.to_human_readable(result))

    # Access specific fields
    print(f"Name: {result.personal_info.full_name}")
    print(f"DOB: {result.personal_info.date_of_birth}")
    print(f"Document #: {result.document_info.document_number}")
    """)


def example_with_validation():
    """Example with validation."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Verification with Validation")
    print("="*60)

    print("""
    # Extract identity
    extractor = IdentityExtractor()
    result = extractor.verify_document("drivers_license.jpg")

    # Validate result
    validation_errors = IdentityValidator.validate_result(result)

    if validation_errors:
        print("Validation failed:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("Validation passed!")

    # Check specific validations
    is_valid_age, error = IdentityValidator.validate_age(
        result.personal_info.date_of_birth,
        min_age=21  # Custom minimum age
    )

    is_expired, error = IdentityValidator.validate_expiry(
        result.document_info.expiry_date
    )
    """)


def example_batch_processing():
    """Example of batch processing."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Processing Multiple Documents")
    print("="*60)

    print("""
    from pathlib import Path

    # Initialize extractor
    extractor = IdentityExtractor()

    # Process all images in directory
    documents_dir = Path("./documents")
    results = []

    for image_file in documents_dir.glob("*.jpg"):
        print(f"Processing {image_file.name}...")
        result = extractor.verify_document(image_file)
        results.append(result)

        # Save individual result
        output_path = Path("output") / f"{image_file.stem}_result.json"
        OutputFormatter.save_to_file(result, output_path, format="json")

    # Create summary report
    summary = OutputFormatter.create_summary_report(
        results,
        output_path="output/summary_report.txt"
    )
    print(summary)
    """)


def example_custom_model():
    """Example using different model."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Using Different Models")
    print("="*60)

    print("""
    # Use a smaller, faster model for simple documents
    extractor_fast = IdentityExtractor(
        model="accounts/fireworks/models/qwen2-vl-7b-instruct"
    )

    # Use the largest model for complex documents
    extractor_accurate = IdentityExtractor(
        model="accounts/fireworks/models/qwen2-vl-72b-instruct"
    )

    # Process simple ID
    result_simple = extractor_fast.verify_document("simple_id.jpg")

    # Process complex passport with multiple languages
    result_complex = extractor_accurate.verify_document("passport_complex.jpg")
    """)


def example_output_formats():
    """Example of different output formats."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Different Output Formats")
    print("="*60)

    print("""
    extractor = IdentityExtractor()
    result = extractor.verify_document("document.jpg")

    # JSON output
    json_str = OutputFormatter.to_json(result, indent=2)
    print(json_str)

    # Dictionary output
    data_dict = OutputFormatter.to_dict(result)

    # Human-readable output
    readable = OutputFormatter.to_human_readable(result)
    print(readable)

    # Save to files
    OutputFormatter.save_to_file(result, "output.json", format="json")
    OutputFormatter.save_to_file(result, "output.txt", format="txt")

    # Exclude raw extraction data from output
    json_clean = OutputFormatter.to_json(result, exclude_raw=True)
    """)


def example_error_handling():
    """Example with error handling."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Error Handling")
    print("="*60)

    print("""
    from pathlib import Path

    extractor = IdentityExtractor()

    try:
        # Verify document
        result = extractor.verify_document("document.jpg")

        # Check for extraction warnings
        if result.validation_flags:
            print("Warnings during extraction:")
            for flag in result.validation_flags:
                print(f"  - {flag}")

        # Validate result
        validation_errors = IdentityValidator.validate_result(result)

        if validation_errors:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            # Handle validation failures
            # Maybe request manual review
        else:
            # All good, proceed with KYC
            print("Document verified successfully")

    except FileNotFoundError as e:
        print(f"Document not found: {e}")
    except ValueError as e:
        print(f"Invalid document: {e}")
    except RuntimeError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    """)


def example_accessing_fields():
    """Example of accessing specific fields."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Accessing Extracted Fields")
    print("="*60)

    print("""
    result = extractor.verify_document("document.jpg")

    # Personal information
    full_name = result.personal_info.full_name
    first_name = result.personal_info.first_name
    last_name = result.personal_info.last_name
    dob = result.personal_info.date_of_birth
    nationality = result.personal_info.nationality

    # Document information
    doc_type = result.document_info.document_type  # 'passport', 'drivers_license', etc.
    doc_number = result.document_info.document_number
    expiry = result.document_info.expiry_date
    issuing_country = result.document_info.issuing_country

    # Type-specific information
    if result.document_info.document_type == "drivers_license":
        license_class = result.drivers_license_info.license_class
        address = result.drivers_license_info.address
        state = result.drivers_license_info.state_province

    elif result.document_info.document_type == "passport":
        passport_type = result.passport_info.passport_type
        place_of_birth = result.passport_info.place_of_birth

    # Validation flags
    warnings = result.validation_flags

    # Raw extraction (for debugging)
    raw_data = result.raw_extraction
    """)


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print(" KYC IDENTITY VERIFICATION SYSTEM - EXAMPLES")
    print("="*70)

    example_basic_usage()
    example_with_validation()
    example_batch_processing()
    example_custom_model()
    example_output_formats()
    example_error_handling()
    example_accessing_fields()

    print("\n" + "="*70)
    print(" For actual usage, replace example paths with real document images")
    print(" Make sure to set FIREWORKS_API_KEY in your .env file")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
