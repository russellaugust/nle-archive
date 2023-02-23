from typing import List
import xml.etree.ElementTree as et
from urllib.parse import unquote
import os, math, argparse
from shutil import copy2
import sys

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
    files_copied = 0
    files_skipped = 0
    indent = ' '*5

    for index, src_file in enumerate(source_paths):

        #[1:] is snipping off the / to conform to os.path.join rules
        dst_file = os.path.join(
            destination_path, 
            src_file.split('/Volumes/', 1)[1])
        
        dst_folder = os.path.dirname(dst_file)
        
        # create the full path of folders if they don't exist
        if not os.path.exists(dst_folder):
            print("\nCreating folder: ", dst_folder)
            os.makedirs(dst_folder)
            
        print(f"\n{index+1}/{len(source_paths)}    {src_file}")
        # skip files that already exist.
        if os.path.exists(dst_file):
            print(f"{indent}File exists, skipping.")
        else:
            if os.path.exists(src_file):
                # read out what's being copied
                print(f"{indent}copying from : ", src_file)
                print(f"{indent}copying to   : ", dst_file)
                
                # perform the copy
                # copy(src_file, dst_file)
                try:
                    copy2(src_file, dst_file)
                    files_copied += 1
                    #TODO need to actually do something with the logger
                    logging.debug(src_file)
                except Exception as e:
                    logging.debug(f"COPY FAILED: {src_file}  -  {e}")
                    print(f"{indent}!!! COPY FAILED!  FILE TRANSFER ERROR: {e}")
                    files_skipped += 1
            else:
                logging.debug(f"COPY SKIPPED: {src_file}")
                print(f"{indent}!!! COPY SKIPPED!  FILE DOES NOT EXIST: {src_file}")
                files_skipped += 1
    
    print(f"\n\n{files_copied} files copied.\n{files_skipped} files not copied.")


def dir_path(string):
	# Checks if the path is a directory or not, just to confirm its real.	
	if os.path.isdir(string):
		return string
	else:
		export = "This is not a directory!  " + string
		raise NotADirectoryError(export)

def is_string(string):
    # checks is argument is a string
    if isinstance(string, str):
        return string
    else:
        export = "This is not a string!  " + string
        raise ValueError(export)
    
