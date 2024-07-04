import warnings
#warnings.filterwarnings("ignore", category=UserWarning, module='torchaudio._backend')
warnings.filterwarnings("ignore", category=UserWarning)

print ("Starting (imports can take a while first run)...", flush=True)

import os
import sys
import json
import math
import torch
import numpy as np
from run_ffmpeg import main as ffmpeg
from run_ffmpeg import get_media_duration
from pydub import AudioSegment



from pyannote.audio import Pipeline, Audio


def get_max_speaker(j, verbose=False):
    max_time = -1
    max_speaker = ""
    for k in j:
        ar = j[k]
        diffs = [ x[1] - x[0] for x in ar ]
        total = sum(diffs)
        if verbose:
            print (f"{k} total seconds: {total}")
        if total > max_time:
            max_time = total
            max_speaker = k

    if verbose:
        print (f"Max speaker: {max_speaker}")
    return max_speaker

def stitch_audio_segments(time_array, input_wav_file, output_wav_file):
    audio = AudioSegment.from_wav(input_wav_file)
    output_audio = AudioSegment.empty()
    for start_time, end_time in time_array:
        # Convert times to milliseconds
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # Extract the segment
        segment = audio[start_ms:end_ms]
        
        # Append the segment to the output audio
        output_audio += segment
    
    # Export the stitched audio to a new WAV file
    output_audio.export(output_wav_file, format="wav")


def get_speakers(input_file, write_output="speakers.json", verbose=False):
    io = Audio(mono='downmix', sample_rate=16000)
    waveform, sample_rate = io(input_file)

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=open('hftoken.txt').read().replace('\n', ''))

    pipeline.to(torch.device("cuda"))

    diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

    #diarization = pipeline(input_file)
    ar = {}
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if verbose:
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        if speaker in ar:
            ar[speaker].append([turn.start, turn.end])
        else:
            ar[speaker] = [[turn.start, turn.end]]

    if write_output:
        with open(write_output, 'w') as f:
            json.dump(ar, f, indent=4)
    return ar

def convert_input(input_file, output_file):
    ffmpeg(["-i", input_file, "-ar", "16000", "-ac", "1", output_file])

def convert_audio_wav(input_file, output_file):
    ffmpeg(["-i", input_file, output_file])

def convert_audio_final(input_file, output_file):
    ffmpeg(["-i", input_file, output_file])

def get_speaker_times(speakers, threshold=60, verbose=False):
    results = []
    for k in speakers:
        ar = speakers[k]
        diffs = [ x[1] - x[0] for x in ar ]
        total = sum(diffs)
        if verbose:
            print (f"{k} total seconds: {total}")
        if total > threshold:
            if verbose:
                print (f"Adding speaker {k} to result times")
            results += ar
    results = sorted(results, key=lambda x: x[0])
    return results

def get_max_speaker_times(speakers): # alternative strategy
    max_speaker = get_max_speaker(speakers)
    results = speakers[max_speaker]
    results = sorted(results, key=lambda x: x[0])
    return results

def get_dynamic_threshold(input_file):
    duration = get_media_duration(input_file)
    per_ten_minutes = 61
    buffer = 10
    # 61 seconds per every 10 minutes with a 10 second buffer
    threshold = int((math.ceil(duration/60/10) * 61) + 10)
    return threshold

def main():
    args = sys.argv[1:]
    if len(args) == 0:
        print ("Arguments missing.")
        sys.exit(1)
    
    input_file = os.path.basename(args[0])
    input_file_ext = os.path.splitext(input_file)[1]
    if not input_file_ext.startswith("."):
        input_file_ext = f".{input_file_ext}"
    
    if not os.path.exists(input_file):
        print (f'File not found "{input_file}"')
        sys.exit(1)

    #temporary_file = "tempfile.wav"
    hq_temporary_file = "hq_tempfile.wav"
    hq_combined_file = "hq_combined.wav"
    basename = os.path.basename(os.path.splitext(input_file)[0])
    final_output_file = f"output_{basename}{input_file_ext}"
    print (f'Input file: "{input_file}" - Output file: "{final_output_file}"')
    print("converting file to correct format")
    #convert_input(input_file, temporary_file)
    convert_audio_wav(input_file, hq_temporary_file)
    print ("Getting speakers from audio (may take some time)", flush=True)
    speakers = get_speakers(input_file)
    dynamic_threshold = get_dynamic_threshold(hq_temporary_file)
    print (f"Threshold speaker time: {dynamic_threshold}")
    speaker_times = get_speaker_times(speakers, dynamic_threshold, True)
    stitch_audio_segments(speaker_times, hq_temporary_file, hq_combined_file)
    convert_audio_final(hq_combined_file, final_output_file)
    print (f"Audio output to file \"{final_output_file}\"")

if __name__ == "__main__":
    main()