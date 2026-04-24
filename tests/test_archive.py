import archive_nle as a
import search as s
import unittest, pytest
import gzip
from pathlib import Path
from typing import List
from unittest.mock import patch
    
def test_convert_size():
    assert a.convert_size(100000000000) == '93.13 GB'
    assert a.convert_size(10000000000000) == '9.09 TB'
    
def test_dir_path():
    with patch('archive_nle.Path.is_dir', return_value=True):
        assert a.dir_path('/Volumes/raid/') == '/Volumes/raid/'

    with patch('archive_nle.Path.is_dir', return_value=False):
        with pytest.raises(NotADirectoryError):
            a.dir_path('/Volumes/raid/')
    
def test_parse_arguments_input_variables_are_cast_accurately():
    # Mock the command-line arguments
    with patch('sys.argv', ['archive aaf xml', '-s', 'some_source.xml', '-d', '/some/destination', '-e', '/path/to/exclude1', '/path/to/exclude2']), \
         patch('archive_nle.Path.is_file', return_value=True), \
         patch('archive_nle.Path.is_dir', return_value=True):
             
             args = a.parse_arguments()
             
             assert args.source == [Path('some_source.xml')]
             assert args.destination == Path('/some/destination')
             assert '/path/to/exclude1' in args.exclude_directories
             assert '/path/to/exclude2' in args.exclude_directories


def test_parse_arguments_accepts_multiple_sources_of_same_type():
    with patch('sys.argv', ['archive aaf xml', '-s', 'one.xml', 'two.xml', '-d', '/some/destination']), \
         patch('archive_nle.Path.is_file', return_value=True), \
         patch('archive_nle.Path.is_dir', return_value=True):

             args = a.parse_arguments()

             assert args.source == [Path('one.xml'), Path('two.xml')]


def test_parse_arguments_rejects_mixed_source_types():
    with patch('sys.argv', ['archive aaf xml', '-s', 'one.xml', 'two.prproj', '-d', '/some/destination']), \
         patch('archive_nle.Path.is_file', return_value=True), \
         patch('archive_nle.Path.is_dir', return_value=True), \
         pytest.raises(SystemExit):
             a.parse_arguments()

def test_parse_arguments_invalid_directory():
    # Mock the command-line arguments
    with patch('sys.argv', ['prog_name', '-s', 'some_source.xml', '-d', '/nonexistent/destination']), \
         patch('archive_nle.Path.is_file', return_value=False), \
         patch('archive_nle.Path.is_dir', return_value=True), \
         pytest.raises(SystemExit):
             a.parse_arguments()
             
def test_get_destination_path():
    x = a.destination_path(Path('/Volumes/raid1/dailies/test.mov'), 
                           Path('/Volumes/raid2/'))
    assert x == Path('/Volumes/raid2/raid1/dailies/test.mov')
    
def test_is_file_copied_not():
    assert a.file_exists(Path('/Volumes/raid1/dailies/test.mov')) == False
    
def test_uncopied_files():
    
    with patch('archive_nle.file_exists', return_value=True):

        srcs = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
        uncopied_files = a.uncopied_files(srcs, Path('/Volumes/raid2/'))
        compare = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
    
        assert uncopied_files != compare
        
    with patch('archive_nle.file_exists', return_value=False):

        srcs = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
        uncopied_files = a.uncopied_files(srcs, Path('/Volumes/raid2/'))
        compare = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
    
        assert uncopied_files == compare
        
    
def test_get_filelist(tmp_path: Path):

    # Step 1: Setup
    extensions = ['mxf', 'wav','MXF', 'WAV']
    files = [
        # tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "msFMID.pmr",
        # tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "msmMMOB.mdb",
        tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C318_221111I1_R5C1A.MXF",
        tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C355_221111ZH_R5C1A.MXF",
        # tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "msFMID.pmr",
        # tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "msmMMOB.mdb",
        tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "A010C356_221111ZH_R5C1A.MXF",
        tmp_path / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "A010C357_221111ZH_R5C1A.MXF",
        tmp_path / "OMFI MediaFiles" / "RUSSELL.1" / "A010C318_221111I1_R5C1A.WAV",
    ]

    # Creating files
    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()

    expected_files = {f.name for f in files}

    # Step 2: Invoke
    result_files = a.filenames_in_path(tmp_path, extensions)

    # Step 3: Assert
    assert expected_files == result_files

