# APT Encoder/Decoder

A Claude skill that encodes images into NOAA APT (Automatic Picture Transmission) format WAV files and decodes APT WAV recordings back into images.

APT is the analog image transmission format used by NOAA polar-orbiting weather satellites (NOAA-15, 18, 19). Hobbyists worldwide receive these signals with inexpensive SDR dongles and simple antennas, recording them as WAV files. This skill lets you go both directions — turn any image into an APT-format WAV that sounds like a real satellite pass, or extract images from recorded APT audio.

## How APT Works

Each APT transmission is a continuous stream of scan lines broadcast at 137 MHz. The satellite's radiometer sweeps the Earth below as it orbits, and each line is transmitted in real time as an amplitude-modulated audio signal on a 2400 Hz subcarrier.

A single APT line is 2080 pixels wide and takes 0.5 seconds to transmit (4160 pixels/second). The line structure looks like this:

```
| Sync A (39px) | Space (47px) | Channel A Image (909px) | Telemetry (45px) |
| Sync B (39px) | Space (47px) | Channel B Image (909px) | Telemetry (45px) |
```

Channel A carries visible-light imagery and Channel B carries infrared. Sync pulses (1040 Hz for Channel A, 832 Hz for Channel B) allow decoders to align each line. The telemetry wedges contain calibration data.

When decoded, the result is a long vertical strip showing the Earth as the satellite saw it during its pass — typically a ~15 minute window covering thousands of kilometers.

## Installation

### As a Claude Skill

Download `apt-encoder.skill` from the [Releases](../../releases) page and install it in Claude Desktop or Claude Code.

### Standalone Scripts

The encoder and decoder are self-contained Python scripts with minimal dependencies. Clone this repo and install requirements:

```bash
git clone https://github.com/YOUR_USERNAME/apt-encoder.git
cd apt-encoder
pip install numpy Pillow
```

## Usage

### Encoding an Image to APT WAV

```bash
python scripts/apt_encode.py input.jpg output.wav
```

The encoder will:
1. Convert the image to grayscale
2. Resize to 909 pixels wide (the APT channel width), preserving aspect ratio
3. Build each APT line with proper sync pulses, spacing, and telemetry
4. AM-modulate the pixel data onto a 2400 Hz carrier
5. Output a 16-bit mono WAV at 20800 Hz

The same image appears in both Channel A and Channel B. On a real satellite, these would be different spectral bands, but for encoding arbitrary images the duplication is standard practice.

### Decoding an APT WAV to Image

```bash
python scripts/apt_decode.py recording.wav output.png
```

This produces two files:
- `output.png` — the full 2080-pixel-wide APT frame showing both channels, sync bars, and telemetry wedges
- `output_channelA.png` — the extracted 909-pixel-wide Channel A image data

The decoder handles WAV files at any sample rate by resampling to 20800 Hz internally.

### As a Claude Skill

Once installed, just ask naturally:

> "Encode this photo as a NOAA satellite transmission WAV file"

> "I recorded a satellite pass — decode apt_recording.wav and show me the image"

> "Turn my logo into an APT audio file I can play through a speaker"

## Examples

### Encode

```
$ python scripts/apt_encode.py photo.jpg satellite_pass.wav
Input:  photo.jpg
Resized to 909x511  (511 APT lines, 255.5s)
  100/511 lines
  200/511 lines
  300/511 lines
  400/511 lines
  500/511 lines
Output: satellite_pass.wav  (255.5s, 10380 KB)
```

### Decode

```
$ python scripts/apt_decode.py satellite_pass.wav decoded.png
Input:  satellite_pass.wav  (5314400 samples, 20800 Hz, 255.5s)
Full frame: 2080x511 -> decoded.png
Channel A:  909x511 -> decoded_channelA.png
```

## Technical Details

| Parameter | Value |
|---|---|
| Sample rate | 20800 Hz |
| Carrier frequency | 2400 Hz |
| Pixel rate | 4160 pixels/sec |
| Line width | 2080 pixels |
| Line duration | 0.5 seconds |
| Image channel width | 909 pixels |
| Sync A frequency | 1040 Hz (7 cycles) |
| Sync B frequency | 832 Hz (7 cycles) |
| Audio format | 16-bit mono PCM WAV |
| Modulation | Amplitude modulation (AM) |

## Dependencies

- Python 3.8+
- NumPy
- Pillow (PIL)

No other libraries required. The scripts use only the standard library `wave` module for audio I/O.

## Project Structure

```
apt-encoder/
├── SKILL.md              # Claude skill instructions
├── scripts/
│   ├── apt_encode.py     # Image → APT WAV encoder
│   └── apt_decode.py     # APT WAV → Image decoder
└── evals/
    └── evals.json        # Test cases for skill evaluation
```

## Background

NOAA's polar-orbiting satellites have been broadcasting APT signals since the 1960s. The format was designed to be simple enough that anyone with a radio receiver could capture weather imagery directly. Today, NOAA-15 (launched 1998), NOAA-18 (2005), and NOAA-19 (2009) continue transmitting on 137.620, 137.9125, and 137.100 MHz respectively.

The APT format is being succeeded by LRPT (Low Rate Picture Transmission) on the Russian Meteor-M satellites, which uses digital QPSK modulation and offers higher resolution. However, APT remains popular in the amateur radio and weather satellite community for its simplicity and accessibility.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. Some ideas for extensions:

- Doppler shift simulation for more realistic encoding
- Noise injection and signal degradation for decoder testing
- Support for different images in Channel A vs Channel B
- LRPT encoder/decoder as a companion tool
- Real-time decoding from SDR audio streams
