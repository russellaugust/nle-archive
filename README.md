# Archive NLE README.md

## Overview

`archive_nle` is a Python module used in film post-production environments for archiving final sequences. It facilitates the consolidation of media files referenced in AAF (for Avid), XML (for Premiere), or Premiere project files (`.prproj`) to a singular location, thereby enabling easy reconstruction of projects using the respective source file.

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

### Basic Command Shape

Run `archive_nle.py` with one or more source files and one destination:

```bash
python archive_nle.py -s /path/to/source.prproj -d /path/to/destination
```

After scanning the source file, the tool prints the total referenced media size and the media still left to copy. It then asks:

```text
Okay to proceed? Y / N:
```

Enter `Y` to copy media or create placeholders. Enter `N` to cancel.

### Normal Archive Mode

This is the default behavior for XML and PRPROJ sources. The tool copies media under `--destination` while preserving the source path structure as an archive tree.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup
```

Source media path found in the PRPROJ:

```text
/Volumes/jobs/movie/02_post/media/Import/_Block02/DPJ_20241217/EDIT_PACKAGE/Copied_DPJ_EDIT_12/014_DPJ_0100_v002.v001.mov
```

Destination path:

```text
/Volumes/nle_backup/jobs/movie/02_post/media/Import/_Block02/DPJ_20241217/EDIT_PACKAGE/Copied_DPJ_EDIT_12/014_DPJ_0100_v002.v001.mov
```

For `/Volumes/...` source paths, the archive path starts with the volume name. The literal `/Volumes` folder is not included.

Another source media path:

```text
/Users/user/Desktop/temp_media/card01/A001_C001.mov
```

Destination path:

```text
/Volumes/nle_backup/Users/user/Desktop/temp_media/card01/A001_C001.mov
```

### Active Storage Rewrite Mode

Use `--rewrite-root` when XML or PRPROJ media should be copied to a real active location instead of under the archive destination. This is useful when the media should live at a reconnectable production path such as LucidLink.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs
```

Source media path:

```text
/Volumes/jobs/movie/02_post/media/Import/_Block02/DPJ_20241217/EDIT_PACKAGE/Copied_DPJ_EDIT_12/014_DPJ_0100_v002.v001.mov
```

Destination path:

```text
/Volumes/company/jobs/movie/02_post/media/Import/_Block02/DPJ_20241217/EDIT_PACKAGE/Copied_DPJ_EDIT_12/014_DPJ_0100_v002.v001.mov
```

In plain language, the tool replaces this root:

```text
/Volumes/jobs
```

with this root:

```text
/Volumes/company/jobs
```

and leaves the rest of the media path unchanged.

`--rewrite-root` only matches full path parts. For example, this source path does not match `/Volumes/jobs`:

```text
/Volumes/jobs_backup/movie/02_post/media/A001_C001.mov
```

So it falls back to normal archive mode:

```text
/Volumes/nle_backup/jobs_backup/movie/02_post/media/A001_C001.mov
```

### Rewrite Fallback Behavior

If a media file does not live under the rewritten root, the tool still copies it using the normal archive structure under `--destination`.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs
```

Source media path:

```text
/Users/user/Desktop/pulled_from_editor/one_off_graphic.mov
```

Destination path:

```text
/Volumes/nle_backup/Users/user/Desktop/pulled_from_editor/one_off_graphic.mov
```

This lets project media from `/Volumes/jobs` move to the active storage path while one-off desktop, download, external drive, or other odd paths remain safely archived.

### Multiple Rewrite Roots

You can use `--rewrite-root` more than once. The first matching rule wins.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs \
  --rewrite-root /Volumes/assets /Volumes/company/assets
```

Example path results:

```text
/Volumes/jobs/movie/02_post/media/A.mov
-> /Volumes/company/jobs/movie/02_post/media/A.mov

/Volumes/assets/logos/client_logo.mov
-> /Volumes/company/assets/logos/client_logo.mov

/Volumes/shuttle_drive/card01/B.mov
-> /Volumes/nle_backup/shuttle_drive/card01/B.mov
```

