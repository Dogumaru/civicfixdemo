"""
AI Classification module for CivicFix.

Three-tier classification cascade:
  1. Google Gemini Flash  – best accuracy, needs API key (free tier)
  2. MobileNetV2 (local)  – good accuracy, needs trained weights
  3. Simulated fallback   – deterministic hash, always works

The first tier that succeeds is used.  If all AI tiers fail the
simulated fallback guarantees a result so the app never breaks.

Train MobileNetV2 weights:
    python -m app.train            # from the backend/ directory
    python -m app.train --help     # see all options

Set Gemini API key (free at https://aistudio.google.com):
    export GEMINI_API_KEY=your-key-here   # or add to .env
"""

import base64
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import io
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

logger = logging.getLogger("civicfix.classifier")

# ── Paths ─────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent
MODEL_WEIGHTS_PATH = _THIS_DIR / "model" / "mobilenetv2_civicfix.pth"

# ── Class labels (must match the order used during training) ──
CLASS_NAMES = ["graffiti", "pothole", "streetlight", "trash"]
NUM_CLASSES = len(CLASS_NAMES)

# ── ImageNet-normalised transform (same as training) ──────
_inference_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# ── Domain look-up tables ────────────────────────────────
CATEGORY_CONFIG = {
    "pothole": {
        "severity_range": (0.5, 1.0),
        "repair_days": {"LOW": 14, "MEDIUM": 7, "HIGH": 3, "CRITICAL": 1},
        "cost_range": {"LOW": (200, 500), "MEDIUM": (500, 1500),
                       "HIGH": (1500, 3000), "CRITICAL": (3000, 8000)},
    },
    "streetlight": {
        "severity_range": (0.3, 0.9),
        "repair_days": {"LOW": 21, "MEDIUM": 10, "HIGH": 5, "CRITICAL": 2},
        "cost_range": {"LOW": (100, 300), "MEDIUM": (300, 800),
                       "HIGH": (800, 2000), "CRITICAL": (2000, 5000)},
    },
    "trash": {
        "severity_range": (0.2, 0.8),
        "repair_days": {"LOW": 7, "MEDIUM": 3, "HIGH": 1, "CRITICAL": 1},
        "cost_range": {"LOW": (50, 150), "MEDIUM": (150, 400),
                       "HIGH": (400, 1000), "CRITICAL": (1000, 2500)},
    },
    "graffiti": {
        "severity_range": (0.2, 0.7),
        "repair_days": {"LOW": 30, "MEDIUM": 14, "HIGH": 7, "CRITICAL": 3},
        "cost_range": {"LOW": (100, 250), "MEDIUM": (250, 600),
                       "HIGH": (600, 1500), "CRITICAL": (1500, 3000)},
    },
}

SEVERITY_THRESHOLDS = [
    (0.25, "LOW"),
    (0.50, "MEDIUM"),
    (0.75, "HIGH"),
    (1.00, "CRITICAL"),
]


# ── Model singleton ──────────────────────────────────────
_model: Optional[torch.nn.Module] = None
_model_loaded: bool = False


def _build_model() -> torch.nn.Module:
    """Build a MobileNetV2 with the final classifier head replaced for our 4 classes."""
    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = torch.nn.Linear(model.last_channel, NUM_CLASSES)
    return model


