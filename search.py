from typing import List, Optional
import warnings
import xml.etree.ElementTree as et
from urllib.parse import unquote, urlparse

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