### Multiple Source Files

You can pass multiple source files in one run as long as they all use the same format.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/episode_101.prproj /Users/user/projects/movie/edits/episode_102.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs
```

The tool combines the referenced media from both projects, removes duplicate paths, checks which destination files already exist, and copies only the missing files.

Mixed source formats are not supported in one run. For example, do not combine `.xml` and `.prproj` in the same command.

### Excluding Paths

Use `-e` or `--exclude_directories` to skip media under specific source path roots.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs \
  -e /Volumes/jobs/movie/02_post/vfx/tools /Volumes/jobs/movie/02_post/reference
```

Any referenced media under these roots is ignored:

```text
/Volumes/jobs/movie/02_post/vfx/tools
/Volumes/jobs/movie/02_post/reference
```

Other media is still copied normally or rewritten if it matches `--rewrite-root`.

### Placeholder Mode

Use `-p` or `--placeholder` to create the destination folder structure and empty placeholder files instead of copying full media.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/edits/movie_sequence.prproj \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs \
  -p
```

Source media path:

```text
/Volumes/jobs/movie/02_post/media/A001_C001.mov
```

Placeholder path:

```text
/Volumes/company/jobs/movie/02_post/media/A001_C001.mov
```

The file at the destination is empty, but the path and filename are created. Without `--rewrite-root`, placeholder files are created under the normal archive destination.

### AAF / Avid Behavior

AAF sources are treated differently because Avid media workflows are different. AAF copy mode is flat and directory-agnostic: it checks destination media by filename and copies missing files into a timestamped folder under `--destination`.

Command:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/aaf/movie_sequence.aaf \
  -d /Volumes/nle_backup
```

Example source media paths:

```text
/Volumes/jobs/movie/02_post/avid_media/Avid MediaFiles/MXF/USER.1/A010C318_221111I1_R5C1A.MXF
/Volumes/shuttle_drive/Avid MediaFiles/MXF/USER.2/A010C357_221111ZH_R5C1A.MXF
```

Example destination paths:

```text
/Volumes/nle_backup/260515143012/A010C318_221111I1_R5C1A.MXF
/Volumes/nle_backup/260515143012/A010C357_221111ZH_R5C1A.MXF
```

The timestamp folder is generated at runtime, so the exact number will be different.

`--rewrite-root` is not supported for AAF sources. This command will fail:

```bash
python archive_nle.py \
  -s /Users/user/projects/movie/aaf/movie_sequence.aaf \
  -d /Volumes/nle_backup \
  --rewrite-root /Volumes/jobs /Volumes/company/jobs
```

### Command-Line Arguments

The script supports the following command-line arguments:

- `-s, --source`: One or more source XML, AAF, or PRPROJ files (required). Mixed source types are not supported in the same run.
- `-d, --destination`: Destination path for media (required).
- `-e, --exclude_directories`: Space-separated list of paths to exclude from copying.
- `-p, --placeholder`: Create empty placeholder files at the destination instead of copying full media.
- `--rewrite-root OLD_ROOT NEW_ROOT`: For XML/PRPROJ sources, copy matching media paths under `NEW_ROOT` instead of the archive destination by replacing `OLD_ROOT` with `NEW_ROOT`. Both paths must be absolute, `NEW_ROOT` must already exist, and AAF sources do not support this option.

### Important Path Rules

- `--destination` must be an existing directory.
- `--rewrite-root OLD_ROOT NEW_ROOT` requires absolute paths.
- `NEW_ROOT` must be an existing directory.
- Rewrite mode applies only to XML and PRPROJ sources.
- If no rewrite rule matches a source media path, the existing archive behavior is used.
- Existing destination files are skipped.

## Future Improvements

- Implement verification of copied files, ensuring the destination files are the same size as their source counterparts. If discrepancies are found, recopy the files.
- Add a feature that cross-verifies source and destination files, providing users the option to delete destination files not present in the source to conserve storage space.