def test_uncopiedfiles_directoryagnostic(tmp_path: Path):
    # TODO This test really should compare output better, its just checking to
    # confirm its a list. 

    src_base = tmp_path / "Raid1"
    # Step 1: Setup
    src_paths = [
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "msFMID.pmr",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "msmMMOB.mdb",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C318_221111I1_R5C1A.MXF",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C355_221111ZH_R5C1A.MXF",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "msFMID.pmr",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "msmMMOB.mdb",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "A010C356_221111ZH_R5C1A.MXF",
        src_base / "Avid MediaFiles" / "MXF" / "RUSSELL.2" / "A010C357_221111ZH_R5C1A.MXF",
        src_base / "OMFI MediaFiles" / "RUSSELL.1" / "A010C318_221111I1_R5C1A.WAV",
    ]
    
    dst_base = tmp_path / "Raid2"
    dst_paths = [
        dst_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C318_221111I1_R5C1A.MXF",
        dst_base / "Avid MediaFiles" / "MXF" / "RUSSELL.1" / "A010C355_221111ZH_R5C1A.MXF",
    ]

    # Creating source files
    for file in src_paths:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    # Creating destination files
    for file in dst_paths:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()

    expected_files = {f.name for f in src_paths}

    # Step 2: Invoke
    result_files = a.uncopiedfiles_directoryagnostic(src_paths, dst_base)

    # Step 3: Assert
    assert isinstance(result_files, list)
    
def test_path_from_url():
    source = 'file://localhost/Volumes/Media/MyProject/Media/Media%20-%20Editorial/Leaders/Premiere/2pop_24fps_MyProject.mov'
    dest = '/Volumes/Media/MyProject/Media/Media - Editorial/Leaders/Premiere/2pop_24fps_MyProject.mov'
    result_path_from_url = s.unquoted_path_from_url(source)
    assert result_path_from_url == dest

def test_extract_pathurls_from_xml_passes():
    result = s.extract_pathurls_from_xml('tests/xmls/TEST_230918.xml')
    assert isinstance(result, list)

def test_extract_pathurls_from_malformed_xml_fallback(tmp_path: Path):
        malformed_xml = tmp_path / "malformed.xml"
        malformed_xml.write_text(
                """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xmeml>
    <sequence>
        <pathurl>file://localhost/Volumes/Media/Test/A%20Clip.mov</pathurl>
        <broken>
    </sequence>
</xmeml>
""",
                encoding="utf-8",
        )

        result = s.extract_pathurls_from_xml(str(malformed_xml))

        assert isinstance(result, list)
        assert "/Volumes/Media/Test/A Clip.mov" in result
    
def test_filter_ignored_paths():
    src_files = s.extract_pathurls_from_xml('tests/xmls/TEST_230918.xml')
    ignore_paths = ['/Volumes/Media/Matz/Media/Dailies - ProResHQ/',
                    '/Volumes/Media/Matz/Media/Media - Received/Sound/Mixes']
    result = s.filter_ignored_paths(src_files, ignore_paths)
    assert all(ignore_path not in result for ignore_path in ignore_paths)
    
def test_ensure_folder_exists(tmp_path: Path):
    folder = tmp_path / "Volumes" / "Media" / "MyProject" / "Media" / "Dailies - ProResHQ"
    a.ensure_folder_exists(folder)
    assert folder.exists()
    
