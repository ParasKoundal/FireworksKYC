"""
Document processing utilities for identity verification.
"""
import json
from pathlib import Path
from typing import Union, Optional

from PIL import Image


class DocumentProcessor:
    """Handles document image preprocessing and optimization."""

    # Fireworks AI image constraints
    MAX_IMAGE_SIZE_MB = 10
    MAX_DIMENSION = 4096
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png"}

    @staticmethod
    def validate_image(image_path: Union[str, Path]) -> tuple[bool, Optional[str]]:
        """
        Validate image file meets requirements.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (is_valid, error_message)
        """
        image_path = Path(image_path)

        # Check file exists
        if not image_path.exists():
            return False, f"File not found: {image_path}"

        # Check file extension
        if image_path.suffix.lower() not in DocumentProcessor.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {image_path.suffix}. Supported: {DocumentProcessor.SUPPORTED_FORMATS}"

        # Check file size
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > DocumentProcessor.MAX_IMAGE_SIZE_MB:
            return False, f"File too large: {file_size_mb:.2f}MB (max {DocumentProcessor.MAX_IMAGE_SIZE_MB}MB)"

        # Check image dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width > DocumentProcessor.MAX_DIMENSION or height > DocumentProcessor.MAX_DIMENSION:
                    return False, f"Image dimensions too large: {width}x{height} (max {DocumentProcessor.MAX_DIMENSION}px)"
        except Exception as e:
            return False, f"Failed to open image: {str(e)}"

        return True, None

    @staticmethod
    def optimize_image(
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        max_dimension: int = 2048,
        quality: int = 85
    ) -> Path:
        """
        Optimize image for API processing.

        Args:
            image_path: Path to input image
            output_path: Path for optimized image (defaults to temp file)
            max_dimension: Maximum width or height
            quality: JPEG quality (1-100)

        Returns:
            Path to optimized image
        """
        image_path = Path(image_path)

        if output_path is None:
            output_path = image_path.parent / f"{image_path.stem}_optimized.jpg"
        else:
            output_path = Path(output_path)

        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P", "LA"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = rgb_img

            # Resize if needed
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                ratio = min(max_dimension / width, max_dimension / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save optimized image
            img.save(output_path, "JPEG", quality=quality, optimize=True)

        return output_path

    @staticmethod
    def detect_document_type(image_path: Union[str, Path]) -> str:
        """
        Attempt basic document type detection from filename.

        Args:
            image_path: Path to document image

        Returns:
            Detected document type or 'unknown'
        """
        image_path = Path(image_path)
        filename_lower = image_path.name.lower()

        if "passport" in filename_lower:
            return "passport"
        elif "driver" in filename_lower or "license" in filename_lower or "dl" in filename_lower:
            return "drivers_license"
        elif "id" in filename_lower or "national" in filename_lower:
            return "national_id"
        else:
            return "unknown"

    @staticmethod
    def prepare_document(
        image_path: Union[str, Path],
        optimize: bool = True
    ) -> tuple[Path, dict]:
        """
        Prepare document for processing.

        Args:
            image_path: Path to document image
            optimize: Whether to optimize the image

        Returns:
            Tuple of (processed_image_path, metadata)
        """
        image_path = Path(image_path)

        # Validate
        is_valid, error = DocumentProcessor.validate_image(image_path)
        if not is_valid:
            raise ValueError(f"Invalid document image: {error}")

        # Metadata
        metadata = {
            "original_path": str(image_path),
            "original_size_mb": image_path.stat().st_size / (1024 * 1024),
            "detected_type": DocumentProcessor.detect_document_type(image_path)
        }

        # Optimize if requested
        processed_path = image_path
        if optimize:
            with Image.open(image_path) as img:
                width, height = img.size
                # Only optimize if image is large
                if width > 2048 or height > 2048 or metadata["original_size_mb"] > 2:
                    processed_path = DocumentProcessor.optimize_image(image_path)
                    metadata["optimized"] = True
                    metadata["optimized_size_mb"] = processed_path.stat().st_size / (1024 * 1024)
                else:
                    metadata["optimized"] = False

        return processed_path, metadata
