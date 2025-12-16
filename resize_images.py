"""
Resize PNG images to 30% of their original size while maintaining aspect ratio.

This script finds all PNG files in the data/ directory and resizes them to 30%
of their original dimensions.

Third-party packages:
- Pillow: https://pillow.readthedocs.io/en/stable/

Sample input: PNG files in data/ directory
Expected output: Resized PNG files (30% of original size) in the same location
"""

from pathlib import Path
from PIL import Image
from loguru import logger


def resize_image(image_path: Path, scale_factor: float = 0.3) -> None:
    """
    Resize an image to a percentage of its original size.

    Args:
        image_path: Path to the image file
        scale_factor: Scale factor (0.3 = 30% of original size)
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Get original dimensions
            original_width, original_height = img.size
            logger.info(f"Original size: {original_width}x{original_height}")

            # Calculate new dimensions
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            logger.info(f"New size: {new_width}x{new_height}")

            # Resize with high-quality resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save the resized image (overwrite original)
            resized_img.save(image_path, optimize=True)
            logger.info(f"✓ Resized {image_path.name}")

    except Exception as e:
        logger.error(f"✗ Failed to resize {image_path.name}: {e}")


def main() -> None:
    """Find and resize all PNG images in the data/ directory."""
    data_dir = Path(__file__).parent / "data"

    # Find all PNG files (case-insensitive)
    png_files = list(data_dir.glob("*.PNG")) + list(data_dir.glob("*.png"))

    if not png_files:
        logger.warning("No PNG files found in data/ directory")
        return

    logger.info(f"Found {len(png_files)} PNG file(s)")

    for png_file in png_files:
        resize_image(png_file, scale_factor=0.3)

    logger.info("Done!")


if __name__ == "__main__":
    main()
