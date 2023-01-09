from typing import List
import xml.etree.ElementTree as et
from urllib.parse import unquote
import os, math, argparse
from shutil import copy2

import read_paths_from_file as pathtools

import logging

logging.basicConfig(
    filename='example.log', 
    filemode='a',
    encoding='utf-8', 
    level=logging.DEBUG)

def convert_size(size_bytes):
    """ Returns a string of the total file size, human readable."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def filepaths_from_xml(xml_path: str, ignore_paths: List[str] = []) -> List[str]:
    """ Returns list of unique file paths from the Premiere XML. """
    
    ignore_paths = [] if ignore_paths is None else ignore_paths

    # get pathurls only
    parser = et.XMLParser(encoding='utf-8')
    xmlTree = et.parse(xml_path, parser)
    pathurls = xmlTree.findall('.//pathurl')
    
    src_files = []
    for pathurl in pathurls:
        unquoted_path = unquote(pathurl.text.split("file://localhost")[1])
        include=True
        if unquoted_path not in src_files:
            # print (ignore_paths)
            for ignore_path in ignore_paths:
                if unquoted_path.startswith(ignore_path):
                    include=False
            
        if include:
            src_files.append(unquoted_path)

    # del pathurls
    # del xmlTree

    return src_files


def uncopied_files(source_paths: List[str], destination_path: str) -> List[str]:
    """ get list of source files that have not been copied."""
    
    files_to_copy = []
    for src_file in source_paths:

        #[1:] is snipping off the / to conform to os.path.join rules
        dst_file = os.path.join(
            destination_path, 
            src_file.split('/Volumes/', 1)[1])
        if os.path.exists(dst_file):
            # if filecmp.cmp(src_file, dst_file):
            #     print('same')
                pass
        else:
            files_to_copy.append(src_file)
            
    return files_to_copy

def copy_files_with_full_path_shutil(source_paths: List[str], destination_path: str):
    """ Performs copy to new location. """
    
    for src_file in source_paths:

        #[1:] is snipping off the / to conform to os.path.join rules
        dst_file = os.path.join(
            destination_path, 
            src_file.split('/Volumes/', 1)[1])
        
        dst_folder = os.path.dirname(dst_file)
        
        # create the full path of folders if they don't exist
        if not os.path.exists(dst_folder):
            print("creating folder: ", dst_folder)
            os.makedirs(dst_folder)
            
        # skip files that already exist.
        if os.path.exists(dst_file):
            print("File exists, skipping.")
        else:
            # read out what's being copied
            print("copying from : ", src_file)
            print("copying to   : ", dst_file)
            logging.debug(dst_file)
            
            # perform the copy
            # copy(src_file, dst_file)
            copy2(src_file, dst_file)
            

def dir_path(string):
	# Checks if the path is a directory or not, just to confirm its real.	
	if os.path.isdir(string):
		return string
	else:
		export = "This is not a directory!  " + string
		raise NotADirectoryError(export)

def parse_arguments():
    # CLI interface

    parser = argparse.ArgumentParser(prog='archive xml', 
                                     description='Archive your project using an XML by discovering the media used and recreating the folder structure for reconnect. Dont forget to disabled your multicams (not flatten) if you want them included :)')
    
    parser.add_argument('-x', '--xml', 
                        type=open, 
                        required=True,
                        help='XML file containing project that needs archiving.')
    
    parser.add_argument('-d', '--destination', 
                        type=dir_path,
                        required=True, 
                        help='path to the dailies to be replaced.')

    parser.add_argument('-e', '--exclude_directories', 
                        type=dir_path, 
                        nargs='*',
                        help='paths to exclude from copy.')
    args = parser.parse_args()

    if args.xml and args.destination:
        xml_path		= args.xml
        destination 	= args.destination
        ignore_paths    = args.exclude_directories

        # all source paths
        # source_paths_all = filepaths_from_xml(
        #     xml_path=xml_path)
        # total_size = sum([os.path.getsize(src_file) for src_file in source_paths_all])
        # print ("XML Media Total:", convert_size(total_size))
        
        # source paths excluding ignored pathes
        source_paths_to_process = filepaths_from_xml(
            xml_path=xml_path,
            ignore_paths=ignore_paths)
        total_size_with_ignored = sum([os.path.getsize(src_file) for src_file in source_paths_to_process])
        print ("XML Media (excluding ignored paths):", convert_size(total_size_with_ignored))
        
        # source paths of of only files that need to be copied
        source_uncopied = uncopied_files(source_paths=source_paths_to_process,
                                         destination_path=destination)
        uncopied_size = sum([os.path.getsize(src_file) for src_file in source_uncopied])

        # get total size of source files but exclude what's already been copied.
        print ("XML Media Left to Copy:", convert_size(uncopied_size))
        
        ready = False
        while(ready == False):
            name = input("Okay to proceed? Y / N: ")
            if(name.lower() == "y"):
                copy_files_with_full_path_shutil(
                    source_paths=source_uncopied, 
                    destination_path=destination)
                ready = True
            elif(name.lower() == "n"):
                exit()

    else:
        parser.print_help()

if __name__== "__main__":
	parse_arguments()