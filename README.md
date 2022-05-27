# Auto Combiner
## Description
Auto Combiner is a tool that combines multiple video files into one video file with muxing.
FFmpeg is used to combine the video files through subprocess.

## Project Goals
* Accept regex for file increment matching regex group is the part which will be looked at for sortation.
* Accept folder path for input files
* Accept regex and template for output file name
* Accept folder path for output files
* Create module to join one or more video files in order
* [TODO] Multi-thread using actions and threads

## Usage
    usage: auto_combiner.py [-h] -i INPUT_FOLDER [--input-regex INPUT_REGEX] [-r] -o OUTPUT_FOLDER [--output-regex OUTPUT_REGEX] [-t OUTPUT_FILE_TEMPLATE] [-d] [-c | -w]

    Combine input video files into a single video file using ffmpeg muxing.

    options:
    -h, --help            show this help message and exit
    -i INPUT_FOLDER, --input-folder INPUT_FOLDER
                            Folder containing input video files.
    --input-regex INPUT_REGEX
                            Regular expression for input video files. Grouping around incrementing number is mandatory. (Default: .*([0-9]*)\.[a-zA-Z0-9]*)
    -r, --reverse_order   Reverse order of input files.
    -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                            Folder to save output video files.
    --output-regex OUTPUT_REGEX
                            Regular expression for output video files applied to the first file of a set to be used for substitution in the output file name. (Default: .*(?:[0-9]*)\.[a-zA-Z0-9]*)
    -t OUTPUT_FILE_TEMPLATE, --output-file-template OUTPUT_FILE_TEMPLATE
                            Template for output video file name. Use $[groupnumber] for substitution and /[number of leading 0s] for number of files combined. '\' escapes (Default: $1$2)
    -d, --dry-run         Do not execute ffmpeg, but print out video sets.
    -c, --combine         Combine video sets into a single video file when output file already exists.
    -w, --overwrite       Overwrite existing output file when output file already exists.