def test_determine_destination_flat(tmp_path: Path):
    src_file = Path('/Volumes/Media/MyProject/Media/Media - Editorial/Leaders/Premiere/2pop_24fps_MyProject.mov')
    dst_path = tmp_path / 'Test' / '20230503010203'
    result = a.determine_destination(src_file, dst_path, True)
    assert isinstance(result, Path)
    assert result.name.endswith('2pop_24fps_MyProject.mov')

def test_determine_destination_heiarchy(tmp_path: Path):
    src_file = Path('/Volumes/Media/MyProject/Media/Media - Editorial/Leaders/Premiere/2pop_24fps_MyProject.mov')
    dst_path = tmp_path / 'Test' / '20230503010203'
    result = a.determine_destination(src_file, dst_path, False)
    assert isinstance(result, Path)
    assert result.name.endswith('2pop_24fps_MyProject.mov')
    
def test_copy_files_shutil():
    assert 1 == 1


def test_is_gzip_file_detects_prproj_fixture():
    prproj_path = Path("tests/prproj/SHORT_SEQUENCE_FOR_FILEPATH_ANALYSIS.prproj")
    assert s.is_gzip_file(prproj_path) is True


def test_filepaths_from_prproj_has_strong_overlap_with_xml_fixture():
    prproj_path = Path("tests/prproj/SHORT_SEQUENCE_FOR_FILEPATH_ANALYSIS.prproj")
    xml_path = Path("tests/prproj/SHORT_SEQUENCE_FOR_FILEPATH_ANALYSIS.xml")

    prproj_paths = set(s.filepaths_from_prproj(prproj_path))
    xml_paths = set(s.filepaths_from_xml(str(xml_path)))

    assert len(prproj_paths) > 0
    overlap = prproj_paths & xml_paths
    overlap_ratio = len(overlap) / len(prproj_paths)
    assert overlap_ratio >= 0.8


def test_filepaths_from_prproj_ignore_paths_filtering():
    prproj_path = Path("tests/prproj/SHORT_SEQUENCE_FOR_FILEPATH_ANALYSIS.prproj")
    ignored_prefix = "/Volumes/jobs/GPWR1/02_post/vfx/tools/"

    filtered_paths = s.filepaths_from_prproj(prproj_path, ignore_paths=[ignored_prefix])

    assert all(not path.startswith(ignored_prefix) for path in filtered_paths)
    assert any("/Volumes/jobs/GPWR1/02_post/media/" in path for path in filtered_paths)


def test_filepaths_from_prproj_fallback_on_malformed_project(tmp_path: Path):
    malformed_prproj = tmp_path / "malformed.prproj"
    malformed_content = (
        "<PremiereProject>"
        "<FilePath>/Volumes/jobs/GPWR1/clipA.mov</FilePath>"
        "<ActualMediaFilePath>/Volumes/jobs/GPWR1/clipB.mov</ActualMediaFilePath>"
        "<UnclosedTag>"
    )

    with gzip.open(malformed_prproj, "wt", encoding="utf-8") as handle:
        handle.write(malformed_content)

    with pytest.warns(RuntimeWarning, match="Project parse failed"):
        paths = s.filepaths_from_prproj(malformed_prproj)

    assert "/Volumes/jobs/GPWR1/clipA.mov" in paths
    assert "/Volumes/jobs/GPWR1/clipB.mov" in paths


def test_main_dispatches_prproj_with_hierarchical_copy(tmp_path: Path):
    source = tmp_path / "sample.prproj"
    source.touch()
    destination = tmp_path / "archive"
    destination.mkdir()

    args = a.argparse.Namespace(
        source=[source],
        destination=destination,
        exclude_directories=None,
        placeholder=True,
    )

    source_files = [Path("/Volumes/jobs/GPWR1/02_post/media/example.mov")]

    with patch("archive_nle.parse_arguments", return_value=args), \
        patch("archive_nle.search.filepaths_from_prproj", return_value=source_files) as mock_extract, \
        patch("archive_nle.uncopied_files", return_value=source_files), \
        patch("archive_nle.get_file_size_with_retry", return_value=0), \
        patch("archive_nle.copy_files_shutil") as mock_copy, \
        patch("builtins.input", return_value="y"):
        a.main()

    mock_extract.assert_called_once_with(prproj_path=source, ignore_paths=None)
    assert mock_copy.call_args.kwargs["flat"] is False


