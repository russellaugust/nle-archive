from typing import List
import os, math, argparse
from shutil import copy2
import search
from pathlib import Path
from datetime import datetime
import time

import logging

logging.basicConfig(filename="example.log", filemode="a", level=logging.DEBUG)

def log_file_operation(file_path: Path, operation: str):
    logging.debug(f"{operation}: {file_path}")

def convert_size(size_bytes: int):
    """Returns a string of the total file size, human readable."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def filenames_in_path(path: Path, extensions: List[str]):
    dst_files = set()
    for ext in extensions:
        dst_files.update(p.name for p in path.rglob(f"*.{ext}"))
    return dst_files


def uncopiedfiles_directoryagnostic(src_paths: List[Path], dst_path: Path) -> List[str]:
    # Get all files in the destination base path
    dst = filenames_in_path(dst_path, ["*"])

    # Ensure src_paths contains Path objects
    src_paths = [Path(src) for src in src_paths]

    # Go through source files, if any file names don't match, add to copy_list
    copy_list = []
    for src in src_paths:
        if src.name in dst:
            pass
        else:
            copy_list.append(src)
    return copy_list


def destination_path(src_file: Path, base_path: Path) -> Path:
    """Transforms the source path into a destination path."""
    relative_path = str(src_file).split("/Volumes/", 1)[-1]
    return base_path / Path(relative_path)


def file_exists(dst_file: Path) -> bool:
    """Checks if a file is copied to the destination."""
    return dst_file.exists()


def uncopied_files(src_files: List[Path], dst_path: Path) -> List[Path]:
    """Get a list of source files that have not been copied."""
    files_to_copy = [
        Path(src_path)
        for src_path in src_files
        if not file_exists(destination_path(src_path, dst_path))
    ]
    return files_to_copy

def ensure_folder_exists(folder: Path):
    """Creates folder if it doesn't exist."""
    folder.mkdir(parents=True, exist_ok=True)


def determine_destination(src: Path, base_dst: Path, flat: bool) -> Path:
    """Determine the destination path."""
    if flat:
        return base_dst / src.name
    return base_dst / src.relative_to("/Volumes")


def copy_file(src: Path, dst: Path, dry_run=False):
    """Copies file and creates necessary folders."""
    if dry_run:
        pass
    else:
        ensure_folder_exists(dst.parent)
        copy2(src, dst)


def copy_files_shutil(src_paths: List[Path], dst_path: Path, flat: bool = False):
    """Performs copy to new location."""
    # Revise the destination folder path if structure is flat
    date = datetime.now().strftime("%y%m%d%H%M%S")
    dst_path = dst_path / date if flat else dst_path

    for src in src_paths:
        dst = determine_destination(src, dst_path, flat)

        # skip files that already exist.
        if dst.exists():
            print("File exists, skipping.")
        else:
            print(f"copying from : {src}\ncopying to   : {dst}")

            try:
                copy_file(src, dst, dry_run=False)
            except Exception as e:
                with open("failed.log", "a") as f:
                    f.write(f"failed to write from: {src}\n")
                    f.write(f"failed to write from: {dst}\n")
                    f.write(f"why: {e}\n\n")


def dir_path(string):
    # Check if the path is a directory
    if Path(string).is_dir():
        return string
    else:
        export = "This is not a directory!  " + string
        raise NotADirectoryError(export)


def parse_arguments():
    # CLI interface

    parser = argparse.ArgumentParser(
        prog="archive aaf xml",
        description="Archive your project or sequence using an XML or AAF by discovering the media used and recreating the folder structure for reconnect. When using Premiere, dont forget to disabled your multicams (not flatten) if you want them included :)",
    )

    parser.add_argument(
        "-s",
        "--source",
        type=Path,
        required=True,
        help="XML or AAF file containing project that needs archiving.",
    )

    parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        required=True,
        help="path to the dailies to be replaced.",
    )

    parser.add_argument(
        "-e",
        "--exclude_directories",
        type=dir_path,
        nargs="*",
        help="paths to exclude from copy.",
    )

    args = parser.parse_args()

    if args.source.is_file() == False:
        parser.error("The source must be a file.")
    elif args.destination.is_dir() == False:
        parser.error("The destination must be a directory.")
    else:
        return parser.parse_args()


def ask_user_to_continue_or_exit(error: Exception):
    """Ask the user if they'd like to exit or continue."""
    while True:
        print(f"Error: {error}")
        response = input("Would you like to continue or exit? (C/E): ").strip().lower()
        if response == 'c':
            return True
        elif response == 'e':
            exit()
        else:
            print("Invalid input. Please enter 'C' to continue or 'E' to exit.")

def get_file_size_with_retry(file_path: str, retries: int = 3, delay: float = 1.0) -> int:
    """Get file size with retries to handle potential file system latency."""
    for attempt in range(retries):
        try:
            return os.path.getsize(file_path)
        except FileNotFoundError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print (f"{e}")
                return 0
    
    return 0  # Return 0 if all retries fail

def main():
    args = parse_arguments()

    source = args.source
    destination = args.destination
    ignore_paths = args.exclude_directories

    source_paths_to_process = []
    source_uncopied = []
    flat = False

    if source.suffix == ".xml":
        # source paths excluding ignored pathes
        source_paths_to_process = search.filepaths_from_xml(
            xml_path=source, ignore_paths=ignore_paths
        )

        # source paths of only files that need to be copied
        source_uncopied = uncopied_files(
            src_files=source_paths_to_process, dst_path=destination
        )

    elif source.suffix == ".aaf":
        # source paths excluding ignored pathes
        source_paths_to_process = search.filepaths_from_aaf(
            aaf_path=source, ignore_paths=ignore_paths
        )

        source_uncopied = uncopiedfiles_directoryagnostic(
            src_paths=source_paths_to_process, dst_path=destination
        )
        flat = True

    src_size_with_ignored = sum(
        [get_file_size_with_retry(str(src_file), 1, 0) for src_file in source_paths_to_process]
    )
    print("Total Media (excluding ignored paths):", convert_size(src_size_with_ignored))

    # print(source_uncopied)
    uncopied_size = sum([get_file_size_with_retry(str(src_file), 1, 0) for src_file in source_uncopied])

    # get total size of source files but exclude what's already been copied.
    print("Media Left to Copy:", convert_size(uncopied_size))

    ready = False
    while ready == False:
        name = input("Okay to proceed? Y / N: ")
        if name.lower() == "y":
            copy_files_shutil(
                src_paths=source_uncopied, dst_path=destination, flat=flat
            )
            ready = True
        elif name.lower() == "n":
            exit()

    # TODO add a section that goes back over and compares the source file against the destination file to make sure they are the same size.  If they are not, then it will copy the file again.  This will be useful for when the copy fails for some reason.
    # TODO add a section that goes back over and compares the source file against the destination files and allows the user to choose if they want to remove files on the destination not present in the source file, this is for storage purposes only.


if __name__ == "__main__":
    main()
