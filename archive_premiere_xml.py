import xml.etree.ElementTree as et
from urllib.parse import unquote
import os, math, argparse
from shutil import copy

def convert_size(size_bytes):
    """ Returns a string of the total file size, human readable."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def filepaths_from_xml(xml_path) -> list:
    """ Returns a list of unique file paths contained in the Premiere XML. """
    
    # get pathurls only
    xmlTree = et.parse(xml_path)
    pathurls = xmlTree.findall('.//pathurl')

    # create a list of source files, removing the beginning of the path
    # fixing the escaped characters and deleting duplicates
    src_files = []
    [src_files.append(
        unquote(pathurl.text.split("file://localhost")[1]))
        for pathurl in pathurls 
        if pathurl.text not in src_files]

    return src_files

def copy_files_with_full_path(source_paths: list, destination_path: str) -> list:
    """ Returns the new location of the files. """
    
    for src_file in source_paths:

        #[1:] is snipping off the / to conform to os.path.join rules
        dst_file = os.path.join(destination_path, src_file[1:])
        dst_folder = os.path.dirname(dst_file)
        
        # create the full path of folders if they don't exist
        if not os.path.exists(dst_folder):
            print("creating: ", dst_folder)
            os.makedirs(dst_folder)

        # read out what's being copied
        print("copying from : ", src_file)
        print("copying to   : ", dst_file)
        
        # perform the copy
        copy(src_file, dst_file)

def dir_path(string):
	# Checks if the path is a directory or not, just to confirm its real.	
	if os.path.isdir(string):
		return string
	else:
		export = "This is not a directory!  " + string
		raise NotADirectoryError(export)

def parse_arguments():
    # terminal level interface for CLI

    parser = argparse.ArgumentParser(prog='archive xml', description='Archive your project using an XML by discovering the media used and recreating the folder structure for reconnect. Dont forget to disabled your multicams (not flatten) if you want them included :)')
    parser.add_argument('-x', '--xml', type=open, help='XML file containing project that needs archiving.')
    parser.add_argument('-d', '--destination', type=dir_path, help='path to the dailies to be replaced.')
    args = parser.parse_args()

    if args.xml and args.destination:
        xml_path		= args.xml
        destination 	= args.destination

        source_paths = filepaths_from_xml(xml_path)

        # tell the user the size of the copy.
        total_size = sum([os.path.getsize(src_file) for src_file in source_paths])
        print ("XML Media is:", convert_size(total_size))
        
        ready = False
        while(ready == False):
            name = input("Okay to proceed? Y / N: ")
            if(name.lower() == "y"):
                copy_files_with_full_path(
                    source_paths=source_paths, 
                    destination_path=destination)
                ready = True
            elif(name.lower() == "n"):
                exit()

    else:
        parser.print_help()

if __name__== "__main__":
	parse_arguments()