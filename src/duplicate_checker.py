"""
Duplicate detection for identity verification results.
Uses image content hashing for reliable duplicate detection.
"""
import json
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Union
from io import BytesIO

from PIL import Image

from .models import VerificationResult


class DuplicateChecker:
    """Check for duplicate identity verifications using image content hashing."""

    def __init__(self, storage_path: str = "verification_history.json"):
        """
        Initialize duplicate checker.

        Args:
            storage_path: Path to store verification history
        """
        self.storage_path = Path(storage_path)
        self.history = self._load_history()

    def _load_history(self) -> List[dict]:
        """Load verification history from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        """Save verification history to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass  # Fail silently for storage issues

    def _compute_image_hash(self, image_path: Union[str, Path] = None, image_bytes: bytes = None) -> str:
        """
        Compute a hash of the image content for duplicate detection.
        Uses MD5 hash of the image bytes.

        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes (alternative to path)

        Returns:
            MD5 hash of image content
        """
        if image_bytes:
            return hashlib.md5(image_bytes).hexdigest()
        
        if image_path:
            image_path = Path(image_path)
            if image_path.exists():
                with open(image_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
        
        return ""

    def _compute_perceptual_hash(self, image_path: Union[str, Path] = None, image_bytes: bytes = None) -> str:
        """
        Compute a perceptual hash (pHash-like) for detecting visually similar images.
        This helps catch duplicates even if the image has been slightly modified.

        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes

        Returns:
            Perceptual hash string
        """
        try:
            if image_bytes:
                img = Image.open(BytesIO(image_bytes))
            elif image_path:
                img = Image.open(image_path)
            else:
                return ""

            # Convert to grayscale and resize to 8x8
            img = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
            
            # Get pixel values
            pixels = list(img.getdata())
            
            # Calculate average
            avg = sum(pixels) / len(pixels)
            
            # Generate hash based on whether each pixel is above or below average
            bits = ''.join(['1' if p > avg else '0' for p in pixels])
            
            # Convert to hex
            return hex(int(bits, 2))[2:].zfill(16)
            
        except Exception:
            return ""

    def _create_thumbnail(self, image_path: Union[str, Path] = None, image_bytes: bytes = None, max_size: int = 200) -> str:
        """
        Create a base64 encoded thumbnail of the image.

        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes
            max_size: Maximum dimension for thumbnail

        Returns:
            Base64 encoded JPEG thumbnail
        """
        try:
            if image_bytes:
                img = Image.open(BytesIO(image_bytes))
            elif image_path:
                img = Image.open(image_path)
            else:
                return ""

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img

            # Create thumbnail
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=75)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        except Exception:
            return ""

    def _generate_identity_key(self, result: VerificationResult) -> str:
        """
        Generate unique key for identity based on extracted data.

        Args:
            result: VerificationResult to generate key for

        Returns:
            Hash of identifying information
        """
        # Combine key identifying fields
        key_parts = [
            result.personal_info.full_name.lower().strip() if result.personal_info.full_name else "",
            result.personal_info.date_of_birth or "",
            result.document_info.document_number or "",
        ]

        # Create hash
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def check_duplicate_by_image(
        self,
        image_path: Union[str, Path] = None,
        image_bytes: bytes = None
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check if this exact image has been verified before.

        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes

        Returns:
            Tuple of (is_duplicate, previous_record)
        """
        # Compute content hash
        content_hash = self._compute_image_hash(image_path, image_bytes)
        if not content_hash:
            return False, None

        # Search history for matching hash
        for record in self.history:
            if record.get("image_hash") == content_hash:
                return True, record

        # Also check perceptual hash for visually similar images
        perceptual_hash = self._compute_perceptual_hash(image_path, image_bytes)
        if perceptual_hash:
            for record in self.history:
                stored_phash = record.get("perceptual_hash", "")
                if stored_phash and self._hamming_distance(perceptual_hash, stored_phash) < 5:
                    record_copy = record.copy()
                    record_copy["match_type"] = "similar_image"
                    return True, record_copy

        return False, None

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hex hashes."""
        try:
            # Convert to binary
            b1 = bin(int(hash1, 16))[2:].zfill(64)
            b2 = bin(int(hash2, 16))[2:].zfill(64)
            return sum(c1 != c2 for c1, c2 in zip(b1, b2))
        except:
            return 100  # Return high distance on error

    def check_duplicate(
        self,
        result: VerificationResult
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check if identity has been verified before based on extracted data.

        Args:
            result: VerificationResult to check

        Returns:
            Tuple of (is_duplicate, previous_record)
        """
        identity_key = self._generate_identity_key(result)

        # Search history for matching key
        for record in self.history:
            if record.get("identity_key") == identity_key:
                return True, record

        return False, None

    def find_similar(
        self,
        result: VerificationResult,
        threshold: float = 0.8
    ) -> List[dict]:
        """
        Find similar identities in history.

        Args:
            result: VerificationResult to compare
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar records
        """
        similar = []

        for record in self.history:
            similarity = self._calculate_similarity(result, record)
            if similarity >= threshold:
                record_with_score = record.copy()
                record_with_score["similarity_score"] = similarity
                similar.append(record_with_score)

        # Sort by similarity
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar

    def _calculate_similarity(
        self,
        result: VerificationResult,
        record: dict
    ) -> float:
        """
        Calculate similarity between result and historical record.

        Args:
            result: VerificationResult to compare
            record: Historical record dict

        Returns:
            Similarity score (0-1)
        """
        score = 0.0
        total_weight = 0.0

        # Name similarity (weight: 0.4)
        if result.personal_info.full_name and record.get("full_name"):
            if result.personal_info.full_name.lower() == record["full_name"].lower():
                score += 0.4
            elif self._fuzzy_match(result.personal_info.full_name, record["full_name"]):
                score += 0.2
            total_weight += 0.4

        # DOB match (weight: 0.3)
        if result.personal_info.date_of_birth and record.get("date_of_birth"):
            if result.personal_info.date_of_birth == record["date_of_birth"]:
                score += 0.3
            total_weight += 0.3

        # Document number match (weight: 0.3)
        if result.document_info.document_number and record.get("document_number"):
            if result.document_info.document_number == record["document_number"]:
                score += 0.3
            total_weight += 0.3

        # Normalize score
        if total_weight > 0:
            return score / total_weight
        return 0.0

    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Simple fuzzy string matching."""
        # Remove common variations
        s1 = str1.lower().replace(" ", "").replace("-", "").replace(".", "")
        s2 = str2.lower().replace(" ", "").replace("-", "").replace(".", "")

        # Check if one is substring of other
        return s1 in s2 or s2 in s1

    def add_verification(
        self,
        result: VerificationResult,
        image_path: Union[str, Path] = None,
        image_bytes: bytes = None,
        validation_errors: List[str] = None
    ):
        """
        Add a verification result to history.

        Args:
            result: VerificationResult object
            image_path: Path to image file
            image_bytes: Raw image bytes
            validation_errors: Optional list of validation errors/warnings from the UI
        """
        # Generate identity key
        identity_key = self._generate_identity_key(result)

        # Get image hash
        image_hash = self._compute_image_hash(image_path, image_bytes)

        # Get perceptual hash
        perceptual_hash = self._compute_perceptual_hash(image_path, image_bytes)

        # Create thumbnail
        thumbnail = self._create_thumbnail(image_path, image_bytes)

        # Create record
        record = {
            "id": identity_key,
            "image_hash": image_hash,
            "perceptual_hash": perceptual_hash,
            "thumbnail": thumbnail,
            "full_name": result.personal_info.full_name,
            "first_name": result.personal_info.first_name,
            "last_name": result.personal_info.last_name,
            "date_of_birth": result.personal_info.date_of_birth,
            "sex": result.personal_info.sex,
            "nationality": result.personal_info.nationality,
            "document_type": result.document_info.document_type,
            "document_number": result.document_info.document_number,
            "issuing_country": result.document_info.issuing_country,
            "expiry_date": result.document_info.expiry_date,
            "address": result.drivers_license_info.address if result.drivers_license_info else None,
            "verified_at": datetime.now().isoformat(),
            "validation_passed": len(result.validation_flags) == 0 and not validation_errors,
            "validation_flags": result.validation_flags,
            "validation_errors": validation_errors or []
        }

        # Check if this exact image already exists (update instead of duplicate)
        for i, existing in enumerate(self.history):
            if existing.get("image_hash") == image_hash:
                self.history[i] = record
                self._save_history()
                return

        # Check if identity already exists (update instead of duplicate)
        for i, existing in enumerate(self.history):
            if existing.get("identity_key") == identity_key:
                self.history[i] = record
                self._save_history()
                return

        # Add new record
        self.history.append(record)
        self._save_history()

    def get_all_verifications(self) -> List[dict]:
        """
        Get all verification records.

        Returns:
            List of all verification records
        """
        return sorted(self.history, key=lambda x: x.get("verified_at", ""), reverse=True)

    def get_verification_by_hash(self, image_hash: str) -> Optional[dict]:
        """
        Get verification record by image hash.

        Args:
            image_hash: MD5 hash of image content

        Returns:
            Matching verification record or None
        """
        for record in self.history:
            if record.get("image_hash") == image_hash:
                return record
        return None

    def delete_verification(self, image_hash: str) -> bool:
        """
        Delete a verification record by image hash.

        Args:
            image_hash: MD5 hash of image content

        Returns:
            True if deleted, False if not found
        """
        for i, record in enumerate(self.history):
            if record.get("image_hash") == image_hash:
                del self.history[i]
                self._save_history()
                return True
        return False

    def get_verification_count(self, result: VerificationResult) -> int:
        """
        Get number of times this identity has been verified.

        Args:
            result: VerificationResult to check

        Returns:
            Count of verifications
        """
        identity_key = self._generate_identity_key(result)
        count = 0

        for record in self.history:
            if record.get("identity_key") == identity_key:
                count += 1

        return count

    def clear_history(self):
        """Clear all verification history."""
        self.history = []
        self._save_history()

    def get_statistics(self) -> dict:
        """
        Get verification statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.history:
            return {
                "total_verifications": 0,
                "unique_identities": 0,
                "passed_validations": 0,
                "failed_validations": 0
            }

        unique_keys = set(r.get("identity_key") for r in self.history)

        return {
            "total_verifications": len(self.history),
            "unique_identities": len(unique_keys),
            "passed_validations": sum(1 for r in self.history if r.get("validation_passed")),
            "failed_validations": sum(1 for r in self.history if not r.get("validation_passed"))
        }

