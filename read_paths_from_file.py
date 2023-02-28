from typing import List
import os
import re

def read_paths_from_file(filepath: str, ignore_paths: List[str] = [], ignore_folders: bool = True) -> List[str]:
    '''
    Read in a list of filepaths from a text file

    Expects that each line in the file is a path formatted as a correct path
    Each line will be treated as a path regardless of its format
    
    :param filepath str:        Path to text file
    :param ignore_paths list:   list of string paths that will be ignored when reading from file
    :param ignore_folders bool: When True, only paths ending in a file extension
                                will be collected.  Folders are ignored.

    :return list_of_paths list: list of path strings found
    '''
    
    list_of_paths = []

    if os.path.exists(filepath):
        f = open(filepath, mode = 'r')

        count = 0
        for line in f.readlines():
            stripped_line = line.strip()

            # skip folders if appropriate to do so
            if (
                (ignore_folders and os.path.splitext(line.strip())[1] != '')
                or not ignore_folders
                ):
                # TODO this RegEx needs to be addressed/removed/abstracted
                # regex_corrected_line = re.sub(r'^./', '/Volumes/Media/Matz/', stripped_line)
                regex_corrected_line = stripped_line
                
                if not any(regex_corrected_line.startswith(path) for path in ignore_paths):
                    list_of_paths.append(regex_corrected_line)
                    count += 1

        f.close()

    else:
        raise FileNotFoundError(filepath)

    return list_of_paths

def remove_paths_from_filepaths(list_of_paths: List[str]) -> List[str]:
    '''
    Remove all paths from a list of filepaths, resulting in filenames only
    Any duplicate file names will be pruned from final list

    WARNING: any differentiatiation between unique files of the same name
    located in different folders will be lost. The resulting file names will
    be considered identical and only listed only once in the final returned
    list

    :param list_of_paths list:  list of file path strings

    :return: list of filenames extracted from the original list of paths, with
             no duplicates
    '''

    list_of_files = set()

    for path in list_of_paths:
        if os.path.splitext(path)[1] != '':
            list_of_files.add(os.path.split(path)[1])

    return list(list_of_files)

def find_common_root(list_of_paths: list) -> str:
    '''
    Given a list of filepaths, find a common root path among them

    :param list_of_paths list:  list of file path strings to parse
    
    :return parent_path str:   string of common parent path
    '''

    parent_path = ''

    if len(list_of_paths) > 0:
        parent_path = str(list_of_paths[0])

    for path in list_of_paths:
        while parent_path not in path and parent_path not in ['', '/', ' ']:
            parent_path = os.path.split(parent_path)[0]

    return parent_path

def conform_paths_to_new_root(new_root_path: str, list_of_paths: List[str], replace_common_root = True) -> List[str]:
    '''
    Add a new root path to all paths contained in a list of paths
    Default action is to first find the common root of all paths in the list, and
    then replace this common root with the new root path.

    :param new_root_path str:   the new root path to be prepended onto each path
    :param list_of_paths list:  list of paths strings to be modified
    :param replace_common_root bool:    True: common root is replaced in all paths with new root
                                        False: new root is prepended without any existing path modification
    
    :return: list of modified path strings
    '''
    
    conformed_paths_list = list_of_paths.copy()
    common_root = find_common_root(list_of_paths)
    
    for index, path in enumerate(conformed_paths_list):
        # remove common path first if appropriate to do so
        if replace_common_root:
            conformed_paths_list[index] = os.path.relpath(path, common_root)

        # prepend new root onto paths
        conformed_paths_list[index] = os.path.join(new_root_path, conformed_paths_list[index])
        
    return conformed_paths_list

def fix_premiere_path_dots(path: str) -> str:
    '''
    Takes a path that has Premieres /./ or /../ path bug and corrects the path string

    :param path str:    path string

    :return:    corrected path string
    '''

    processed_path = path

    # Remove instances of /./ in filepath
    if '/./' in processed_path:
        processed_path = processed_path.replace('/./', '/')

    # Remove instance of /../ and the previous folder referenced by .. in filepath
    if '/../' in processed_path:
        split_path = []
        
        while processed_path not in  ['', '/']:
            processed_path, folder = os.path.split(processed_path)
            split_path.append(folder)
        split_path.reverse()

        while '..' in split_path:
            dots_index = split_path.index('..')
            if dots_index < 1:
                # give up if .. are at the start of the path, as the folder
                # backwards one position to remove will not exist
                break
            else:
                split_path.pop(dots_index)
                split_path.pop(dots_index - 1)

        # preserve any path previx (likely /) remaining in processed path
        processed_path = processed_path + os.path.join(*split_path)
        

    return processed_path

def trim_path(path: str, pad: int = -1) -> str:
    '''
    Take any filepath and return the filename padded with X number of folders
    that precede the filename in the path.  For example, the filepath:

    this/is/my/path/to/my/file.txt

    with a pad of 2 would return:

    to/my/file.txt
    
    If the total number of folders in the file path is less than the requested
    pad, the entire file path will be returned.

    If pad is less than 0, the entire filepath will be returned.

    If pad is 0, only the filename is returned

    :param path str:    file path string
    :param pad int:     number of folders to include in pad

    :return str:    trimmed path string
    '''

    # Check correct values for arguments
    if not isinstance(path, str):
        raise ValueError(f"String expected. Received '{path}'.")
    
    try:
        if int(pad) != pad:
            raise ValueError()
    except:
        raise ValueError(f"Integer expected. Received '{pad}'.")
    
    split_path = path.split(os.sep)
    stop_index = len(split_path) - pad

    new_split_path = split_path[stop_index - 1 : len(split_path)]
    # if starting slice index is greater than ending slice index 
    if stop_index > len(split_path):
        new_split_path = split_path

    return (os.sep).join(new_split_path)
    


def testing():
    # When you gotta just try something right now
    pass



if __name__ == "__main__":
    testing()