def _load_model() -> Optional[torch.nn.Module]:
    """Load the fine-tuned MobileNetV2 weights (lazy, once)."""
    global _model, _model_loaded
    if _model_loaded:
        return _model

    _model_loaded = True  # prevent repeated attempts

    if not MODEL_WEIGHTS_PATH.exists():
        logger.warning(
            "Trained model not found at %s – falling back to simulated classifier. "
            "Run 'python -m app.train' to train a real model.",
            MODEL_WEIGHTS_PATH,
        )
        return None

    try:
        model = _build_model()
        state = torch.load(MODEL_WEIGHTS_PATH, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()
        _model = model
        logger.info("MobileNetV2 civic-issue classifier loaded from %s", MODEL_WEIGHTS_PATH)
        return _model
    except Exception as exc:
        logger.error("Failed to load model weights: %s – using simulated fallback.", exc)
        return None


# ── Helpers ──────────────────────────────────────────────
def _get_severity(score: float) -> str:
    for threshold, label in SEVERITY_THRESHOLDS:
        if score <= threshold:
            return label
    return "CRITICAL"


def _deterministic_random(seed_bytes: bytes, low: float = 0.0, high: float = 1.0) -> float:
    """Deterministic float from bytes (used for cost estimation & simulated fallback)."""
    h = int(hashlib.sha256(seed_bytes[:4096]).hexdigest(), 16)
    normalized = (h % 10000) / 10000.0
    return low + normalized * (high - low)


def _make_description(category: str, confidence: float, severity: str) -> str:
    pct = int(confidence * 100)
    urgent = severity in ("HIGH", "CRITICAL")
    descriptions = {
        "pothole": f"Pothole detected – {pct}% confidence. Road surface damage requiring {'immediate' if urgent else 'scheduled'} repair.",
        "streetlight": f"Broken streetlight detected – {pct}% confidence. {'Safety hazard – immediate attention needed.' if urgent else 'Maintenance scheduled.'}",
        "trash": f"Illegal dumping/trash detected – {pct}% confidence. {'Large accumulation – urgent cleanup required.' if urgent else 'Standard cleanup needed.'}",
        "graffiti": f"Graffiti/vandalism detected – {pct}% confidence. {'Offensive content – priority removal.' if urgent else 'Cosmetic damage – scheduled removal.'}",
    }
    return descriptions.get(category, f"{category} detected – {pct}% confidence.")


# ══════════════════════════════════════════════════════════
# TIER 1 — Google Gemini Flash (API, best accuracy)
# ══════════════════════════════════════════════════════════
_gemini_client = None
_gemini_checked: bool = False

_GEMINI_PROMPT = """You are a civic infrastructure classifier. Analyze this image and classify it into exactly ONE of these categories:
- pothole (road damage, cracks, holes in pavement)
- streetlight (broken, damaged, or non-functioning street lights)
- trash (illegal dumping, litter, garbage accumulation)
- graffiti (spray paint, vandalism, tagging on surfaces)

Also assess the severity:
- LOW (minor cosmetic issue)
- MEDIUM (moderate damage needing scheduled repair)
- HIGH (severe damage requiring urgent repair)
- CRITICAL (dangerous condition requiring immediate action)

Respond ONLY with valid JSON, no markdown, no explanation:
{"category": "pothole|streetlight|trash|graffiti", "confidence": 0.0-1.0, "severity": "LOW|MEDIUM|HIGH|CRITICAL", "severity_score": 0.0-1.0}"""


def _get_gemini_client():
    """Lazily initialise the Gemini client (once)."""
    global _gemini_client, _gemini_checked
    if _gemini_checked:
        return _gemini_client
    _gemini_checked = True

    try:
        from app.config import settings
        api_key = settings.gemini_api_key
        if not api_key:
            logger.info("No GEMINI_API_KEY configured – skipping Gemini tier.")
            return None

        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Gemini Flash client initialised (tier-1 classifier).")
        return _gemini_client
    except ImportError:
        logger.warning("google-genai package not installed – skipping Gemini tier.")
        return None
    except Exception as exc:
        logger.warning("Failed to initialise Gemini client: %s", exc)
        return None


def _gemini_classify(image_bytes: bytes, filename: str = "") -> Optional[Dict]:
    """Tier 1: Call Gemini 2.5 Flash Lite to classify the image. Returns result dict or None."""
    client = _get_gemini_client()
    if client is None:
        return None

    try:
        from google.genai import types

        # Detect MIME type from extension or default to JPEG
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                    "webp": "image/webp", "gif": "image/gif"}
        mime_type = mime_map.get(ext, "image/jpeg")

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[_GEMINI_PROMPT, image_part],
        )

        # Parse JSON from response
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        data = json.loads(text)

        # Validate required fields
        category = data.get("category", "").lower().strip()
        if category not in CLASS_NAMES:
            logger.warning("Gemini returned unknown category '%s' – falling through.", category)
            return None

        confidence = float(data.get("confidence", 0.85))
        confidence = max(0.0, min(1.0, confidence))

        severity = data.get("severity", "MEDIUM").upper().strip()
        if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            severity = "MEDIUM"

        severity_score = float(data.get("severity_score", 0.5))
        severity_score = max(0.0, min(1.0, severity_score))

        logger.info("Gemini classified as %s (%.0f%% confidence, %s severity)",
                     category, confidence * 100, severity)

        return {
            "category": category,
            "confidence": round(confidence, 2),
            "severity": severity,
            "severity_score": round(severity_score, 2),
            "source": "gemini",
        }
    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned unparseable JSON: %s – falling through.", exc)
        return None
    except Exception as exc:
        logger.warning("Gemini classification failed: %s – falling through.", exc)
        return None


