import os
import re

def read_paths_from_file(filepath: str, ignore_folders: bool = True) -> list:
    '''
    Read in a list of filepaths from a text file

    Expects that each line in the file is a path formatted as a correct path
    Each line will be treated as a path regardless of its format
    
    :param filepath str:        Path to text file
    :param ignore)folders bool: When True, only paths ending in a file extension
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
                
                list_of_paths.append(regex_corrected_line)
                count += 1

        f.close()

    else:
        raise FileNotFoundError(filepath)

    return list_of_paths

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





def testing():
    paths = read_paths_from_file('testing/MATZ_GS_media_as_of_221129.txt')
    for path in paths:
        print(path)
    
    common_parent = find_common_root(paths)
    print(f"\nCommon Root Folder: {common_parent}")

if __name__ == "__main__":
    testing()