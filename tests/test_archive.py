import archive_xml_aaf_tdd as a
import search as s
import unittest, pytest
from pathlib import Path
from typing import List
from unittest.mock import patch
    
def test_convert_size():
    assert a.convert_size(100000000000) == '93.13 GB'
    assert a.convert_size(10000000000000) == '9.09 TB'
    
def test_dir_path():
    with patch('archive_xml_aaf_tdd.Path.is_dir', return_value=True):
        assert a.dir_path('/Volumes/raid/') == '/Volumes/raid/'

    with patch('archive_xml_aaf_tdd.Path.is_dir', return_value=False):
        with pytest.raises(NotADirectoryError):
            a.dir_path('/Volumes/raid/')
    
def test_parse_arguments_input_variables_are_cast_accurately():
    # Mock the command-line arguments
    with patch('sys.argv', ['archive aaf xml', '-s', 'some_source.xml', '-d', '/some/destination', '-e', '/path/to/exclude1', '/path/to/exclude2']), \
         patch('archive_xml_aaf_tdd.Path.is_file', return_value=True), \
         patch('archive_xml_aaf_tdd.Path.is_dir', return_value=True):
             
             args = a.parse_arguments()
             
             assert args.source == Path('some_source.xml')
             assert args.destination == Path('/some/destination')
             assert '/path/to/exclude1' in args.exclude_directories
             assert '/path/to/exclude2' in args.exclude_directories

def test_parse_arguments_invalid_directory():
    # Mock the command-line arguments
    with patch('sys.argv', ['prog_name', '-s', 'some_source.xml', '-d', '/nonexistent/destination']), \
         patch('archive_xml_aaf_tdd.Path.is_file', return_value=False), \
         patch('archive_xml_aaf_tdd.Path.is_dir', return_value=True), \
         pytest.raises(SystemExit):
             a.parse_arguments()
             
def test_get_destination_path():
    x = a.destination_path(Path('/Volumes/raid1/dailies/test.mov'), 
                           Path('/Volumes/raid2/'))
    assert x == Path('/Volumes/raid2/raid1/dailies/test.mov')
    
def test_is_file_copied_not():
    assert a.file_exists(Path('/Volumes/raid1/dailies/test.mov')) == False
    
def test_uncopied_files():
    
    with patch('archive_xml_aaf_tdd.file_exists', return_value=True):

        srcs = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
        uncopied_files = a.uncopied_files(srcs, Path('/Volumes/raid2/'))
        compare = [Path('/Volumes/raid1/dailies/test1.mov'), Path('/Volumes/raid1/dailies/test2.mov')]
    
        assert uncopied_files != compare
        
    with patch('archive_xml_aaf_tdd.file_exists', return_value=False):

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