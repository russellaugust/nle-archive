# Archive NLE README.md

## Overview

`archive_nle` is a Python module used in film post-production environments for archiving final sequences. It facilitates the consolidation of media files referenced in AAF (for Avid) or XML (for Premiere) files to a singular location, thereby enabling easy reconstruction of projects using the respective AAF or XML files.

## Features

- **Size Conversion**: The `convert_size` function converts file sizes from bytes to a human-readable format.
  
- **File List Retrieval**: `filenames_in_path` retrieves the names of files in a specified path with given extensions.

- **Uncopied File Identification**: Functions `uncopied_files` and `uncopiedfiles_directoryagnostic` identify files that haven’t been copied to the destination directory.

- **Destination Path Determination**: `destination_path` converts a source path into a destination path.

- **File Existence Checking**: `file_exists` checks if a specified file exists in the destination directory.

- **Folder Existence Assurance**: `ensure_folder_exists` creates a folder if it doesn’t already exist.

- **Destination Determination**: `determine_destination` decides the destination path of a file.

- **File Copying**: `copy_file` and `copy_files_shutil` handle the copying of files and folder creation.

- **Directory Validation**: `dir_path` validates if a given string is a directory path.

- **Argument Parsing**: `parse_arguments` parses and validates command-line arguments.

## Usage

### Prerequisites

You'll need to `pip install pyaaf2` if you want to use the AAF archival.  

### Usage Example

1. **Command-Line Execution**: Run the `archive_nle` script with necessary command-line arguments:

    ```bash
    python archive_nle.py -s /path/to/source.xml -d /path/to/destination -e /path/to/exclude1 /path/to/exclude2
    ```
   
   - `-s` or `--source`: Required. The path to the source XML or AAF file.
   - `-d` or `--destination`: Required. The destination path for the copied media.
   - `-e` or `--exclude_directories`: Paths to be excluded from the copy process.

2. **Follow the Prompt**: You will be asked to confirm the operation. Respond with `Y` to proceed or `N` to cancel the operation.

### Command-Line Arguments

The script supports the following command-line arguments:

- `-s, --source`: Path to the source XML or AAF file (required).
- `-d, --destination`: Destination path for media (required).
- `-e, --exclude_directories`: Space-separated list of paths to exclude from copying.

## Future Improvements

- Implement verification of copied files, ensuring the destination files are the same size as their source counterparts. If discrepancies are found, recopy the files.
- Add a feature that cross-verifies source and destination files, providing users the option to delete destination files not present in the source to conserve storage space.