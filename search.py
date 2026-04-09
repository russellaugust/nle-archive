from typing import List, Optional
import gzip
import html
import io
import ntpath
import posixpath
from pathlib import Path
import re
import warnings
import xml.etree.ElementTree as et
from urllib.parse import unquote, urlparse

GZIP_MAGIC = b"\x1f\x8b"
WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
WINDOWS_DRIVE_URL_PATH_PATTERN = re.compile(r"^/[A-Za-z]:[\\/]")
PREMIERE_PATH_TAGS = ("FilePath", "ActualMediaFilePath", "pathurl")
PREMIERE_OPEN_TAGS = {tag: f"<{tag}>" for tag in PREMIERE_PATH_TAGS}
PREMIERE_CLOSE_TAGS = {tag: f"</{tag}>" for tag in PREMIERE_PATH_TAGS}
PREMIERE_MAX_OPEN_TAG_LEN = max(len(tag) for tag in PREMIERE_OPEN_TAGS.values())

# TODO DELETE THIS WHEN ITS CONFIRMED TO NOT BE NECESSARY
# def filepaths_from_aaf(aaf_path: str, ignore_paths: List[str] = []) -> List[str]:
#     """ Returns list of unique file paths from an Avid AAF. """
    
#     # Import here just so we don't have to install aaf2 if we don't need it
#     import aaf2
    
#     ignore_paths = [] if ignore_paths is None else ignore_paths
    
#     files = []
#     # get list of unique paths from AAF    
#     with aaf2.open(aaf_path, 'r') as f:
#         for mob in f.content.sourcemobs():
#             for loc in mob.descriptor.locator:
#                 file = loc['URLString'].value
#                 files.append(file)
#         files = set(files)

#     # check if any of the files are part of the ignore_paths
#     src_files = []
#     for file in files:  
#         include=True
#         for ignore_path in ignore_paths:
#             if file.startswith(ignore_path):
#                 include=False
#         if include:
#             src_files.append(file)

#     return src_files

def filepaths_from_aaf(aaf_path: str, ignore_paths: Optional[List[str]] = None) -> List[str]:
    """Returns list of unique file paths from an Avid AAF."""
    ignore_paths = ignore_paths or []
    
    src_files = extract_files_from_aaf(aaf_path)
    filtered_files = filter_ignored_paths(src_files, ignore_paths)

    return list(set(filtered_files))

def extract_files_from_aaf(aaf_path: str) -> List[str]:
    """Extract and return all file paths from the AAF."""

    import aaf2

    with aaf2.open(aaf_path, 'r') as f:
        files = []
        for mob in f.content.sourcemobs():
            for loc in mob.descriptor.locator:
                # Use the updated function
                file = unquoted_path_from_url(loc['URLString'].value)
                files.append(file)
    return files


def unquoted_path_from_url(url: str) -> str:
    """Extract the filesystem path from a file URL and ensure it starts with /Volumes."""
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)

    if WINDOWS_DRIVE_URL_PATH_PATTERN.match(path):
        return path[1:]

    if parsed_url.netloc and parsed_url.netloc.lower() not in {"", "localhost"}:
        return f"//{parsed_url.netloc}{path}"

    # Ensure the path starts with /Volumes
    if not path.startswith('/Volumes/'):
        path = '/Volumes' + path

    return path

def filter_ignored_paths(files: List[str], 
                         ignore_paths: List[str]) -> List[str]:
    """Filter out files that start with any of the ignore paths."""
    return [file for file in files 
            if not any(file.startswith(ignore_path) 
                       for ignore_path in ignore_paths)]

def extract_pathurls_from_malformed_xml(xml_path: str) -> List[str]:
    """Best-effort extraction of pathurl values from malformed XML content."""
    start_tag = "<pathurl>"
    end_tag = "</pathurl>"

    extracted_paths = []
    collecting = False
    current_value = ""

    with open(xml_path, "r", encoding="utf-8", errors="ignore") as xml_file:
        for line in xml_file:
            cursor = 0

            while cursor < len(line):
                if collecting:
                    end_index = line.find(end_tag, cursor)
                    if end_index == -1:
                        current_value += line[cursor:]
                        break

                    current_value += line[cursor:end_index]
                    value = current_value.strip()
                    if value:
                        extracted_paths.append(unquoted_path_from_url(value))

                    current_value = ""
                    collecting = False
                    cursor = end_index + len(end_tag)
                    continue

                start_index = line.find(start_tag, cursor)
                if start_index == -1:
                    break

                value_start = start_index + len(start_tag)
                end_index = line.find(end_tag, value_start)

                if end_index == -1:
                    collecting = True
                    current_value = line[value_start:]
                    break

                value = line[value_start:end_index].strip()
                if value:
                    extracted_paths.append(unquoted_path_from_url(value))

                cursor = end_index + len(end_tag)

    return extracted_paths


def is_gzip_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(2) == GZIP_MAGIC
    except OSError:
        return False


def open_project_reader(path: Path):
    if is_gzip_file(path):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore", newline=""), True
    return path.open("r", encoding="utf-8", errors="ignore", newline=""), False


