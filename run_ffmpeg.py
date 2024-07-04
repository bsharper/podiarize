import re
import os
import sys
import math
try:
    from alive_progress import alive_bar
except:
    from basic_progress import LineUpdate as alive_bar

from subprocess import Popen, PIPE, DEVNULL, run, CalledProcessError

def convert_time_to_seconds(time_str):
    """
    Convert a time string in the format HH:MM:SS.sss to seconds.
    """
    try:
        hours, minutes, seconds = time_str.split(":")
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
        return total_seconds
    except ValueError:
        return 0

def get_media_duration(file_path):
    """
    Get the duration of a media file using ffmpeg.
    """
    try:
        result = run(f"ffprobe \"{file_path}\"", shell=True, check=True, text=True, capture_output=True)
        duration_match = re.search(r'Duration: (\d{2}:\d{2}:\d{2}\.\d{2})', result.stderr)
        if duration_match:
            return convert_time_to_seconds(duration_match.group(1))
        else:
            return 0
    except CalledProcessError as e:
        return f"Error: {e}"

def main(args):

    verbose = False
    if "DEBUG" in os.environ.keys() and os.environ["DEBUG"] == 1:
        verbose = True

    input_filename = ""
    output_filename = ""
    duration = 0
    args.insert(0, 'ffmpeg')
    if "-y" not in args:
        args.append("-y")
    if verbose: print (f"> {' '.join(args)}")
    process = Popen(args, stdout=PIPE, stderr=PIPE, stdin=PIPE, text=True)
    for line in iter(process.stderr.readline, ''):
        m = re.match(r'\s*Duration: (\d\d:\d\d:\d\d.\d\d)', line)
        if m:
            duration = int(math.ceil(convert_time_to_seconds(m[1])))
            if duration and input_filename and output_filename:
                break
        im = re.match("Input #\d,.*from '(.*)'", line)
        if im:
            if input_filename:
                input_filename = f"{input_filename},{im[1]}"
            else:
                input_filename = im[1]

            if duration and input_filename and output_filename:
                break
        om = re.match("Output #0,.*to '(.*)'", line)
        if om:
            output_filename = om[1]
            if duration and input_filename and output_filename:
                break
        # if duration == 0:
        #     print (line)
        #print (duration, input_filename, output_filename)
        
    
    title = f'Converting "{input_filename}" to "{output_filename}"'
    with alive_bar(duration, manual=True, title=title) as bar:
        for line in iter(process.stderr.readline, ''):
            m = re.match('.*time=(\d\d:\d\d:\d\d\.\d+)', line)
            if m:
                time = m[1]
                seconds = convert_time_to_seconds(time)
                per = seconds/duration
                bar(per)
        bar(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        print ("Arguments missing.")
        sys.exit(1)
    
    main(args)