def test_main_aggregates_multiple_xml_sources_and_deduplicates(tmp_path: Path):
    source_a = tmp_path / "one.xml"
    source_b = tmp_path / "two.xml"
    source_a.touch()
    source_b.touch()
    destination = tmp_path / "archive"
    destination.mkdir()

    args = a.argparse.Namespace(
        source=[source_a, source_b],
        destination=destination,
        exclude_directories=None,
        placeholder=True,
    )

    clip_a = Path("/Volumes/jobs/GPWR1/02_post/media/A.mov")
    clip_b = Path("/Volumes/jobs/GPWR1/02_post/media/B.mov")
    clip_c = Path("/Volumes/jobs/GPWR1/02_post/media/C.mov")
    deduped_clips = [clip_a, clip_b, clip_c]

    with patch("archive_nle.parse_arguments", return_value=args), \
        patch("archive_nle.search.filepaths_from_xml", side_effect=[[clip_a, clip_b], [clip_b, clip_c]]) as mock_extract, \
        patch("archive_nle.uncopied_files", return_value=deduped_clips) as mock_uncopied, \
        patch("archive_nle.get_file_size_with_retry", return_value=0), \
        patch("archive_nle.copy_files_shutil") as mock_copy, \
        patch("builtins.input", return_value="y"):
        a.main()

    assert mock_extract.call_count == 2
    mock_uncopied.assert_called_once_with(src_files=deduped_clips, dst_path=destination)
    assert mock_copy.call_args.kwargs["src_paths"] == deduped_clips
    assert mock_copy.call_args.kwargs["flat"] is False


def test_main_aggregates_multiple_aaf_sources_with_flat_copy(tmp_path: Path):
    source_a = tmp_path / "one.aaf"
    source_b = tmp_path / "two.aaf"
    source_a.touch()
    source_b.touch()
    destination = tmp_path / "archive"
    destination.mkdir()

    args = a.argparse.Namespace(
        source=[source_a, source_b],
        destination=destination,
        exclude_directories=None,
        placeholder=True,
    )

    clip_a = Path("/Volumes/jobs/GPWR1/02_post/media/A.mxf")
    clip_b = Path("/Volumes/jobs/GPWR1/02_post/media/B.mxf")
    deduped_clips = [clip_a, clip_b]

    with patch("archive_nle.parse_arguments", return_value=args), \
        patch("archive_nle.search.filepaths_from_aaf", side_effect=[[clip_a], [clip_a, clip_b]]) as mock_extract, \
        patch("archive_nle.uncopiedfiles_directoryagnostic", return_value=deduped_clips) as mock_uncopied, \
        patch("archive_nle.get_file_size_with_retry", return_value=0), \
        patch("archive_nle.copy_files_shutil") as mock_copy, \
        patch("builtins.input", return_value="y"):
        a.main()

    assert mock_extract.call_count == 2
    mock_uncopied.assert_called_once_with(src_paths=deduped_clips, dst_path=destination)
    assert mock_copy.call_args.kwargs["src_paths"] == deduped_clips
    assert mock_copy.call_args.kwargs["flat"] is True


# ---------------------------------------------------------------------------
# make_archive_relative
# ---------------------------------------------------------------------------


def test_make_archive_relative_volumes_path():
    result = a.make_archive_relative(Path("/Volumes/raid1/dailies/test.mov"))
    assert result == Path("raid1/dailies/test.mov")


def test_make_archive_relative_users_path():
    result = a.make_archive_relative(Path("/Users/russell/Dropbox/media/test.mov"))
    assert result == Path("Users/russell/Dropbox/media/test.mov")


