"""
Training script for the CivicFix MobileNetV2 civic-issue classifier.

Trains a MobileNetV2 model (pre-trained on ImageNet) to classify images
into 4 civic-issue categories: graffiti, pothole, streetlight, trash.

─── Quick start ───────────────────────────────────────────────────────

1.  Organise a small dataset (≥ 20 images per class recommended):

        backend/
          dataset/
            train/
              graffiti/    ← put graffiti images here
              pothole/
              streetlight/
              trash/
            val/           ← (optional) validation split
              graffiti/
              pothole/
              streetlight/
              trash/

    If you only provide train/, the script auto-splits 80/20.

2.  Run from the backend/ directory:

        python -m app.train

    Or with options:

        python -m app.train --data-dir ./dataset --epochs 10 --batch-size 16

3.  Trained weights are saved to  backend/app/model/mobilenetv2_civicfix.pth
    and picked up automatically the next time the app starts.

─── Tips ──────────────────────────────────────────────────────────────
•  50 images per class usually gives > 85% accuracy.
•  Training takes ~1-3 minutes on a modern laptop CPU.
•  Images can be any size/format (JPEG, PNG, WebP); they are resized to 224×224.
•  Re-run training at any time – the old weights are overwritten.
"""

import argparse
import logging
import os
import shutil
import random
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger("civicfix.train")

# ── Constants ────────────────────────────────────────────
CLASS_NAMES = ["graffiti", "pothole", "streetlight", "trash"]
NUM_CLASSES = len(CLASS_NAMES)
IMG_SIZE = 224

_THIS_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = _THIS_DIR.parent / "dataset"
DEFAULT_OUTPUT = _THIS_DIR / "model" / "mobilenetv2_civicfix.pth"


# ── Transforms ───────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])


# ── Auto-split helper ───────────────────────────────────
def _auto_split(train_dir: Path, val_dir: Path, ratio: float = 0.2):
    """Copy ~20% of train/ images into val/ (random, stratified)."""
    logger.info("No val/ folder found – auto-splitting %.0f%% from train/", ratio * 100)
    random.seed(42)
    for cls in CLASS_NAMES:
        src = train_dir / cls
        dst = val_dir / cls
        if not src.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        images = sorted(src.iterdir())
        n_val = max(1, int(len(images) * ratio))
        picks = random.sample(images, n_val)
        for p in picks:
            shutil.copy2(p, dst / p.name)
    logger.info("Validation split created at %s", val_dir)


# ── Build model ──────────────────────────────────────────
def build_model(freeze_features: bool = True) -> nn.Module:
    """MobileNetV2 with ImageNet features optionally frozen."""
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    if freeze_features:
        for param in model.features.parameters():
            param.requires_grad = False

    model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
    return model


# ── Training loop ────────────────────────────────────────
def train(
    data_dir: Path,
    output_path: Path,
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 1e-3,
    unfreeze_epoch: int = 5,
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists():
        logger.error("Training data not found at %s", train_dir)
        logger.error(
            "Create sub-folders for each class:\n  %s",
            "\n  ".join(str(train_dir / c) for c in CLASS_NAMES),
        )
        sys.exit(1)

    # Auto-create validation split if missing
    if not val_dir.exists() or not any(val_dir.iterdir()):
        _auto_split(train_dir, val_dir)

    # Datasets
    train_ds = datasets.ImageFolder(str(train_dir), transform=train_transform)
    val_ds = datasets.ImageFolder(str(val_dir), transform=val_transform)

    # Verify class order matches CLASS_NAMES
    actual_classes = train_ds.classes
    if actual_classes != CLASS_NAMES:
        logger.warning(
            "Folder names %s differ from expected %s – class order comes from "
            "folder names (alphabetical). Make sure folder names match exactly.",
            actual_classes, CLASS_NAMES,
        )

    logger.info("Training samples: %d  |  Validation samples: %d", len(train_ds), len(val_ds))
    logger.info("Classes (from folders, alphabetical): %s", actual_classes)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    # Model
    model = build_model(freeze_features=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    best_acc = 0.0

    for epoch in range(1, epochs + 1):
        # Unfreeze all layers after warmup
        if epoch == unfreeze_epoch:
            logger.info("Unfreezing all layers for fine-tuning")
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.Adam(model.parameters(), lr=lr * 0.1)

        # ── Train ──
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)

        train_loss = running_loss / total
        train_acc = correct / total

        # ── Validate ──
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_total += labels.size(0)
        val_acc = val_correct / val_total if val_total else 0.0

        scheduler.step()

        logger.info(
            "Epoch %2d/%d  loss=%.4f  train_acc=%.1f%%  val_acc=%.1f%%",
            epoch, epochs, train_loss, train_acc * 100, val_acc * 100,
        )

        # Save best
        if val_acc >= best_acc:
            best_acc = val_acc
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_path)
            logger.info("  ✓ Saved best model (val_acc=%.1f%%) → %s", val_acc * 100, output_path)

    logger.info("Training complete. Best validation accuracy: %.1f%%", best_acc * 100)
    logger.info("Weights saved to: %s", output_path)


# ── CLI ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Train MobileNetV2 for CivicFix image classification",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR,
        help=f"Root dataset directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Where to save trained weights (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs (default: 10)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate (default: 0.001)")
    parser.add_argument(
        "--unfreeze-epoch", type=int, default=5,
        help="Epoch at which to unfreeze all layers (default: 5)",
    )
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        unfreeze_epoch=args.unfreeze_epoch,
    )


if __name__ == "__main__":
    main()
