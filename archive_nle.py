from typing import List, Sequence, Union
import os, math, argparse
import sys
from shutil import copy2
import search
from pathlib import Path
from datetime import datetime
import time

import logging

logging.basicConfig(filename="example.log", filemode="a", level=logging.DEBUG)

SUPPORTED_SOURCE_SUFFIXES = {".xml", ".aaf", ".prproj"}

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


def uncopiedfiles_directoryagnostic(src_paths: Sequence[Union[Path, str]], dst_path: Path) -> List[Path]:
    # Get all files in the destination base path
    dst = filenames_in_path(dst_path, ["*"])

    # Ensure src_paths contains Path objects
    source_paths = [Path(src) for src in src_paths]

    # Go through source files, if any file names don't match, add to copy_list
    copy_list: List[Path] = []
    for src in source_paths:
        if src.name in dst:
            pass
        else:
            copy_list.append(src)
    return copy_list


def make_archive_relative(src_file: Path) -> Path:
    """Strip the root prefix from an absolute path for archive mirroring.

    /Volumes/DriveA/foo  -> DriveA/foo
    /Users/russell/foo   -> Users/russell/foo
    """
    parts = src_file.parts
    # Skip the filesystem root ("/") and, for /Volumes paths, also skip
    # the "Volumes" mount-point directory so the drive name comes first.
    if len(parts) > 2 and parts[1] == "Volumes":
        return Path(*parts[2:])
    if len(parts) > 1:
        return Path(*parts[1:])
    return Path(src_file.name)


def destination_path(src_file: Path, base_path: Path) -> Path:
    """Transforms the source path into a destination path."""
    return base_path / make_archive_relative(src_file)


def file_exists(dst_file: Path) -> bool:
    """Checks if a file is copied to the destination."""
    return dst_file.exists()


def uncopied_files(src_files: Sequence[Union[Path, str]], dst_path: Path) -> List[Path]:
    """Get a list of source files that have not been copied."""
    files_to_copy = [
        Path(src_path)
        for src_path in src_files
        if not file_exists(destination_path(Path(src_path), dst_path))
    ]
    return files_to_copy

def ensure_folder_exists(folder: Path):
    """Creates folder if it doesn't exist."""
    folder.mkdir(parents=True, exist_ok=True)


def determine_destination(src: Path, base_dst: Path, flat: bool) -> Path:
    """Determine the destination path."""
    if flat:
        return base_dst / src.name
    return base_dst / make_archive_relative(src)


def copy_file(src: Path, dst: Path, placeholder: bool = False):
    """Copies file or creates a placeholder file at destination."""
    ensure_folder_exists(dst.parent)
    if placeholder:
        dst.touch(exist_ok=True)
        return
    copy2(src, dst)


def copy_files_shutil(
    src_paths: Sequence[Union[Path, str]],
    dst_path: Path,
    flat: bool = False,
    placeholder: bool = False,
):
    """Performs copy to new location."""
    # Revise the destination folder path if structure is flat
    date = datetime.now().strftime("%y%m%d%H%M%S")
    dst_path = dst_path / date if flat else dst_path

    for src in src_paths:
        src = Path(src)
        dst = determine_destination(src, dst_path, flat)

        # skip files that already exist.
        if dst.exists():
            print("File exists, skipping.")
        else:
            if placeholder:
                print(f"creating placeholder from : {src}\ncreating placeholder at   : {dst}")
            else:
                print(f"copying from : {src}\ncopying to   : {dst}")

            try:
                copy_file(src, dst, placeholder=placeholder)
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


def source_suffixes(sources: Sequence[Union[Path, str]]) -> set[str]:
    return {Path(source).suffix.lower() for source in sources}


def validate_source_file_types(sources: Sequence[Union[Path, str]]) -> str:
    suffixes = source_suffixes(sources)
    unsupported_suffixes = sorted(
        suffix for suffix in suffixes if suffix not in SUPPORTED_SOURCE_SUFFIXES
    )

    if unsupported_suffixes:
        supported_suffixes = ", ".join(sorted(SUPPORTED_SOURCE_SUFFIXES))
        raise ValueError(
            f"Unsupported source format(s): {', '.join(unsupported_suffixes)}. "
            f"Use only {supported_suffixes}."
        )

    if len(suffixes) != 1:
        supported_suffixes = ", ".join(sorted(SUPPORTED_SOURCE_SUFFIXES))
        raise ValueError(
            "All source files must use the same format. "
            f"Use only one of: {supported_suffixes}."
        )

    return next(iter(suffixes))


