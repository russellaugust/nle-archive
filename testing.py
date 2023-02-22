import archive_premiere_xml as arcxml

omit_xml_paths = [
                # '/Volumes/matz-projects/',
            ]

xml_paths = arcxml.filepaths_from_xml("testing/20230109_All_Reels.xml", omit_xml_paths)
# for path in paths:
#     print(path)
print(f"\nXML Paths: {len(xml_paths)}")
xml_common_root = arcxml.pathtools.find_common_root(xml_paths)
print(f"XML Media Common Root: {xml_common_root}")

# Fix XML Paths
for index, path in enumerate(xml_paths):
    if '/./' in path or '/../' in path:
        xml_paths[index] = arcxml.pathtools.fix_premiere_path_dots(path)

omit_txt_paths = [
                #'./Assist/',
                './zzAutosaves/',
                './zzPremiere Scratch Disks/'
            ]

txt_paths = arcxml.pathtools.read_paths_from_file("testing/MATZ_GS_media_as_of_221129.txt", omit_txt_paths)
print(f"\nTXT Paths: {len(txt_paths)}")
txt_common_root = arcxml.pathtools.find_common_root(txt_paths)
print(f"TXT Media Common Root: {txt_common_root}")


# # Builds exact filename match using common root replacement
# txt_paths = arcxml.pathtools.conform_paths_to_new_root(xml_common_root, txt_paths)
# new_txt_common_root = arcxml.pathtools.find_common_root(txt_paths)
# print(f"Updated TXT Media Common Root: {new_txt_common_root}")

# # Build list (as sets) of files to transfer, and list of files NOT to transfer
# paths_to_transfer = set()
# paths_not_to_transfer = set()

# for path in xml_paths:
#     if path in txt_paths:
#         paths_not_to_transfer.add(path)
#     else:
#         paths_to_transfer.add(path)

# Build a list of trimmed paths
xml_trimmed_paths = []
for path in xml_paths:
    xml_trimmed_paths.append([path, arcxml.pathtools.trim_path(path, 3)])

print(f"\nXML Trimmed Paths: {len(xml_trimmed_paths)}")

# Build list (as sets) of files to transfer, and list of files NOT to transfer
paths_to_transfer = set()
paths_not_to_transfer = set()

for path in xml_trimmed_paths:
    for transferred_path in txt_paths:
        if transferred_path.endswith(path[1]):
            paths_not_to_transfer.add(path[0])
            break
    else:
        paths_to_transfer.add(path[0])

print(f"\nMedia Files to Transfer: {len(paths_to_transfer)}\nMedia Files to Omit During Transfer: {len(paths_not_to_transfer)}")

new_list = list(paths_to_transfer)
new_list.sort()
f = open('testing/paths_to_write.txt', 'w')
for path in new_list:
    f.write(path + '\n')
f.close()