# Podiarize

Podiarize (podcast + diarize) is a Python script that for extracting and stitching together the main speaker's segments from audio files, particularly useful for podcasts.

## Description

Podiarize uses speaker diarization (provided by pyannote) to identify different speakers in an audio file, then extracts and combines the segments of the primary speaker(s). This can be useful for:

- Condensing podcasts to focus on the main content
- Removing advertisements or less relevant sections

## Features

- Speaker diarization using pyannote.audio
- Dynamic threshold calculation for speaker inclusion
- Support for various input audio formats

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. [Agree to the terms for pyannote](https://github.com/pyannote/pyannote-audio?tab=readme-ov-file#tldr)
4. Put a valid huggingface token in hf.txt (or change `modify_podcast.py` to use your token)
5. Make sure you have `ffmpeg` and `ffprobe` in your path.

## Running

`python modify_podcast.py some_audio_file.mp3`

This will output to `output_some_audio_file.mp3`. 

## License

The license in the LICENSE.md file applies only to the code in this repository. Be sure to review the license for pyannote and relevant models