def unique_source_paths(paths: Sequence[Union[Path, str]]) -> List[Path]:
    unique_paths: List[Path] = []
    seen_paths = set()

    for path in paths:
        normalized_path = Path(path)
        path_key = str(normalized_path)
        if path_key in seen_paths:
            continue
        seen_paths.add(path_key)
        unique_paths.append(normalized_path)

    return unique_paths


def extract_source_media_paths(
    source: Path,
    ignore_paths: Union[Sequence[str], None],
) -> List[Path]:
    source_suffix = source.suffix.lower()
    ignore_paths_list = list(ignore_paths) if ignore_paths is not None else None

    if source_suffix == ".xml":
        extracted_paths = search.filepaths_from_xml(
            xml_path=str(source), ignore_paths=ignore_paths_list
        )
    elif source_suffix == ".aaf":
        extracted_paths = search.filepaths_from_aaf(
            aaf_path=str(source), ignore_paths=ignore_paths_list
        )
    elif source_suffix == ".prproj":
        extracted_paths = search.filepaths_from_prproj(
            prproj_path=source, ignore_paths=ignore_paths_list
        )
    else:
        raise ValueError(
            "Unsupported source format. Use .xml, .aaf, or .prproj."
        )

    return [Path(path) for path in extracted_paths]


def collect_source_media_paths(
    sources: Sequence[Path],
    ignore_paths: Union[Sequence[str], None],
) -> tuple[str, List[Path]]:
    source_suffix = validate_source_file_types(sources)

    combined_paths: List[Path] = []
    for source in sources:
        combined_paths.extend(extract_source_media_paths(source, ignore_paths))

    return source_suffix, unique_source_paths(combined_paths)


def parse_arguments():
    # CLI interface

    parser = argparse.ArgumentParser(
        prog="archive aaf xml",
        description=(
            "Archive your project or sequence using XML, AAF, or PRPROJ sources by "
            "discovering used media and recreating the folder structure for reconnect. "
            "When using Premiere XML/PRPROJ, remember to disable multicams (not flatten) "
            "if you want them included :)"
        ),
    )

    parser.add_argument(
        "-s",
        "--source",
        type=Path,
        nargs="+",
        action="append",
        required=True,
        help=(
            "One or more XML, AAF, or PRPROJ files containing project media "
            "references. All source files must use the same format."
        ),
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

    parser.add_argument(
        "-p",
        "--placeholder",
        action="store_true",
        help="create destination structure with placeholder files instead of copying media.",
    )

    args = parser.parse_args()

    args.source = [source for source_group in args.source for source in source_group]

    if any(source.is_file() == False for source in args.source):
        parser.error("Every source must be a file.")
    elif args.destination.is_dir() == False:
        parser.error("The destination must be a directory.")
    else:
        try:
            validate_source_file_types(args.source)
        except ValueError as error:
            parser.error(str(error))

        return args


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

    sources = args.source
    destination = args.destination
    ignore_paths = args.exclude_directories
    placeholder = args.placeholder

    source_paths_to_process = []
    source_uncopied = []
    flat = False

    try:
        source_suffix, source_paths_to_process = collect_source_media_paths(
            sources=sources,
            ignore_paths=ignore_paths,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return

    if source_suffix == ".aaf":
        source_uncopied = uncopiedfiles_directoryagnostic(
            src_paths=source_paths_to_process, dst_path=destination
        )
        flat = True
    else:
        source_uncopied = uncopied_files(
            src_files=source_paths_to_process, dst_path=destination
        )

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
                src_paths=source_uncopied,
                dst_path=destination,
                flat=flat,
                placeholder=placeholder,
            )
            ready = True
        elif name.lower() == "n":
            exit()

    # TODO add a section that goes back over and compares the source file against the destination file to make sure they are the same size.  If they are not, then it will copy the file again.  This will be useful for when the copy fails for some reason.
    # TODO add a section that goes back over and compares the source file against the destination files and allows the user to choose if they want to remove files on the destination not present in the source file, this is for storage purposes only.


if __name__ == "__main__":
    main()
