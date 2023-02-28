# Premiere XML Archiver

Tool for consolidating media from an XML file.

Primarily used for archiving a final project or creating a travel hard drive.

Can also utilize a .txt file containing paths to ignore so that only new files
not already existing on a drive will be collected, without requiring the drive
to be present on the system.  Exact file path matching is not required between
the two systesm for file inclusion/exclusion to be accurate (see directory 
padding in help).

The bash program "Tree" (separate install) can be used to generate such a .txt
file on the remote system where the drive to update exists.

# Generate Existing File List with Tree
```bash
tree -afi --noreport > ignore_files.txt
```

# Example CLI

```bash
python3 archive_premiere_xml.py \
-x '/Volumes/Devo1/Exports/Cuts Reels 1-4.xml' \
-d '/Volumes/Devo1/forCopy'
```


```bash
python3 archive_premiere_xml.py \
-x '/Users/admin/Desktop/sequence.xml' \
-d '/Volumes/EXTERNAL_02' \
-e "/Volumes/Media/Media/Media - Editorial/" \
"/Volumes/Media/Media/Media - Received/" \
"/Volumes/projects/"
```

```bash
python3 archive_premiere_xml.py \
-x '/Users/admin/Desktop/sequence.xml' \
-d '/Volumes/EXTERNAL_02' \
--exclude_directories "/Volumes/Media/Assist/" "/Volumes/Media/Media/Dailies/"
```
