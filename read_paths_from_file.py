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

def find_common_root(list_of_paths: list):
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


def testing():
    paths = read_paths_from_file('testing/MATZ_GS_media_as_of_221129.txt', ["./Assist/", "./zzAutosaves/", "./zzPremiere Scratch Disks/"])
    # for path in paths:
    #     print(path)
    print(f"# paths: {len(paths)}")

    common_parent = find_common_root(paths)
    print(f"Common Root Folder: {common_parent}")

    new_paths = conform_paths_to_new_root("/this/is/my/new/root/path/", paths)
    # for path in new_paths:
    #     print(path)
    print(f"# new paths: {len(new_paths)}")

    no_paths = remove_paths_from_filepaths(paths)
    # for path in no_paths:
    #     print(path)
    print(f"# no paths: {len(no_paths)}")

if __name__ == "__main__":
    testing()