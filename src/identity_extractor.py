"""
Identity verification and data extraction using Fireworks AI.
"""
import json
from pathlib import Path
from typing import Union, Optional

from .fireworks_client import FireworksClient
from .document_processor import DocumentProcessor
from .models import (
    VerificationResult,
    PersonalInfo,
    DocumentInfo,
    DriversLicenseInfo,
    PassportInfo,
    ExtractionSchema
)


class IdentityExtractor:
    """Extracts and verifies identity information from documents."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct"
    ):
        """
        Initialize identity extractor.

        Args:
            api_key: Fireworks API key
            model: Vision-language model to use
        """
        self.client = FireworksClient(api_key=api_key, model=model)
        self.processor = DocumentProcessor()

    def _build_extraction_prompt(self, document_type: str = "unknown") -> str:
        """
        Build prompt for identity extraction.

        Args:
            document_type: Type of document being processed

        Returns:
            Extraction prompt
        """
        base_prompt = """You are an expert document analysis system for KYC (Know Your Customer) identity verification.

Analyze the provided identity document image and extract all relevant information with high accuracy.

IMPORTANT: Return your response EXACTLY as a JSON object within a markdown code block. Do not include any other text.
The JSON must follow this structure:
{
  "document_type": "passport" | "drivers_license" | "national_id",
  "full_name": "...",
  "first_name": "...",
  "last_name": "...",
  "middle_name": "...",
  "date_of_birth": "YYYY-MM-DD",
  "sex": "M" | "F" | "X",
  "nationality": "...",
  "document_number": "...",
  "issuing_country": "...",
  "issuing_authority": "...",
  "issue_date": "YYYY-MM-DD",
  "expiry_date": "YYYY-MM-DD",
  "license_class": "...",
  "address": "...",
  "state_province": "...",
  "place_of_birth": "...",
  "passport_type": "..."
}

Instructions:
1. Carefully examine all text, dates, numbers, and fields in the document
2. Extract information exactly as it appears - do not infer or guess
3. For dates, convert to YYYY-MM-DD format when possible
4. If a field is not visible or unclear, use null
5. Be thorough and accurate - this is for official identity verification purposes."""

        if document_type == "passport":
            base_prompt += """

This appears to be a PASSPORT. Pay special attention to:
- Passport number and type
- Machine Readable Zone (MRZ) at the bottom
- Place of birth
- Nationality
- Issue and expiry dates"""

        elif document_type == "drivers_license":
            base_prompt += """