def decode_xml_entities(path_value: str) -> str:
    return html.unescape(path_value)


def normalize_lookup_path(path_value: str) -> str:
    value = decode_xml_entities(path_value).strip()
    if not value:
        return ""

    parsed_url = urlparse(value)
    if parsed_url.scheme and parsed_url.scheme.lower() != "file":
        return ""
    if parsed_url.scheme.lower() == "file":
        value = unquoted_path_from_url(value)

    if WINDOWS_DRIVE_PATTERN.match(value) or "\\" in value:
        return ntpath.normpath(value)
    return posixpath.normpath(value)


def _find_next_premiere_tag_start(buffer: str, start: int) -> tuple[int, str] | None:
    best_index = -1
    best_tag = ""
    for tag, open_tag in PREMIERE_OPEN_TAGS.items():
        index = buffer.find(open_tag, start)
        if index == -1:
            continue
        if best_index == -1 or index < best_index:
            best_index = index
            best_tag = tag

    if best_index == -1:
        return None
    return best_index, best_tag


def extract_premiere_paths_streaming(reader: io.TextIOBase, chunk_size: int = 4 * 1024 * 1024) -> List[str]:
    values: List[str] = []
    buffer = ""

    while True:
        chunk = reader.read(chunk_size)
        is_final = chunk == ""
        if not is_final:
            buffer += chunk

        search_pos = 0
        while True:
            next_tag = _find_next_premiere_tag_start(buffer, search_pos)
            if next_tag is None:
                if is_final:
                    buffer = ""
                else:
                    flush_upto = max(search_pos, len(buffer) - (PREMIERE_MAX_OPEN_TAG_LEN - 1))
                    buffer = buffer[flush_upto:]
                break

            tag_start, tag_name = next_tag
            open_tag = PREMIERE_OPEN_TAGS[tag_name]
            close_tag = PREMIERE_CLOSE_TAGS[tag_name]

            value_start = tag_start + len(open_tag)
            close_start = buffer.find(close_tag, value_start)
            if close_start == -1:
                if is_final:
                    buffer = ""
                else:
                    buffer = buffer[tag_start:]
                break

            value = buffer[value_start:close_start].strip()
            if value:
                values.append(value)

            search_pos = close_start + len(close_tag)

        if is_final:
            break

    return values


def extract_premiere_paths_from_malformed_project(project_path: Path) -> List[str]:
    with open_project_reader(project_path)[0] as reader:
        return extract_premiere_paths_streaming(reader)


def extract_premiere_paths_from_project(project_path: Path) -> List[str]:
    extracted_paths: List[str] = []
    try:
        reader, _ = open_project_reader(project_path)
        with reader:
            for _, elem in et.iterparse(reader, events=("end",)):
                tag_name = elem.tag.rsplit("}", 1)[-1]
                if tag_name in PREMIERE_PATH_TAGS and elem.text:
                    extracted_paths.append(elem.text.strip())
                elem.clear()
    except et.ParseError as error:
        warnings.warn(
            (
                f"Project parse failed ({error}). "
                "Falling back to best-effort Premiere path extraction."
            ),
            RuntimeWarning,
        )
        return extract_premiere_paths_from_malformed_project(project_path)

    return extracted_paths


def filepaths_from_prproj(prproj_path: str | Path,
                          ignore_paths: Optional[List[str]] = None) -> List[str]:
    """Returns list of unique file paths from a Premiere .prproj file."""
    ignore_paths = ignore_paths or []

    try:
        raw_paths = extract_premiere_paths_from_project(Path(prproj_path))
    except OSError as error:
        warnings.warn(f"Failed reading Premiere project ({error}).", RuntimeWarning)
        return []

    normalized_paths = [normalize_lookup_path(path_value) for path_value in raw_paths]
    normalized_paths = [path for path in normalized_paths if path]
    filtered_files = filter_ignored_paths(normalized_paths, ignore_paths)

    return list(set(filtered_files))

def extract_pathurls_from_xml(xml_path: str) -> List[str]:
    """Extract and return all pathurls from the XML."""
    parser = et.XMLParser(encoding='utf-8')
    try:
        xmlTree = et.parse(xml_path, parser)
        pathurls = xmlTree.findall('.//pathurl')
        return [unquoted_path_from_url(pathurl.text) for pathurl in pathurls if pathurl.text]
    except et.ParseError as error:
        warnings.warn(
            f"XML parse failed ({error}). Falling back to best-effort pathurl extraction.",
            RuntimeWarning,
        )
        return extract_pathurls_from_malformed_xml(xml_path)

def filepaths_from_xml(xml_path: str, 
                       ignore_paths: Optional[List[str]] = None) -> List[str]:
    """Returns list of unique file paths from the Premiere XML."""
    ignore_paths = ignore_paths or []

    src_files = extract_pathurls_from_xml(xml_path)
    filtered_files = filter_ignored_paths(src_files, ignore_paths)
    
    return list(set(filtered_files))