# ══════════════════════════════════════════════════════════
# TIER 2 — MobileNetV2 (local, no API key needed)
# ══════════════════════════════════════════════════════════
def _mobilenet_classify(image_bytes: bytes) -> Optional[Dict]:
    """Run MobileNetV2 inference. Returns result dict or None on failure."""
    model = _load_model()
    if model is None:
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _inference_transform(img).unsqueeze(0)  # [1, 3, 224, 224]

        with torch.no_grad():
            logits = model(tensor)                        # [1, NUM_CLASSES]
            probs = F.softmax(logits, dim=1)[0]           # [NUM_CLASSES]

        top_prob, top_idx = probs.max(0)
        category = CLASS_NAMES[top_idx.item()]
        confidence = round(top_prob.item(), 2)

        logger.info("MobileNetV2 classified as %s (%.0f%% confidence)", category, confidence * 100)
        return {"category": category, "confidence": confidence, "probs": probs, "source": "mobilenet"}
    except Exception as exc:
        logger.error("MobileNetV2 inference failed: %s – using simulated fallback.", exc)
        return None


# ══════════════════════════════════════════════════════════
# TIER 3 — Simulated fallback (deterministic, always works)
# ══════════════════════════════════════════════════════════
def _simulated_classify(image_bytes: bytes) -> Dict:
    """Deterministic hash-based classifier used when no trained model is available."""
    seed = image_bytes[:4096] if len(image_bytes) >= 4096 else image_bytes

    h = int(hashlib.sha256(seed).hexdigest(), 16)
    category_names = list(CATEGORY_CONFIG.keys())
    weights = [15, 40, 25, 20]  # graffiti, pothole, streetlight, trash (alpha order)
    bucket = h % 100
    cumulative, chosen_idx = 0, 0
    for i, w in enumerate(weights):
        cumulative += w
        if bucket < cumulative:
            chosen_idx = i
            break

    category = category_names[chosen_idx]
    confidence = round(_deterministic_random(seed + b"conf", 0.72, 0.97), 2)
    logger.info("Simulated fallback classified as %s (%.0f%% confidence)", category, confidence * 100)
    return {"category": category, "confidence": confidence, "probs": None, "source": "simulated"}


# ══════════════════════════════════════════════════════════
# PUBLIC API (unchanged signature)
# ══════════════════════════════════════════════════════════
def classify_image(image_bytes: bytes, filename: str = "") -> Dict:
    """
    Classify an uploaded civic-issue image.

    Three-tier cascade:
      1. Gemini Flash  – if GEMINI_API_KEY is set and the call succeeds
      2. MobileNetV2   – if trained weights exist at app/model/
      3. Simulated      – deterministic hash fallback (always works)

    Returns dict with: category, confidence, severity, severity_score,
                       estimated_repair_days, estimated_cost, description
    """
    seed = image_bytes[:4096] if len(image_bytes) >= 4096 else image_bytes

    # ── Tier 1: Gemini Flash ──
    gemini_result = _gemini_classify(image_bytes, filename)
    if gemini_result is not None:
        category = gemini_result["category"]
        confidence = gemini_result["confidence"]
        severity = gemini_result["severity"]
        severity_score = gemini_result["severity_score"]
        cat_config = CATEGORY_CONFIG[category]

        # Use Gemini's severity directly; fill cost/repair from domain tables
        repair_days = cat_config["repair_days"][severity]
        cost_lo, cost_hi = cat_config["cost_range"][severity]
        estimated_cost = round(_deterministic_random(seed + b"cost", cost_lo, cost_hi), 2)

        return {
            "category": category,
            "confidence": confidence,
            "severity": severity,
            "severity_score": severity_score,
            "estimated_repair_days": repair_days,
            "estimated_cost": estimated_cost,
            "description": _make_description(category, confidence, severity),
            "source": "gemini",
        }

    # ── Tier 2: MobileNetV2 ──
    result = _mobilenet_classify(image_bytes)

    # ── Tier 3: Simulated fallback ──
    if result is None:
        result = _simulated_classify(image_bytes)

    category = result["category"]
    confidence = result["confidence"]
    cat_config = CATEGORY_CONFIG[category]

    # Estimate severity
    if result.get("probs") is not None:
        severity_score = round(
            _deterministic_random(seed + b"sev", *cat_config["severity_range"])
            * (0.6 + 0.4 * confidence),
            2,
        )
    else:
        severity_score = round(
            _deterministic_random(seed + b"sev", *cat_config["severity_range"]), 2
        )

    severity_score = min(severity_score, 1.0)
    severity = _get_severity(severity_score)

    # Cost & repair estimates (domain look-up)
    repair_days = cat_config["repair_days"][severity]
    cost_lo, cost_hi = cat_config["cost_range"][severity]
    estimated_cost = round(_deterministic_random(seed + b"cost", cost_lo, cost_hi), 2)

    return {
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "severity_score": severity_score,
        "estimated_repair_days": repair_days,
        "estimated_cost": estimated_cost,
        "description": _make_description(category, confidence, severity),
        "source": result["source"],
    }


def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    """Return (width, height) of an image."""
    img = Image.open(io.BytesIO(image_bytes))
    return img.size