def test_make_archive_relative_other_root():
    result = a.make_archive_relative(Path("/mnt/storage/project/clip.mov"))
    assert result == Path("mnt/storage/project/clip.mov")


def test_make_archive_relative_bare_filename():
    result = a.make_archive_relative(Path("clip.mov"))
    assert result == Path("clip.mov")


# ---------------------------------------------------------------------------
# unquoted_path_from_url – non-/Volumes paths
# ---------------------------------------------------------------------------


def test_path_from_url_users():
    source = "file://localhost/Users/russell/Dropbox/media/My%20Clip.mov"
    result = s.unquoted_path_from_url(source)
    assert result == "/Users/russell/Dropbox/media/My Clip.mov"


def test_path_from_url_no_host():
    source = "file:///Volumes/Media/clip.mov"
    result = s.unquoted_path_from_url(source)
    assert result == "/Volumes/Media/clip.mov"


def test_path_from_url_users_no_host():
    source = "file:///Users/russell/Dropbox/clip.mov"
    result = s.unquoted_path_from_url(source)
    assert result == "/Users/russell/Dropbox/clip.mov"


# ---------------------------------------------------------------------------
# normalize_lookup_path – non-/Volumes file URLs
# ---------------------------------------------------------------------------


def test_normalize_lookup_path_users_url():
    url = "file://localhost/Users/russell/Dropbox/media/clip.mov"
    result = s.normalize_lookup_path(url)
    assert result == "/Users/russell/Dropbox/media/clip.mov"


def test_normalize_lookup_path_volumes_url():
    url = "file://localhost/Volumes/Media/clip.mov"
    result = s.normalize_lookup_path(url)
    assert result == "/Volumes/Media/clip.mov"


def test_normalize_lookup_path_plain_users_path():
    result = s.normalize_lookup_path("/Users/russell/media/clip.mov")
    assert result == "/Users/russell/media/clip.mov"


# ---------------------------------------------------------------------------
# destination_path – non-/Volumes paths
# ---------------------------------------------------------------------------


def test_get_destination_path_users(tmp_path: Path):
    result = a.destination_path(
        Path("/Users/russell/Dropbox/media/clip.mov"), tmp_path
    )
    assert result == tmp_path / "Users" / "russell" / "Dropbox" / "media" / "clip.mov"


def test_get_destination_path_volumes_unchanged(tmp_path: Path):
    """Ensure existing /Volumes behaviour is preserved."""
    result = a.destination_path(
        Path("/Volumes/raid1/dailies/test.mov"), tmp_path
    )
    assert result == tmp_path / "raid1" / "dailies" / "test.mov"


# ---------------------------------------------------------------------------
# determine_destination – non-/Volumes paths
# ---------------------------------------------------------------------------


def test_determine_destination_hierarchy_users(tmp_path: Path):
    src = Path("/Users/russell/Dropbox/media/clip.mov")
    result = a.determine_destination(src, tmp_path, flat=False)
    assert result == tmp_path / "Users" / "russell" / "Dropbox" / "media" / "clip.mov"


def test_determine_destination_flat_users(tmp_path: Path):
    src = Path("/Users/russell/Dropbox/media/clip.mov")
    result = a.determine_destination(src, tmp_path, flat=True)
    assert result == tmp_path / "clip.mov"


def test_determine_destination_hierarchy_volumes_unchanged(tmp_path: Path):
    """Existing /Volumes behaviour preserved."""
    src = Path("/Volumes/Media/MyProject/clip.mov")
    result = a.determine_destination(src, tmp_path, flat=False)
    assert result == tmp_path / "Media" / "MyProject" / "clip.mov"


# ---------------------------------------------------------------------------
# uncopied_files – non-/Volumes paths
# ---------------------------------------------------------------------------


def test_uncopied_files_users_paths(tmp_path: Path):
    """Files under /Users should NOT falsely appear as already copied."""
    srcs = [
        Path("/Users/russell/media/clip1.mov"),
        Path("/Users/russell/media/clip2.mov"),
    ]
    # Nothing exists under tmp_path so both should be uncopied
    result = a.uncopied_files(srcs, tmp_path)
    assert set(result) == set(srcs)


