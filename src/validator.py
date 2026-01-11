"""
Validation utilities for identity verification results.
"""
from datetime import datetime, date
from typing import List, Optional
import re

from .models import VerificationResult, PersonalInfo, DocumentInfo


class IdentityValidator:
    """Validates extracted identity information."""

    @staticmethod
    def validate_date_format(date_str: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validate date string is in YYYY-MM-DD format and is a valid date.

        Args:
            date_str: Date string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return True, None

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, None
        except ValueError:
            return False, f"Invalid date format: {date_str} (expected YYYY-MM-DD)"

    @staticmethod
    def validate_expiry(expiry_date: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validate document has not expired.

        Args:
            expiry_date: Expiry date string in YYYY-MM-DD format

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expiry_date:
            return True, None

        # First validate format
        is_valid_format, error = IdentityValidator.validate_date_format(expiry_date)
        if not is_valid_format:
            return False, error

        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            today = date.today()

            if expiry < today:
                return False, f"Document expired on {expiry_date}"

            return True, None
        except ValueError as e:
            return False, f"Invalid expiry date: {str(e)}"

    @staticmethod
    def validate_age(date_of_birth: Optional[str], min_age: int = 18) -> tuple[bool, Optional[str]]:
        """
        Validate person meets minimum age requirement.

        Args:
            date_of_birth: Date of birth in YYYY-MM-DD format
            min_age: Minimum age requirement

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_of_birth:
            return True, None

        # First validate format
        is_valid_format, error = IdentityValidator.validate_date_format(date_of_birth)
        if not is_valid_format:
            return False, error

        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            today = date.today()

            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age < min_age:
                return False, f"Age {age} below minimum requirement of {min_age}"

            if age > 120:
                return False, f"Invalid age: {age} (date of birth may be incorrect)"

            return True, None
        except ValueError as e:
            return False, f"Invalid date of birth: {str(e)}"

    @staticmethod
    def validate_name(name: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validate name is present and reasonable.

        Args:
            name: Name string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Name is required"

        # Check for minimum length
        if len(name.strip()) < 2:
            return False, "Name too short"

        # Check contains at least some letters
        if not re.search(r'[A-Za-z]', name):
            return False, "Name must contain letters"

        return True, None

    @staticmethod
    def validate_document_number(
        document_number: Optional[str],
        document_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate document number is present and has reasonable format.

        Args:
            document_number: Document number to validate
            document_type: Type of document

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not document_number or not document_number.strip():
            return False, "Document number is required"

        # Basic validation - should be alphanumeric
        if not re.match(r'^[A-Z0-9\-\s]+$', document_number.strip(), re.IGNORECASE):
            return False, "Document number contains invalid characters"

        # Length check
        doc_num = document_number.strip().replace(" ", "").replace("-", "")
        if len(doc_num) < 4:
            return False, "Document number too short"

        if len(doc_num) > 20:
            return False, "Document number too long"

        return True, None

    @staticmethod
    def validate_result(
        result: VerificationResult,
        min_age: int = 18,
        check_expiry: bool = True
    ) -> List[str]:
        """
        Comprehensive validation of verification result.

        Args:
            result: VerificationResult to validate
            min_age: Minimum age requirement
            check_expiry: Whether to check document expiry

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate personal info
        is_valid, error = IdentityValidator.validate_name(result.personal_info.full_name)
        if not is_valid:
            errors.append(f"Full name: {error}")

        if result.personal_info.date_of_birth:
            is_valid, error = IdentityValidator.validate_date_format(
                result.personal_info.date_of_birth
            )
            if not is_valid:
                errors.append(f"Date of birth: {error}")
            else:
                is_valid, error = IdentityValidator.validate_age(
                    result.personal_info.date_of_birth,
                    min_age
                )
                if not is_valid:
                    errors.append(f"Age: {error}")

        # Validate document info
        if result.document_info.document_number:
            is_valid, error = IdentityValidator.validate_document_number(
                result.document_info.document_number,
                result.document_info.document_type
            )
            if not is_valid:
                errors.append(f"Document number: {error}")

        if result.document_info.issue_date:
            is_valid, error = IdentityValidator.validate_date_format(
                result.document_info.issue_date
            )
            if not is_valid:
                errors.append(f"Issue date: {error}")

        if result.document_info.expiry_date:
            is_valid, error = IdentityValidator.validate_date_format(
                result.document_info.expiry_date
            )
            if not is_valid:
                errors.append(f"Expiry date: {error}")
            elif check_expiry:
                is_valid, error = IdentityValidator.validate_expiry(
                    result.document_info.expiry_date
                )
                if not is_valid:
                    errors.append(f"Document expiry: {error}")

        # Check issue date is before expiry date
        if result.document_info.issue_date and result.document_info.expiry_date:
            try:
                issue = datetime.strptime(result.document_info.issue_date, "%Y-%m-%d").date()
                expiry = datetime.strptime(result.document_info.expiry_date, "%Y-%m-%d").date()
                if issue >= expiry:
                    errors.append("Issue date must be before expiry date")
            except ValueError:
                pass  # Already reported format errors above

        return errors

    @staticmethod
    def is_valid(result: VerificationResult, **kwargs) -> bool:
        """
        Check if verification result is valid.

        Args:
            result: VerificationResult to validate
            **kwargs: Additional arguments to pass to validate_result

        Returns:
            True if valid, False otherwise
        """
        errors = IdentityValidator.validate_result(result, **kwargs)
        return len(errors) == 0