def parse_arguments():
    # CLI interface

    parser = argparse.ArgumentParser(
                                formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                description='Archive your project using an XML by discovering the media used, copying it, and recreating the folder structure for a clean reconnect. Dont forget to disable your multicams (not flatten) if you want them included :)',
                            )
    
    parser.add_argument('-x', '--xml', 
                        type=open, 
                        required=True,
                        help='XML file containing project that needs archiving.')
    
    parser.add_argument('-d', '--destination', 
                        type=dir_path,
                        required=True,
                        help='Path to destination folder where copy will take place.')

    parser.add_argument('-e', '--exclude_directories',  
                        nargs='*',
                        default=[],
                        help='File paths to exclude from copy. Any filepath beginning with any excluded path(s) will be ignored.')

    parser.add_argument('-i', '--ignore_paths_from_file', 
                        default = '',
                        help='Path to text file containing filepaths to ignore.')
    
    parser.add_argument('-p', '--pad_filenames_with_dirs', 
                        type=int,
                        default=-1,
                        help='Trim XML filepaths down to filename plus X parent directories when comparing against an ignore paths file. Helps identify unique files to ignore, without requiring exactly filepath matches between XML and Ignore paths. If this option is not provided, full filepaths will be used. This option is ignored unless an ingore paths file is also provided.')

    parser.add_argument('--dry_run',
                        action='store_true',
                        help='Report how many files will be copied without actually copying any files.'
                    )

    args = parser.parse_args()

    if args.xml and args.destination:
        xml_path		= args.xml
        destination 	= args.destination
        ignore_paths    = args.exclude_directories
        ignore_txt_file = args.ignore_paths_from_file
        pad             = args.pad_filenames_with_dirs
        dry_run         = args.dry_run

        # all source paths
        # source_paths_all = filepaths_from_xml(
        #     xml_path=xml_path)
        # total_size = sum([os.path.getsize(src_file) for src_file in source_paths_all])
        # print ("XML Media Total:", convert_size(total_size))
        
        # source paths excluding ignored pathes
        source_paths_to_process = filepaths_from_xml(
            xml_path=xml_path,
            ignore_paths=ignore_paths)
        
        # Fix XML Paths /./ /../ Premiere issue
        for index, path in enumerate(source_paths_to_process):
            if '/./' in path or '/../' in path:
                source_paths_to_process[index] = pathtools.fix_premiere_path_dots(path)

        print(f"\nPaths found in XML: {len(source_paths_to_process)}")

        # process paths to ignore from txt file if provided
        # TODO add in CLI option for path replacement, filename only, or truncated path - file comparison options
        if ignore_txt_file != '':
            if os.path.exists(ignore_txt_file):

                txt_paths = pathtools.read_paths_from_file(ignore_txt_file, ignore_paths)
                print(f"\nPaths found in ignore text file: {len(txt_paths)}")

                # Builds list of [[original-xml-filepath, trimmed-padded-xml-filename], ...]
                # to be used for identifying which files to transfer/ignore
                xml_trimmed_paths = []
                for path in source_paths_to_process:
                    xml_trimmed_paths.append([path, pathtools.trim_path(path, pad)])
            
                # Build list (as sets) of files to transfer, and list of files NOT to transfer
                paths_to_transfer = set()
                paths_not_to_transfer = set()

                print("\nBuilding list of files to copy.  This may take some time...")
                count_msg = ''
                for index, path in enumerate(xml_trimmed_paths):
                    if index % 1 == 0:  # Change Mod to reduce speed hit for CLI refresh
                        # CLI FEEDBACK
                        sys.stdout.write('\b' * len(count_msg))
                        count_msg = f"{index}/{len(xml_trimmed_paths)}"
                        sys.stdout.write(count_msg)
                        sys.stdout.flush()

                    # Build Lists
                    omit_flag = False
                    for transferred_path in txt_paths:
                        if transferred_path.endswith(path[1]):
                            paths_not_to_transfer.add(path[0])
                            omit_flag = True
                            break

                    if not omit_flag:
                        paths_to_transfer.add(path[0])

                print(f"\n\nMedia Files to Transfer: {len(paths_to_transfer)}\nMedia Files to Omit During Transfer: {len(paths_not_to_transfer)}")

                source_paths_to_process = list(paths_to_transfer)
            else:
                print(f"\nText file of paths to skip was not found.  No paths will be skipped.")
        else:
            print(f"\nMedia Files to Transfer: {len(source_paths_to_process)}\nMedia Files to Omit During Transfer: None Provided by User")

        # Copy files if not dry run
        if not dry_run:
            # TODO size total for ALL and COPY ONLY media are redundant and waste time.  Can be combined into single pass with ifs

            # # CURRENTLY OMITTED TO NOT WAS TIME ON EXTRA CALCULATIONS OF THOUSANDS OF FILES
            # total_size_with_ignored = sum([os.path.getsize(src_file) for src_file in source_paths_to_process if os.path.exists(src_file)])
            # print("XML Media (including ignored paths):", convert_size(total_size_with_ignored))

            # source paths of of only files that need to be copied
            source_uncopied = uncopied_files(source_paths=source_paths_to_process,
                                            destination_path=destination)
            uncopied_size = sum([os.path.getsize(src_file) for src_file in source_uncopied if os.path.exists(src_file)])

            if len(source_paths_to_process) != len(source_uncopied):
                print((f"\nALERT! Some files to be copied were found to already exist in the target destination."
                       f"\n  Total number of files to copy: {len(source_paths_to_process)}"
                       f"\n  Files already existing in target location: {len(source_paths_to_process) - len(source_uncopied)}"
                       f"\n  Files remaining to copy: {len(source_uncopied)}"
                       "\nExisting files will not be recopied."
                       "\nIf this is incorrect, please clear the destinaton folder's contents or select a new destination."))

            # get total size of source files but exclude what's already been copied.
            print("\nXML Media Left to Copy:", convert_size(uncopied_size))
            
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
            print("\nDry Run Complete.  No files were copied.")

        print("\nDone!\n")

    else:
        parser.print_help()

if __name__== "__main__":
	parse_arguments()