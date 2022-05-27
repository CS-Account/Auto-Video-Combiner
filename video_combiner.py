import subprocess, os

def combine_videos(input_files, output_file):
    """Combine input video files into a single video file using ffmpeg muxing.

    https://stackoverflow.com/questions/7333232/how-to-concatenate-two-mp4-files-using-ffmpeg
    https://stackoverflow.com/questions/2869281/how-to-determine-video-codec-of-a-file-with-ffmpeg

    Returns:
        Error message if error occurred. None otherwise."""

    # Check what type of video format the output file is using ffp
    output_file_format = None
    try:
        video_type_check_command = ["ffprobe",  "-v",  "error",  "-select_streams",  "v:0",  "-show_entries",
                                    "stream=codec_name",  "-of",  "default=noprint_wrappers=1:nokey=1", input_files[0]]
        output_file_format = subprocess.check_output(video_type_check_command).decode("utf-8").strip()
        print("\toutput_file_format: {}".format(output_file_format))
    except subprocess.CalledProcessError as e:
        error = "{}|{}".format(e.returncode, e.output)
        return error

    # Create temporary file containing all input files.
    temporary_file = "{}.txt".format(output_file)
    with open(temporary_file, "w") as f:
        for input_file in input_files:
            f.write("file '{}'\n".format(input_file.replace(os.sep, "/")))

    # Create command list to execute ffmpeg.
    combine_command = []
    if output_file_format == "h264":
        combine_command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-f", "concat", "-safe", "0", "-i" , temporary_file, "-c", "copy", output_file.replace(os.sep, "/")]
    else:
        print("\tUnsupported output format: {}. Trying Anyways".format(output_file_format))
        combine_command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-f", "concat", "-safe", "0", "-i" , temporary_file, "-c", "copy", output_file.replace(os.sep, "/")]


    try:
        output_text = subprocess.check_output(combine_command).decode("utf-8")
        print("\toutput_text: {}".format(output_text))
    except subprocess.CalledProcessError as e:
        error = "{}|{}".format(e.returncode, e.output)
        return error
    finally:
        os.remove(temporary_file)


if __name__ == "__main__":
    print("This is a library file. Do not run directly.")