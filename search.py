from typing import List, Optional
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
                file = unquoted_path_from_url(loc['URLString'].value)
                files.append(file)
    return files


def unquoted_path_from_url(url: str) -> str:
    """Extract the filesystem path from a file URL."""
    parsed_url = urlparse(url)
    return unquote(parsed_url.path)

def filter_ignored_paths(files: List[str], 
                         ignore_paths: List[str]) -> List[str]:
    """Filter out files that start with any of the ignore paths."""
    return [file for file in files 
            if not any(file.startswith(ignore_path) 
                       for ignore_path in ignore_paths)]

def extract_pathurls_from_xml(xml_path: str) -> List[str]:
    """Extract and return all pathurls from the XML."""
    parser = et.XMLParser(encoding='utf-8')
    xmlTree = et.parse(xml_path, parser)
    pathurls = xmlTree.findall('.//pathurl')
    return [unquoted_path_from_url(pathurl.text) for pathurl in pathurls]

def filepaths_from_xml(xml_path: str, 
                       ignore_paths: List[str] = None) -> List[str]:
    """Returns list of unique file paths from the Premiere XML."""
    ignore_paths = ignore_paths or []

    src_files = extract_pathurls_from_xml(xml_path)
    filtered_files = filter_ignored_paths(src_files, ignore_paths)
    
    return list(set(filtered_files))