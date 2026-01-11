#!/usr/bin/env python3
"""
KYC Identity Verification System - Main CLI
"""
import argparse
import sys
from pathlib import Path

from src.identity_extractor import IdentityExtractor
from src.output_formatter import OutputFormatter
from src.validator import IdentityValidator


def verify_single_document(
    image_path: str,
    output_dir: str = "output",
    model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
    verbose: bool = True
):
    """
    Verify a single identity document.

    Args:
        image_path: Path to document image
        output_dir: Directory for output files
        model: Fireworks AI model to use
        verbose: Print detailed output
    """
    try:
        if verbose:
            print(f"\n🔍 Processing document: {image_path}")
            print(f"📊 Using model: {model}\n")

        # Initialize extractor
        extractor = IdentityExtractor(model=model)

        # Extract identity information
        result = extractor.verify_document(image_path)

        # Print human-readable result
        if verbose:
            print(OutputFormatter.to_human_readable(result))

        # Save results
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        input_name = Path(image_path).stem

        # Save JSON
        json_path = output_dir_path / f"{input_name}_result.json"
        OutputFormatter.save_to_file(result, json_path, format="json")
        if verbose:
            print(f"\n💾 JSON result saved to: {json_path}")

        # Save human-readable
        txt_path = output_dir_path / f"{input_name}_result.txt"
        OutputFormatter.save_to_file(result, txt_path, format="txt")
        if verbose:
            print(f"💾 Text result saved to: {txt_path}")

        # Validation summary
        validation_errors = IdentityValidator.validate_result(result)
        if validation_errors:
            print("\n⚠️  Validation Issues:")
            for error in validation_errors:
                print(f"   ✗ {error}")
            return False
        else:
            if verbose:
                print("\n✅ Verification successful!")
            return True

    except Exception as e:
        print(f"\n❌ Error processing document: {str(e)}", file=sys.stderr)
        return False


def verify_batch_documents(
    input_dir: str,
    output_dir: str = "output",
    model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
    pattern: str = "*.*"
):
    """
    Verify multiple identity documents.

    Args:
        input_dir: Directory containing document images
        output_dir: Directory for output files
        model: Fireworks AI model to use
        pattern: File pattern to match
    """
    input_path = Path(input_dir)

    if not input_path.is_dir():
        print(f"❌ Error: {input_dir} is not a directory", file=sys.stderr)
        return False

    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"}
    image_files = [
        f for f in input_path.glob(pattern)
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        print(f"❌ No image files found in {input_dir}", file=sys.stderr)
        return False

    print(f"\n📁 Found {len(image_files)} documents to process")
    print(f"📊 Using model: {model}\n")

    # Process each document
    extractor = IdentityExtractor(model=model)
    results = []
    success_count = 0

    for i, image_file in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing: {image_file.name}...")

        try:
            result = extractor.verify_document(image_file)
            results.append(result)

            # Quick validation
            validation_errors = IdentityValidator.validate_result(result)
            if not validation_errors and not result.validation_flags:
                print(f"  ✓ {result.personal_info.full_name} - OK")
                success_count += 1
            else:
                print(f"  ⚠️  {result.personal_info.full_name} - Issues detected")

            # Save individual result
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            json_path = output_dir_path / f"{image_file.stem}_result.json"
            OutputFormatter.save_to_file(result, json_path, format="json")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

    # Create summary report
    if results:
        print("\n" + "=" * 80)
        print("📋 GENERATING SUMMARY REPORT")
        print("=" * 80)

        output_dir_path = Path(output_dir)
        summary_path = output_dir_path / "summary_report.txt"

        report = OutputFormatter.create_summary_report(results, summary_path)
        print(report)
        print(f"\n💾 Summary report saved to: {summary_path}")

        print(f"\n✅ Batch processing complete: {success_count}/{len(results)} successful")
        return True
    else:
        print("\n❌ No documents were successfully processed")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KYC Identity Verification using Fireworks AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify single document
  python main.py --image passport.jpg

  # Verify with specific model
  python main.py --image license.png --model accounts/fireworks/models/qwen2p5-vl-32b-instruct

  # Batch process directory
  python main.py --batch-dir ./documents --output ./results

  # Quiet mode (minimal output)
  python main.py --image passport.jpg --quiet
        """
    )

    parser.add_argument(
        "--image",
        type=str,
        help="Path to single document image to verify"
    )

    parser.add_argument(
        "--batch-dir",
        type=str,
        help="Directory containing multiple documents to verify"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        help="Fireworks AI model to use (default: qwen2p5-vl-32b-instruct)"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.*",
        help="File pattern for batch processing (default: *.*)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode - minimal output"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.image and not args.batch_dir:
        parser.print_help()
        print("\n❌ Error: Either --image or --batch-dir must be specified", file=sys.stderr)
        sys.exit(1)

    if args.image and args.batch_dir:
        print("❌ Error: Cannot specify both --image and --batch-dir", file=sys.stderr)
        sys.exit(1)

    # Process
    if args.image:
        success = verify_single_document(
            args.image,
            args.output,
            args.model,
            verbose=not args.quiet
        )
    else:
        success = verify_batch_documents(
            args.batch_dir,
            args.output,
            args.model,
            args.pattern
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
