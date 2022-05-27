"""This script combines input video files into a single video file using ffmpeg muxing."""

import argparse
from enum import Enum
import functools
import os
import re
import sys
import time
import video_combiner


class AutoCombiner:
    class COMBINETYPE(Enum):
        """Enum for combination types."""

        COMBINE = 1
        SKIP = 2
        OVERWRITE = 3

    def __init__(self):
        self.errors = []

    def _collect_video_sets(
        self,
        input_folder_path,
        output_folder_path,
        input_regex,
        output_regex,
        output_template,
        reverse=False,
    ):
        """Collect video sets from input folder using regex."""
        # Get input files.
        input_files = []
        for file in os.listdir(input_folder_path):
            if re.search(input_regex, file):
                input_files.append(
                    os.path.abspath(os.path.join(input_folder_path, file))
                )
        print("Found {} input files.".format(len(input_files)))

        video_sets = {}
        for input_file in input_files:
            output_filename = self._generate_output_filename(
                os.path.basename(input_file), output_regex, output_template
            )

            if output_filename is None:
                continue

            video_sets.setdefault(output_filename, []).append(input_file)

        for key in video_sets.keys():
            self._sort_video_set(video_sets[key], input_regex, reverse)

        parsed_video_sets = {}
        for key in video_sets.keys():
            output_file = os.path.abspath(
                os.path.join(
                    output_folder_path,
                    self._add_combined_number_to_filename(key, len(video_sets[key])),
                )
            )
            parsed_video_sets[output_file] = video_sets[key]

        print("Found {} video sets.".format(len(parsed_video_sets)))

        return parsed_video_sets

    def _sort_video_set(self, video_set, input_regex, reverse_order=False):
        """Sort video set using incrementing section specified by input regex."""
        video_set.sort(
            key=lambda input_file: re.search(input_regex, input_file).group(1),
            reverse=reverse_order,
        )

    def _generate_output_filename(self, input_file, output_regex, output_template):
        """Generate output filename from input file using regex."""
        regex_match = re.search(output_regex, input_file)
        if not regex_match:
            print("Input file does not match output regex: {}".format(input_file))
            self.errors.append(
                "Input file does not match output regex: {}".format(input_file)
            )
            return None

        # find all non escaped $ signs in output template and replace them with regex group values.
        try:
            output_filename = re.sub(
                r"(?<!\\)\$(\d+)",
                lambda match: regex_match.group(int(match.group(1))),
                output_template,
            )
            output_filename = re.sub(r"\\\$", "$", output_filename)
            return output_filename
        except IndexError:
            print(
                "Output template does not match output regex match (IndexError): {}".format(
                    output_template
                )
            )
            self.errors.append(
                "Output template does not match output regex match (IndexError): {}".format(
                    output_template
                )
            )
            return None

    def _add_combined_number_to_filename(self, filename, combined_number):
        output_filename = re.sub(
            r"(?<!\\)/(\d*)",
            lambda match: "{:0{}d}".format(combined_number, match.group(1)),
            filename,
        )
        output_filename = re.sub(r"\\/", "/", output_filename)
        return output_filename

    def auto_combine_videos(
        self,
        input_folder_path,
        output_folder_path,
        input_regex,
        output_regex,
        output_template,
        reverse_order=False,
        dry_run=False,
        combine_type=COMBINETYPE.SKIP,
        verbose=False,
    ):
        """Combine video files from input folder using regex."""
        self.errors = []

        # Check if input folder exists.
        if not os.path.exists(input_folder_path):
            print("Input folder does not exist: {}".format(input_folder_path))
            self.errors.append(
                "Input folder does not exist: {}".format(input_folder_path)
            )
            return

        # Check if output folder exists.
        if not os.path.exists(output_folder_path):
            print("Output folder does not exist: {}".format(output_folder_path))
            self.errors.append(
                "Output folder does not exist: {}".format(output_folder_path)
            )
            return

        # Check if input folder is empty.
        if not os.listdir(input_folder_path):
            print("Input folder is empty: {}".format(input_folder_path))
            self.errors.append("Input folder is empty: {}".format(input_folder_path))
            return

        video_sets = self._collect_video_sets(
            input_folder_path,
            output_folder_path,
            input_regex,
            output_regex,
            output_template,
            reverse_order,
        )

        print("\nList of Actions To Be Performed:\n")

        messages = {}
        actions = {}
        for output_file, input_files in video_sets.items():
            file_exists = os.path.exists(os.path.join(output_folder_path, output_file))

            message = "\t(Dry Run) " if dry_run else "\t"

            def internal_combine_videos(
                input_files, output_file, combine=False, verbose=False
            ):
                if combine:
                    backup_file = output_file + ".bak"

                    os.rename(output_file, backup_file)

                    if reverse_order:
                        new_input_files = [*input_files, backup_file]
                    else:
                        new_input_files = [backup_file, *input_files]

                    result = video_combiner.combine_videos(
                        new_input_files, output_file, verbose=verbose
                    )

                    # Revert changes if combine failed.
                    if result is None:
                        os.remove(backup_file)
                    else:
                        if os.path.exists(output_file):
                            os.remove(output_file)
                        os.rename(backup_file, output_file)
                else:
                    result = video_combiner.combine_videos(
                        input_files, output_file, verbose=verbose
                    )
                return result

            if not file_exists:
                message = message + "Creating {} with files:\n\t\t{}".format(
                    output_file, "\n\t\t".join(input_files)
                )
                messages.setdefault("Creating", []).append(message)
                actions.setdefault("Creating", []).append(
                    (
                        output_file,
                        len(input_files),
                        functools.partial(
                            internal_combine_videos,
                            input_files,
                            output_file,
                            verbose=verbose,
                        ),
                    )
                )
            elif combine_type == self.COMBINETYPE.OVERWRITE:
                message = message + "Overwriting {} with files:\n\t\t{}".format(
                    output_file, "\n\t\t".join(input_files)
                )
                messages.setdefault("Overwriting", []).append(message)
                actions.setdefault("Overwriting", []).append(
                    (
                        output_file,
                        len(input_files),
                        functools.partial(
                            internal_combine_videos,
                            input_files,
                            output_file,
                            verbose=verbose,
                        ),
                    )
                )
            elif combine_type == self.COMBINETYPE.SKIP:
                message = message + "Skipping {} with files:\n\t\t{}".format(
                    output_file, "\n\t\t".join(input_files)
                )
                messages.setdefault("Skipping", []).append(message)
                actions.setdefault("Skipping", []).append(
                    (output_file, len(input_files), None)
                )
            elif combine_type == self.COMBINETYPE.COMBINE:
                message = message + "Combining {} with files:\n\t\t{}".format(
                    output_file, "\n\t\t".join(input_files)
                )
                messages.setdefault("Combining", []).append(message)
                actions.setdefault("Combining", []).append(
                    (
                        output_file,
                        len(input_files),
                        functools.partial(
                            internal_combine_videos,
                            input_files,
                            output_file,
                            True,
                            verbose,
                        ),
                    )
                )

        for message_type, messages in messages.items():
            print(message_type)
            for message in messages:
                print(message)

        if not dry_run:
            print("\nPerforming Actions:\n")
            for action_type, actions_list in actions.items():
                print("{} List".format(action_type))
                times = []
                for output_file, number_of_items, action in actions_list:
                    print(
                        "\tProcessing {} ({} sub items)".format(
                            output_file, number_of_items
                        )
                    )
                    start_time = time.time()
                    if action:
                        result = action()
                    else:
                        result = None

                    time_total = time.time() - start_time
                    times.append(time_total)
                    average_time = sum(times) / len(times)
                    actions_remaining_in_list = len(actions_list) - len(times)
                    print(
                        "\t\tProcess Took: {:.2f} seconds (estimating {:.2f} seconds till {} list ({}/{} {:.2f}%) is complete)".format(
                            time.time() - start_time,
                            average_time * actions_remaining_in_list,
                            action_type,
                            len(times),
                            len(actions_list),
                            (len(times) / len(actions_list)) * 100,
                        )
                    )

                    if result:
                        self.errors.append(
                            "Error combining video: {} with error: {}".format(
                                output_file, result
                            )
                        )
                        print(
                            "\n\tError combining video: {} with error: {}\n".format(
                                output_file, result
                            )
                        )
        return self.errors


