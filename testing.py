import archive_premiere_xml as arcxml

paths = arcxml.filepaths_from_xml("testing/20221129_All Reels_Offline Media_Mutlicams Enabled.xml", ['/Volumes/matz-projects/',])
for path in paths:
    print(path)
print(len(paths))
common_root = arcxml.pathtools.find_common_root(paths)
print(common_root)