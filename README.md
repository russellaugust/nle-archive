# Premiere XML Archiver

Tool for consolidating media from an XML file.  Primarily used for archiving a final project or creating a travel hard drive.

# Example CLI

```bash
python3 archive_premiere_xml.py \
-x '/Volumes/Devo1/Exports/Cuts Reels 1-7 Flattened.xml' \
-d '/Volumes/Devo1/forCopy'
```


```bash
python3 archive_premiere_xml.py \
-x '/Users/admin/Desktop/sequence.xml' \
-d '/Volumes/EXTERNAL_02' \
-e "/Volumes/Media/Media/Media - Editorial/" \
"/Volumes/Media/Media/Media - Received/" \
"/Volumes/matz-projects/"
```

```bash
python3 archive_premiere_xml.py \
-x '/Users/admin/Desktop/sequence.xml' \
-d '/Volumes/EXTERNAL_02' \
--exclude_directories "/Volumes/Media/Assist/zRussell" "/Volumes/Media/Media/Dailies - ProResHQ/"
```
