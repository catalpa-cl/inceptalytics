import zipfile
from xml.etree import cElementTree as ElementTree
from typing import Any, Dict, List, Set
from collections import defaultdict
from zipfile import ZipFile
import xmltodict


def get_annotated_file_names(path: str) -> tuple:

    complete_names = []
    annotator_names = []
    file_names = []

    with ZipFile(path) as zip_file:
        for file in zip_file.namelist():
            if file.startswith('annotation/'):
                complete_names.append(file)
                annotator_names.append(file.split('/')[-1])
                file_names.append(file.split('/')[1])
    return complete_names, file_names, annotator_names


def extract_project_files(path: str, target_path: str, folder_name='annotation/'):

    with ZipFile(path) as zip_file:
        for file in zip_file.namelist():
            if file.startswith(folder_name) or folder_name is None:
                zip_file.extract(file, target_path)

                #if zipfile.is_zipfile(target_path + file):
                #    extract_project_files(target_path, target_path + file.split('.')[0], folder_name=None)


def read_xml_file(file_path):
    with open(file_path) as fd:
        doc = xmltodict.parse(fd.read())
    return doc


if __name__ == '__main__':

    src_path = 'test_project/test2.zip'
    tar_path = 'test_project/test_target/'

    extract_project_files(src_path, tar_path)

    xml_dict = read_xml_file('test_project/test.xml')
    print(xml_dict)

    complete_names, file_names, annotator_names = get_annotated_file_names(src_path)
    print(complete_names, file_names, annotator_names)
