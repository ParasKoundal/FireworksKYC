"""
Data models for KYC identity verification.
"""
from typing import Optional, Literal
from datetime import date
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    """Personal information extracted from identity documents."""
    full_name: str = Field(description="Complete name as appears on document")
    first_name: Optional[str] = Field(None, description="First/given name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    last_name: Optional[str] = Field(None, description="Last/family/surname")
    date_of_birth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    sex: Optional[str] = Field(None, description="Sex/Gender (M/F/X)")
    nationality: Optional[str] = Field(None, description="Nationality or citizenship")


class DocumentInfo(BaseModel):
    """Document-specific information."""
    document_type: Literal["passport", "drivers_license", "national_id", "unknown"] = Field(
        description="Type of identity document"
    )
    document_number: Optional[str] = Field(None, description="Unique document number")
    issuing_country: Optional[str] = Field(None, description="Country that issued the document")
    issuing_authority: Optional[str] = Field(None, description="Authority that issued the document")
    issue_date: Optional[str] = Field(None, description="Date of issue in YYYY-MM-DD format")
    expiry_date: Optional[str] = Field(None, description="Expiration date in YYYY-MM-DD format")


class DriversLicenseInfo(BaseModel):
    """Additional information specific to driver's licenses."""
    license_class: Optional[str] = Field(None, description="License class/category")
    address: Optional[str] = Field(None, description="Residential address")
    state_province: Optional[str] = Field(None, description="State or province of issue")
    restrictions: Optional[str] = Field(None, description="Any driving restrictions")
    endorsements: Optional[str] = Field(None, description="License endorsements")


class PassportInfo(BaseModel):
    """Additional information specific to passports."""
    passport_type: Optional[str] = Field(None, description="Type of passport (regular, official, diplomatic)")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    machine_readable_zone: Optional[str] = Field(None, description="MRZ text if visible")


class VerificationResult(BaseModel):
    """Complete verification result for an identity document."""
    personal_info: PersonalInfo
    document_info: DocumentInfo
    drivers_license_info: Optional[DriversLicenseInfo] = None
    passport_info: Optional[PassportInfo] = None
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall confidence in extraction (0-1)"
    )
    validation_flags: list[str] = Field(
        default_factory=list,
        description="List of validation warnings or issues"
    )
    raw_extraction: Optional[dict] = Field(
        None,
        description="Raw extracted data from the model"
    )


class ExtractionSchema(BaseModel):
    """Schema for structured extraction from identity documents."""
    document_type: str = Field(description="Type of document: passport, drivers_license, or national_id")
    full_name: str = Field(description="Complete name as shown on the document")
    first_name: Optional[str] = Field(None, description="First or given name")
    last_name: Optional[str] = Field(None, description="Last name or surname")
    middle_name: Optional[str] = Field(None, description="Middle name if present")
    date_of_birth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    sex: Optional[str] = Field(None, description="Sex or gender (M/F/X)")
    nationality: Optional[str] = Field(None, description="Nationality")
    document_number: Optional[str] = Field(None, description="Document number")
    issuing_country: Optional[str] = Field(None, description="Issuing country")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority")
    issue_date: Optional[str] = Field(None, description="Issue date in YYYY-MM-DD format")
    expiry_date: Optional[str] = Field(None, description="Expiry date in YYYY-MM-DD format")

    # Driver's license specific
    license_class: Optional[str] = Field(None, description="Driver's license class")
    address: Optional[str] = Field(None, description="Address on driver's license")
    state_province: Optional[str] = Field(None, description="State or province")

    # Passport specific
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    passport_type: Optional[str] = Field(None, description="Passport type")
