"""
Output formatting for verification results.
"""
import json
from pathlib import Path
from typing import Union, Optional
from datetime import datetime

from .models import VerificationResult
from .validator import IdentityValidator


class OutputFormatter:
    """Formats verification results for output."""

    @staticmethod
    def to_json(
        result: VerificationResult,
        indent: int = 2,
        exclude_raw: bool = False
    ) -> str:
        """
        Format result as JSON string.

        Args:
            result: VerificationResult to format
            indent: JSON indentation
            exclude_raw: Exclude raw extraction data

        Returns:
            JSON string
        """
        data = result.model_dump(exclude_none=False)

        if exclude_raw:
            data.pop("raw_extraction", None)

        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def to_dict(
        result: VerificationResult,
        exclude_raw: bool = False
    ) -> dict:
        """
        Convert result to dictionary.

        Args:
            result: VerificationResult to convert
            exclude_raw: Exclude raw extraction data

        Returns:
            Dictionary representation
        """
        data = result.model_dump(exclude_none=False)

        if exclude_raw:
            data.pop("raw_extraction", None)

        return data

    @staticmethod
    def to_human_readable(result: VerificationResult) -> str:
        """
        Format result as human-readable text.

        Args:
            result: VerificationResult to format

        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("IDENTITY VERIFICATION RESULT")
        lines.append("=" * 60)

        # Document Info
        lines.append("\n📄 DOCUMENT INFORMATION")
        lines.append("-" * 60)
        lines.append(f"Document Type:       {result.document_info.document_type.replace('_', ' ').title()}")
        lines.append(f"Document Number:     {result.document_info.document_number or 'N/A'}")
        lines.append(f"Issuing Country:     {result.document_info.issuing_country or 'N/A'}")
        lines.append(f"Issuing Authority:   {result.document_info.issuing_authority or 'N/A'}")
        lines.append(f"Issue Date:          {result.document_info.issue_date or 'N/A'}")
        lines.append(f"Expiry Date:         {result.document_info.expiry_date or 'N/A'}")

        # Personal Info
        lines.append("\n👤 PERSONAL INFORMATION")
        lines.append("-" * 60)
        lines.append(f"Full Name:           {result.personal_info.full_name}")
        if result.personal_info.first_name or result.personal_info.last_name:
            lines.append(f"First Name:          {result.personal_info.first_name or 'N/A'}")
            if result.personal_info.middle_name:
                lines.append(f"Middle Name:         {result.personal_info.middle_name}")
            lines.append(f"Last Name:           {result.personal_info.last_name or 'N/A'}")
        lines.append(f"Date of Birth:       {result.personal_info.date_of_birth or 'N/A'}")
        lines.append(f"Sex:                 {result.personal_info.sex or 'N/A'}")
        lines.append(f"Nationality:         {result.personal_info.nationality or 'N/A'}")

        # Driver's License Info
        if result.drivers_license_info:
            lines.append("\n🚗 DRIVER'S LICENSE DETAILS")
            lines.append("-" * 60)
            lines.append(f"License Class:       {result.drivers_license_info.license_class or 'N/A'}")
            lines.append(f"Address:             {result.drivers_license_info.address or 'N/A'}")
            lines.append(f"State/Province:      {result.drivers_license_info.state_province or 'N/A'}")
            if result.drivers_license_info.restrictions:
                lines.append(f"Restrictions:        {result.drivers_license_info.restrictions}")
            if result.drivers_license_info.endorsements:
                lines.append(f"Endorsements:        {result.drivers_license_info.endorsements}")

        # Passport Info
        if result.passport_info:
            lines.append("\n✈️  PASSPORT DETAILS")
            lines.append("-" * 60)
            lines.append(f"Passport Type:       {result.passport_info.passport_type or 'N/A'}")
            lines.append(f"Place of Birth:      {result.passport_info.place_of_birth or 'N/A'}")

        # Validation
        lines.append("\n✓ VALIDATION")
        lines.append("-" * 60)

        validation_errors = IdentityValidator.validate_result(result)

        if not validation_errors and not result.validation_flags:
            lines.append("Status:              ✓ PASSED - All validations successful")
        else:
            lines.append("Status:              ✗ ISSUES DETECTED")

            if result.validation_flags:
                lines.append("\nExtraction Warnings:")
                for flag in result.validation_flags:
                    lines.append(f"  ⚠️  {flag}")

            if validation_errors:
                lines.append("\nValidation Errors:")
                for error in validation_errors:
                    lines.append(f"  ✗ {error}")

        if result.confidence_score is not None:
            lines.append(f"\nConfidence Score:    {result.confidence_score:.2%}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    @staticmethod
    def save_to_file(
        result: VerificationResult,
        output_path: Union[str, Path],
        format: str = "json",
        exclude_raw: bool = False
    ) -> Path:
        """
        Save result to file.

        Args:
            result: VerificationResult to save
            output_path: Output file path
            format: Output format ('json' or 'txt')
            exclude_raw: Exclude raw extraction data (for JSON)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = OutputFormatter.to_json(result, exclude_raw=exclude_raw)
        elif format == "txt":
            content = OutputFormatter.to_human_readable(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    @staticmethod
    def create_summary_report(
        results: list[VerificationResult],
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """
        Create summary report for multiple verification results.

        Args:
            results: List of VerificationResults
            output_path: Optional path to save report

        Returns:
            Summary report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("BATCH IDENTITY VERIFICATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Documents Processed: {len(results)}")

        # Statistics
        doc_types = {}
        passed = 0
        failed = 0

        for result in results:
            doc_type = result.document_info.document_type
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            validation_errors = IdentityValidator.validate_result(result)
            if not validation_errors and not result.validation_flags:
                passed += 1
            else:
                failed += 1

        lines.append("\n📊 STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Passed:                {passed} ({passed/len(results)*100:.1f}%)")
        lines.append(f"Failed/Warnings:       {failed} ({failed/len(results)*100:.1f}%)")

        lines.append("\n📄 DOCUMENT TYPES")
        lines.append("-" * 80)
        for doc_type, count in sorted(doc_types.items()):
            lines.append(f"{doc_type.replace('_', ' ').title():<20} {count} ({count/len(results)*100:.1f}%)")

        # Individual results
        lines.append("\n" + "=" * 80)
        lines.append("INDIVIDUAL RESULTS")
        lines.append("=" * 80)

        for i, result in enumerate(results, 1):
            lines.append(f"\n[{i}] {result.personal_info.full_name}")
            lines.append(f"    Document: {result.document_info.document_type.replace('_', ' ').title()}")
            lines.append(f"    Number: {result.document_info.document_number or 'N/A'}")

            validation_errors = IdentityValidator.validate_result(result)
            if not validation_errors and not result.validation_flags:
                lines.append("    Status: ✓ PASSED")
            else:
                lines.append("    Status: ✗ ISSUES")
                if result.validation_flags:
                    for flag in result.validation_flags:
                        lines.append(f"      ⚠️  {flag}")
                if validation_errors:
                    for error in validation_errors:
                        lines.append(f"      ✗ {error}")

        lines.append("\n" + "=" * 80)

        report = "\n".join(lines)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report
