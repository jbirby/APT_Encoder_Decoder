#!/usr/bin/env python3
"""
APT Decoder — Convert a NOAA APT-format WAV file back to an image.

Demodulates the 2400 Hz AM subcarrier, extracts pixel values at the APT
pixel rate, and reconstructs the image. Works with real satellite recordings
or WAVs produced by apt_encode.py.

Usage:
    python3 apt_decode.py <input.wav> <output.png>

Produces two files:
  - <output.png>             Full 2080px-wide APT frame (both channels + sync)
  - <output>_channelA.png    Extracted 909px Channel A image

The decoder will automatically resample to 20800 Hz if the input WAV has a
different sample rate.

Dependencies:
    pip install numpy Pillow
"""

import numpy as np
from PIL import Image
import wave
import sys

SAMPLE_RATE = 20800
PIXEL_RATE = 4160
SAMPLES_PER_PIXEL = SAMPLE_RATE // PIXEL_RATE  # 5
LINE_WIDTH = 2080
IMAGE_START = 86   # Sync A (39) + Space A (47)
IMAGE_WIDTH = 909


def decode(wav_path, output_path):
    """Decode an APT-format WAV file into images."""
    with wave.open(wav_path, 'r') as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32767.0
    print(f"Input:  {wav_path}  ({len(audio)} samples, {sr} Hz, {len(audio)/sr:.1f}s)")

    # Resample to 20800 if needed
    if sr != SAMPLE_RATE:
        ratio = SAMPLE_RATE / sr
        new_len = int(len(audio) * ratio)
        x_old = np.linspace(0, 1, len(audio))
        x_new = np.linspace(0, 1, new_len)
        audio = np.interp(x_new, x_old, audio)
        print(f"  Resampled {sr} -> {SAMPLE_RATE} Hz")

    # AM demodulate: rectify + low-pass via averaging
    envelope = np.abs(audio)
    n_pixels = len(envelope) // SAMPLES_PER_PIXEL
    pixels = envelope[:n_pixels * SAMPLES_PER_PIXEL].reshape(-1, SAMPLES_PER_PIXEL).mean(axis=1)

    # Reshape into APT lines
    n_lines = n_pixels // LINE_WIDTH
    pixels = pixels[:n_lines * LINE_WIDTH].reshape(n_lines, LINE_WIDTH)

    # Normalize
    pmax = pixels.max()
    if pmax > 0:
        pixels = pixels / pmax * 255
    pixels = pixels.astype(np.uint8)

    # Full APT frame
    img_full = Image.fromarray(pixels, mode='L')
    img_full.save(output_path)
    print(f"Full frame: {img_full.width}x{img_full.height} -> {output_path}")

    # Channel A extraction
    ch_a = pixels[:, IMAGE_START:IMAGE_START + IMAGE_WIDTH]
    img_a = Image.fromarray(ch_a, mode='L')
    base = output_path.rsplit('.', 1)
    ch_a_path = f"{base[0]}_channelA.{base[1]}" if len(base) > 1 else f"{output_path}_channelA"
    img_a.save(ch_a_path)
    print(f"Channel A:  {img_a.width}x{img_a.height} -> {ch_a_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: apt_decode.py <input.wav> <output.png>")
        sys.exit(1)
    decode(sys.argv[1], sys.argv[2])