def test_uncopied_files_users_paths_some_exist(tmp_path: Path):
    """When a destination file already exists, it should be excluded."""
    srcs = [
        Path("/Users/russell/media/clip1.mov"),
        Path("/Users/russell/media/clip2.mov"),
    ]
    # Create the destination for clip1 so it appears copied
    dst_clip1 = tmp_path / "Users" / "russell" / "media" / "clip1.mov"
    dst_clip1.parent.mkdir(parents=True, exist_ok=True)
    dst_clip1.touch()

    result = a.uncopied_files(srcs, tmp_path)
    assert result == [Path("/Users/russell/media/clip2.mov")]


# ---------------------------------------------------------------------------
# End-to-end: XML with /Users paths
# ---------------------------------------------------------------------------


def test_extract_pathurls_from_xml_users_paths(tmp_path: Path):
    """XML containing file URLs under /Users should produce /Users paths."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
  <sequence>
    <media>
      <file>
        <pathurl>file://localhost/Users/russell/Dropbox/media/clip%20A.mov</pathurl>
      </file>
      <file>
        <pathurl>file://localhost/Users/russell/Dropbox/media/clip%20B.mov</pathurl>
      </file>
    </media>
  </sequence>
</xmeml>"""

    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    result = s.filepaths_from_xml(str(xml_file))
    assert "/Users/russell/Dropbox/media/clip A.mov" in result
    assert "/Users/russell/Dropbox/media/clip B.mov" in result
    # Ensure /Volumes is NOT wrongly prepended
    assert not any("/Volumes/Users" in p for p in result)


# ---------------------------------------------------------------------------
# End-to-end: PRPROJ with /Users paths
# ---------------------------------------------------------------------------


def test_filepaths_from_prproj_users_paths(tmp_path: Path):
    """PRPROJ with media under /Users should produce correct paths."""
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<PremiereData>\n"
        "  <FilePath>/Users/russell/Dropbox/media/clip.mov</FilePath>\n"
        "  <ActualMediaFilePath>/Users/russell/Dropbox/media/clip.mov</ActualMediaFilePath>\n"
        "  <pathurl>file://localhost/Users/russell/Dropbox/media/clip%20B.mov</pathurl>\n"
        "</PremiereData>\n"
    )

    prproj = tmp_path / "test.prproj"
    with gzip.open(prproj, "wt", encoding="utf-8") as handle:
        handle.write(content)

    paths = s.filepaths_from_prproj(prproj)
    assert "/Users/russell/Dropbox/media/clip.mov" in paths
    assert "/Users/russell/Dropbox/media/clip B.mov" in paths
    assert not any("/Volumes/Users" in p for p in paths)


# ---------------------------------------------------------------------------
# Integration: main() with /Users media through XML source
# ---------------------------------------------------------------------------


def test_main_xml_users_paths(tmp_path: Path):
    """XML source with /Users paths should compute sizes without errors."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
  <sequence>
    <media>
      <file>
        <pathurl>file://localhost/Users/russell/media/clip.mov</pathurl>
      </file>
    </media>
  </sequence>
</xmeml>"""
    src = tmp_path / "test.xml"
    src.write_text(xml_content, encoding="utf-8")
    destination = tmp_path / "archive"
    destination.mkdir()

    args = a.argparse.Namespace(
        source=[src],
        destination=destination,
        exclude_directories=None,
        placeholder=True,
    )

    with patch("archive_nle.parse_arguments", return_value=args), \
        patch("archive_nle.get_file_size_with_retry", return_value=100), \
        patch("archive_nle.copy_files_shutil") as mock_copy, \
        patch("builtins.input", return_value="y"):
        a.main()

    # Should reach copy with flat=False (XML default)
    assert mock_copy.call_args.kwargs["flat"] is False