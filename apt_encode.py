#!/usr/bin/env python3
"""
APT Encoder — Convert an image to a NOAA APT-format WAV file.

Encodes any image into the analog audio format used by NOAA polar-orbiting
weather satellites (NOAA-15, 18, 19). The output WAV is a standards-compliant
APT signal at 20800 Hz sample rate with 2400 Hz AM subcarrier.

Usage:
    python3 apt_encode.py <input_image> <output.wav>

The input can be any image format PIL supports (JPG, PNG, BMP, TIFF, etc.).
It will be converted to grayscale, resized to 909px wide (the APT image
channel width), and encoded into a standard APT WAV.

APT Line Structure (2080 pixels, 0.5s per line):
    Sync A (39px) | Space A (47px) | Image A (909px) | Telemetry A (45px)
    Sync B (39px) | Space B (47px) | Image B (909px) | Telemetry B (45px)

Dependencies:
    pip install numpy Pillow
"""

import numpy as np
from PIL import Image
import wave
import sys

# === APT parameters ===
SAMPLE_RATE = 20800
PIXEL_RATE = 4160
SAMPLES_PER_PIXEL = SAMPLE_RATE // PIXEL_RATE  # 5
CARRIER_FREQ = 2400
LINE_WIDTH = 2080
IMAGE_WIDTH = 909

# Line segment sizes (in pixels)
SYNC_A_PX = 39
SPACE_A_PX = 47
TELEM_A_PX = 45
SYNC_B_PX = 39
SPACE_B_PX = 47
TELEM_B_PX = 45


def _sync_pattern(n_pixels, n_cycles):
    """Square-wave sync pattern: n_cycles over n_pixels."""
    px = np.zeros(n_pixels)
    for i in range(n_pixels):
        phase = (i / n_pixels) * n_cycles * 2 * np.pi
        px[i] = 255.0 if np.sin(phase) >= 0 else 0.0
    return px


def _telemetry():
    """Simplified telemetry wedge (gradient)."""
    return np.linspace(0, 255, TELEM_A_PX)


def _modulate(pixel_line):
    """AM-modulate a line of pixel values (0-255) onto 2400 Hz carrier."""
    n_samples = len(pixel_line) * SAMPLES_PER_PIXEL
    t = np.arange(n_samples) / SAMPLE_RATE
    carrier = np.sin(2 * np.pi * CARRIER_FREQ * t)
    envelope = np.repeat(pixel_line / 255.0, SAMPLES_PER_PIXEL)
    return carrier * envelope


def encode(input_path, output_path):
    """Encode an image file into an APT-format WAV."""
    img = Image.open(input_path).convert('L')
    aspect = img.height / img.width
    new_h = int(IMAGE_WIDTH * aspect)
    img = img.resize((IMAGE_WIDTH, new_h), Image.LANCZOS)
    data = np.array(img, dtype=np.float64)

    print(f"Input:  {input_path}")
    print(f"Resized to {IMAGE_WIDTH}x{new_h}  ({new_h} APT lines, {new_h * 0.5:.1f}s)")

    sync_a = _sync_pattern(SYNC_A_PX, 7)   # 1040 Hz equiv
    sync_b = _sync_pattern(SYNC_B_PX, 7)   # 832 Hz equiv
    space = np.zeros(SPACE_A_PX)
    telem = _telemetry()

    chunks = []
    for i in range(new_h):
        row = data[i, :]
        line = np.concatenate([
            sync_a, space, row, telem,
            sync_b, space, row, telem,
        ])
        assert len(line) == LINE_WIDTH
        chunks.append(_modulate(line))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{new_h} lines")

    audio = np.concatenate(chunks)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    pcm = (audio * 32767).astype(np.int16)

    with wave.open(output_path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())

    print(f"Output: {output_path}  ({len(pcm)/SAMPLE_RATE:.1f}s, {len(pcm)*2//1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: apt_encode.py <input_image> <output.wav>")
        sys.exit(1)
    encode(sys.argv[1], sys.argv[2])
