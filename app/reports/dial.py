"""Heart Score dial SVG generator."""
import structlog
from typing import Tuple

log = structlog.get_logger()


def generate_heart_score_dial(
    score: int,
    band: str,
    confidence: str = "Medium",
) -> str:
    """Generate SVG for the P² Heart Score dial.

    Returns SVG string for embedding in PDF/WhatsApp.
    """
    # Color based on band
    colors = {
        "Excellent": "#10B981",
        "Good": "#10B981",
        "Fair": "#F59E0B",
        "At Risk": "#F97366",
        "High Risk": "#EF4444",
    }
    color = colors.get(band, "#10B981")

    # Calculate angle (180 degree arc, score 0-100)
    # 0 = left (180°), 100 = right (0°)
    angle = 180 - (score / 100 * 180)

    # Needletip position
    import math
    rad = math.radians(angle)
    cx, cy = 100, 100
    needle_len = 70
    nx = cx + needle_len * math.cos(rad)
    ny = cy - needle_len * math.sin(rad)

    # Generate SVG
    svg = f"""
<svg width="200" height="120" viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="dialGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#EF4444"/>
      <stop offset="33%" style="stop-color:#F97366"/>
      <stop offset="55%" style="stop-color:#F59E0B"/>
      <stop offset="85%" style="stop-color:#10B981"/>
      <stop offset="100%" style="stop-color:#10B981"/>
    </linearGradient>
  </defs>

  <!-- Background arc -->
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E5E7EB" stroke-width="12" stroke-linecap="round"/>

  <!-- Colored arc -->
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#dialGrad)" stroke-width="12" stroke-linecap="round"/>

  <!-- Score arc (filled portion) -->
  <path d="M 20 100 A 80 80 0 0 1 {nx:.1f} {ny:.1f}"
        fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>

  <!-- Needle -->
  <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#1F2937" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="8" fill="#1F2937"/>

  <!-- Score text -->
  <text x="{cx}" y="{cy + 25}" text-anchor="middle" font-family="Inter, sans-serif" font-size="28" font-weight="bold" fill="#1F2937">{score}</text>

  <!-- Band label -->
  <text x="{cx}" y="{cy + 45}" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" fill="{color}">{band}</text>

  <!-- Confidence -->
  <text x="100" y="115" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#6B7280">Confidence: {confidence}</text>
</svg>
"""
    return svg


def generate_bioage_visual(
    biological_age: float,
    chronological_age: int,
    gap_years: float,
) -> str:
    """Generate SVG for bio age vs chrono age comparison."""
    # Color based on gap
    if gap_years <= -3:
        color = "#10B981"
        status = "Younger"
    elif gap_years <= 3:
        color = "#10B981"
        status = "On par"
    elif gap_years <= 10:
        color = "#F59E0B"
        status = "Older"
    else:
        color = "#EF4444"
        status = "Much older"

    # Bar widths (max 150px)
    max_bar = 150
    bio_width = min(max_bar, (biological_age / 100) * max_bar)
    chrono_width = min(max_bar, (chronological_age / 100) * max_bar)

    svg = f"""
<svg width="300" height="80" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ font-family: Inter, sans-serif; }}
  </style>

  <!-- Biological age bar -->
  <rect x="10" y="10" width="{bio_width}" height="24" rx="4" fill="{color}"/>
  <text x="20" y="27" font-size="14" font-weight="bold" fill="white">{int(biological_age)}</text>

  <!-- Chronological age bar -->
  <rect x="10" y="45" width="{chrono_width}" height="24" rx="4" fill="#6B7280"/>
  <text x="20" y="62" font-size="14" font-weight="bold" fill="white">{chronological_age}</text>

  <!-- Labels -->
  <text x="{bio_width + 20}" y="26" font-size="12" fill="{color}">Bio Age</text>
  <text x="{chrono_width + 20}" y="62" font-size="12" fill="#6B7280">Chrono Age</text>

  <!-- Gap -->
  <text x="150" y="95" text-anchor="middle" font-size="12" fill="{color}">{gap_years:+.0f} years ({status})</text>
</svg>
"""
    return svg


def generate_ppg_waveform(signal_data: list = None) -> str:
    """Generate placeholder PPG waveform SVG."""
    # Simple placeholder waveform
    svg = """
<svg width="300" height="80" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="80" fill="#FAF7F2"/>
  <path d="M 0 40 Q 20 40, 30 40 T 50 40 T 70 40 T 90 20 T 100 20 T 110 40 T 130 40 T 150 40 T 170 40 T 190 40 T 210 20 T 220 20 T 230 40 T 250 40 T 270 40 T 290 40"
        fill="none" stroke="#0F766E" stroke-width="2"/>
  <text x="150" y="70" text-anchor="middle" font-size="10" fill="#6B7280">PPG Waveform</text>
</svg>
"""
    return svg