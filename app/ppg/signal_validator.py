"""PPG signal validation.

Validates client-computed metrics before storing.
"""
import structlog
from typing import Optional

log = structlog.get_logger()


def validate_ppg_metrics(
    hr_bpm: float,
    rmssd_ms: float,
    sdnn_ms: float = None,
    pnn50_pct: float = None,
    signal_quality: float = None,
) -> tuple[bool, Optional[str]]:
    """Validate PPG metrics are physiologically plausible.

    Returns (is_valid, error_message)
    """
    # Heart rate validation
    if hr_bpm < 30 or hr_bpm > 220:
        return False, f"Heart rate {hr_bpm} BPM is outside valid range (30-220)"

    if hr_bpm < 40:
        log.warning("ppg.hr_low", hr=hr_bpm)
    if hr_bpm > 120:
        log.warning("ppg.hr_high", hr=hr_bpm)

    # HRV validation (RMSSD)
    if rmssd_ms < 0 or rmssd_ms > 200:
        return False, f"RMSSD {rmssd_ms} ms is outside valid range (0-200)"

    if rmssd_ms < 10:
        log.warning("ppg.hrv_very_low", rmssd=rmssd_ms)

    # SDNN validation
    if sdnn_ms is not None:
        if sdnn_ms < 0 or sdnn_ms > 300:
            return False, f"SDNN {sdnn_ms} ms is outside valid range (0-300)"

    # pNN50 validation
    if pnn50_pct is not None:
        if pnn50_pct < 0 or pnn50_pct > 100:
            return False, f"pNN50 {pnn50_pct}% is outside valid range (0-100)"

    # Signal quality check (if provided)
    if signal_quality is not None:
        if signal_quality < 0.5:
            return False, "Signal quality too low. Please retry the scan."
        if signal_quality < 0.7:
            log.warning("ppg.quality_low", quality=signal_quality)

    return True, None


def detect_irregular_ibi(ibi_list: list) -> bool:
    """Detect irregular inter-beat intervals.

    Checks for:
    - Coefficient of variation > 20%
    - Very long or short intervals
    - Patterns suggesting arrhythmia
    """
    if len(ibi_list) < 10:
        return False  # Not enough data

    import statistics

    # Calculate coefficient of variation
    mean_ibi = statistics.mean(ibi_list)
    if mean_ibi == 0:
        return False

    stdev_ibi = statistics.stdev(ibi_list)
    cv = (stdev_ibi / mean_ibi) * 100

    if cv > 20:
        return True

    # Check for very long intervals (possible missed beats)
    long_intervals = sum(1 for ibi in ibi_list if ibi > mean_ibi * 1.5)
    if long_intervals > len(ibi_list) * 0.1:
        return True

    # Check for very short intervals (noise)
    short_intervals = sum(1 for ibi in ibi_list if ibi < mean_ibi * 0.6)
    if short_intervals > len(ibi_list) * 0.1:
        return True

    return False


def calculate_signal_quality(signal: list) -> float:
    """Calculate signal quality from raw signal.

    Returns 0-1 quality score.
    """
    if len(signal) < 100:
        return 0.0

    import statistics

    # Basic quality checks
    signal_range = max(signal) - min(signal)
    if signal_range < 10:
        return 0.0  # Too flat

    # Check for clipping (max value repeated)
    max_val = max(signal)
    clip_count = sum(1 for v in signal if v == max_val)
    if clip_count > len(signal) * 0.05:
        return 0.0  # Signal clipped

    # Check variance (too noisy or too smooth)
    try:
        stdev = statistics.stdev(signal)
        if stdev < 2:
            return 0.3  # Too flat
        if stdev > 100:
            return 0.3  # Too noisy
    except:
        return 0.5

    return 0.8  # Reasonable signal