This appears to be a DRIVER'S LICENSE. Pay special attention to:
- License number
- License class/category
- Residential address
- State or province of issue
- Any restrictions or endorsements
- Issue and expiry dates"""

        return base_prompt

    def _create_json_schema(self) -> dict:
        """
        Create JSON schema for structured extraction.

        Returns:
            JSON schema dict
        """
        return {
            "name": "identity_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "description": "Type of document: passport, drivers_license, or national_id"
                    },
                    "full_name": {
                        "type": "string",
                        "description": "Complete name as shown on the document"
                    },
                    "first_name": {
                        "type": ["string", "null"],
                        "description": "First or given name"
                    },
                    "last_name": {
                        "type": ["string", "null"],
                        "description": "Last name or surname"
                    },
                    "middle_name": {
                        "type": ["string", "null"],
                        "description": "Middle name if present"
                    },
                    "date_of_birth": {
                        "type": ["string", "null"],
                        "description": "Date of birth in YYYY-MM-DD format"
                    },
                    "sex": {
                        "type": ["string", "null"],
                        "description": "Sex or gender (M/F/X)"
                    },
                    "nationality": {
                        "type": ["string", "null"],
                        "description": "Nationality"
                    },
                    "document_number": {
                        "type": ["string", "null"],
                        "description": "Document number"
                    },
                    "issuing_country": {
                        "type": ["string", "null"],
                        "description": "Issuing country"
                    },
                    "issuing_authority": {
                        "type": ["string", "null"],
                        "description": "Issuing authority"
                    },
                    "issue_date": {
                        "type": ["string", "null"],
                        "description": "Issue date in YYYY-MM-DD format"
                    },
                    "expiry_date": {
                        "type": ["string", "null"],
                        "description": "Expiry date in YYYY-MM-DD format"
                    },
                    "license_class": {
                        "type": ["string", "null"],
                        "description": "Driver's license class (for driver's licenses only)"
                    },
                    "address": {
                        "type": ["string", "null"],
                        "description": "Address (for driver's licenses only)"
                    },
                    "state_province": {
                        "type": ["string", "null"],
                        "description": "State or province (for driver's licenses only)"
                    },
                    "place_of_birth": {
                        "type": ["string", "null"],
                        "description": "Place of birth (for passports only)"
                    },
                    "passport_type": {
                        "type": ["string", "null"],
                        "description": "Passport type (for passports only)"
                    }
                },
                "required": [
                    "document_type",
                    "full_name",
                    "first_name",
                    "last_name",
                    "middle_name",
                    "date_of_birth",
                    "sex",
                    "nationality",
                    "document_number",
                    "issuing_country",
                    "issuing_authority",
                    "issue_date",
                    "expiry_date",
                    "license_class",
                    "address",
                    "state_province",
                    "place_of_birth",
                    "passport_type"
                ],
                "additionalProperties": False
            }
        }

    def extract(
        self,
        image_path: Union[str, Path],
        optimize_image: bool = True
    ) -> VerificationResult:
        """
        Extract identity information from document image.

        Args:
            image_path: Path to document image
            optimize_image: Whether to optimize image before processing

        Returns:
            VerificationResult with extracted information
        """
        image_path = Path(image_path)

        # Prepare document
        processed_path, metadata = self.processor.prepare_document(
            image_path,
            optimize=optimize_image
        )

        # Build prompt based on detected type
        detected_type = metadata.get("detected_type", "unknown")
        prompt = self._build_extraction_prompt(detected_type)

        # Get JSON schema
        json_schema = self._create_json_schema()

        # Extract structured data
        try:
            extracted_data = self.client.extract_structured_data(
                image_path=processed_path,
                json_schema=json_schema,
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )
        except Exception as e:
            raise RuntimeError(f"Failed to extract data from document: {str(e)}")

        # Parse into models
        result = self._parse_extraction(extracted_data, metadata)

        return result

    def _parse_extraction(
        self,
        extracted_data: dict,
        metadata: dict
    ) -> VerificationResult:
        """
        Parse extracted data into structured result.

        Args:
            extracted_data: Raw extracted data from model
            metadata: Document metadata

        Returns:
            VerificationResult
        """
        # Extract personal info
        personal_info = PersonalInfo(
            full_name=extracted_data.get("full_name", ""),
            first_name=extracted_data.get("first_name"),
            middle_name=extracted_data.get("middle_name"),
            last_name=extracted_data.get("last_name"),
            date_of_birth=extracted_data.get("date_of_birth"),
            sex=extracted_data.get("sex"),
            nationality=extracted_data.get("nationality")
        )

        # Extract document info
        doc_type = extracted_data.get("document_type", "unknown")
        if doc_type not in ["passport", "drivers_license", "national_id", "unknown"]:
            doc_type = "unknown"

        document_info = DocumentInfo(
            document_type=doc_type,
            document_number=extracted_data.get("document_number"),
            issuing_country=extracted_data.get("issuing_country"),
            issuing_authority=extracted_data.get("issuing_authority"),
            issue_date=extracted_data.get("issue_date"),
            expiry_date=extracted_data.get("expiry_date")
        )

        # Extract type-specific info
        drivers_license_info = None
        passport_info = None

        if doc_type == "drivers_license":
            drivers_license_info = DriversLicenseInfo(
                license_class=extracted_data.get("license_class"),
                address=extracted_data.get("address"),
                state_province=extracted_data.get("state_province"),
                restrictions=None,
                endorsements=None
            )
        elif doc_type == "passport":
            passport_info = PassportInfo(
                passport_type=extracted_data.get("passport_type"),
                place_of_birth=extracted_data.get("place_of_birth"),
                machine_readable_zone=None
            )

        # Validation flags
        validation_flags = []

        if not personal_info.full_name:
            validation_flags.append("Missing full name")

        if not document_info.document_number:
            validation_flags.append("Missing document number")

        if not document_info.expiry_date:
            validation_flags.append("Missing expiry date")

        # Create result
        result = VerificationResult(
            personal_info=personal_info,
            document_info=document_info,
            drivers_license_info=drivers_license_info,
            passport_info=passport_info,
            confidence_score=None,
            validation_flags=validation_flags,
            raw_extraction=extracted_data
        )

        return result

    def verify_document(
        self,
        image_path: Union[str, Path],
        optimize_image: bool = True
    ) -> VerificationResult:
        """
        Verify and extract identity from document.

        This is an alias for extract() that emphasizes verification purpose.

        Args:
            image_path: Path to document image
            optimize_image: Whether to optimize image

        Returns:
            VerificationResult
        """
        return self.extract(image_path, optimize_image)
