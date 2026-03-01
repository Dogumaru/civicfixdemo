"""
Download training images for CivicFix MobileNetV2 classifier.

Uses icrawler (Bing image search) to fetch free images for each
civic-issue category: pothole, streetlight, trash, graffiti.

Usage:
    pip install icrawler
    python download_dataset.py              # downloads ~30 images per class
    python download_dataset.py --count 50   # downloads ~50 images per class
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger("dataset-downloader")

# ── Search queries per category ──
CATEGORY_QUERIES = {
    "pothole": [
        "pothole road damage",
        "pothole asphalt street",
        "road pothole close up photo",
    ],
    "streetlight": [
        "broken street light pole",
        "damaged streetlight urban",
        "street lamp broken",
    ],
    "trash": [
        "illegal dumping garbage street",
        "litter trash sidewalk city",
        "overflowing trash urban",
    ],
    "graffiti": [
        "graffiti wall urban vandalism",
        "spray paint graffiti building",
        "graffiti tagging concrete wall",
    ],
}

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "dataset" / "train"


def download_images(output_dir: Path, images_per_class: int = 30):
    """Download training images for all categories using icrawler."""
    try:
        from icrawler.builtin import BingImageCrawler
    except ImportError:
        logger.error("icrawler not installed. Run:  pip install icrawler")
        sys.exit(1)

    for category, queries in CATEGORY_QUERIES.items():
        cat_dir = output_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        existing = len([f for f in cat_dir.iterdir()
                        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
        if existing >= images_per_class:
            logger.info("[%s] Already have %d images, skipping.", category, existing)
            continue

        needed = images_per_class - existing
        logger.info("[%s] Need %d more images (have %d)", category, needed, existing)

        per_query = max(needed // len(queries) + 3, 8)

        for query in queries:
            # Recount in case previous query already filled up
            current = len([f for f in cat_dir.iterdir()
                           if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
            if current >= images_per_class:
                break

            remaining = images_per_class - current
            count = min(per_query, remaining)

            logger.info("  Searching Bing: '%s' (max %d)", query, count)
            crawler = BingImageCrawler(
                storage={"root_dir": str(cat_dir)},
                log_level=logging.WARNING,
            )
            crawler.crawl(
                keyword=query,
                max_num=count,
                min_size=(100, 100),
                file_idx_offset=current,
            )

        final = len([f for f in cat_dir.iterdir()
                      if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
        logger.info("[%s] Done — %d images in %s", category, final, cat_dir)

        if final < 10:
            logger.warning(
                "  ⚠ Only %d images for '%s'. Consider adding more manually.",
                final, category,
            )

    logger.info("\nDataset ready at: %s", output_dir)
    logger.info("To train the model, run:\n  cd backend\n  python -m app.train")


def main():
    parser = argparse.ArgumentParser(description="Download CivicFix training images")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--count", type=int, default=30,
        help="Images per category (default: 30)",
    )
    args = parser.parse_args()
    download_images(args.output, args.count)


if __name__ == "__main__":
    main()


def main():
    parser = argparse.ArgumentParser(description="Download CivicFix training images")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--count", type=int, default=30,
        help="Images per category (default: 30)",
    )
    args = parser.parse_args()
    download_images(args.output, args.count)


if __name__ == "__main__":
    main()