if __name__ == "__main__":
    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description="Combine input video files into a single video file using ffmpeg muxing."
    )
    parser.add_argument(
        "-i",
        "--input-folder",
        required=True,
        help="Folder containing input video files.",
    )
    parser.add_argument(
        "--input-regex",
        default=r".*([0-9]+)\.[a-zA-Z0-9]*",
        help="Regular expression for input video files. Grouping around incrementing number is mandatory. (Default: .*([0-9]*)\.[a-zA-Z0-9]*)",
    )
    parser.add_argument(
        "-r",
        "--reverse_order",
        action="store_true",
        help="Reverse order of input files.",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        required=True,
        help="Folder to save output video files.",
    )
    parser.add_argument(
        "--output-regex",
        default=r"(.*)(?:[0-9]+)(\.[a-zA-Z0-9]*)",
        help="Regular expression for output video files applied to the first file of a set to be used for substitution in the output file name. (Default: .*(?:[0-9]*)\.[a-zA-Z0-9]*)",
    )
    parser.add_argument(
        "-t",
        "--output-file-template",
        default="$1$2",
        help="Template for output video file name. Use $[groupnumber] for substitution and /[number of leading 0s] for number of files combined. '\\' escapes (Default: $1$2)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Do not execute ffmpeg, but print out video sets.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print out all ffmpeg output."
    )

    overwrite_combine_group = parser.add_mutually_exclusive_group()
    overwrite_combine_group.add_argument(
        "-c",
        "--combine",
        action="store_true",
        help="Combine video sets into a single video file when output file already exists.",
    )
    overwrite_combine_group.add_argument(
        "-w",
        "--overwrite",
        action="store_true",
        help="Overwrite existing output file when output file already exists.",
    )
    args = parser.parse_args()

    # Print out all arguments.
    print("Arguments:")
    for key, value in vars(args).items():
        print("\t{}: {}".format(key.replace("_", " ").capitalize(), value))

    combine_option = (
        AutoCombiner.COMBINETYPE.OVERWRITE
        if args.overwrite
        else AutoCombiner.COMBINETYPE.COMBINE
        if args.combine
        else AutoCombiner.COMBINETYPE.SKIP
    )

    # Combine videos.
    auto_combiner = AutoCombiner()
    errors = auto_combiner.auto_combine_videos(
        args.input_folder,
        args.output_folder,
        args.input_regex,
        args.output_regex,
        args.output_file_template,
        args.reverse_order,
        args.dry_run,
        combine_option,
        args.verbose,
    )

    if errors:
        error_message = "Errors:\n\t" + "\n\t".join(errors)
        sys.exit(error_message)
