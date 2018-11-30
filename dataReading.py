import os
import json
import xml.etree.ElementTree as ET
import string
import time
import re
import nltk
import operator
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# personal imports
from configuration import Configuration
from MergeBased import MergeBased

nltk.download('stopwords')
sw = stopwords.words('english')
doc_id_by_file = dict()
inverted_dictionary = {}
inverted_list = {}
nb_documents = 0


def update_inverted_dictionary(array, doc_id):
    global inverted_dictionary
    global inverted_list
    if Configuration.stemming:
        ps = PorterStemmer()
        for word in array:
            item = ps.stem(word)
            if item in sw:
                continue
            elif item in inverted_dictionary:
                if doc_id in inverted_dictionary[item]:
                    inverted_dictionary[item][doc_id] += 1
                else:
                    inverted_dictionary[item][doc_id] = 1
            else:
                inverted_dictionary[item] = {doc_id: 1}
    else:
        for item in array:
            if item in sw:
                continue
            elif item in inverted_dictionary:
                if doc_id in inverted_dictionary[item]:
                    inverted_dictionary[item][doc_id] += 1
                else:
                    inverted_dictionary[item][doc_id] = 1
            else:
                inverted_dictionary[item] = {doc_id: 1}


def treat_text(doc_text):
    doc_text = doc_text.replace("\n", " ")
    punctuation = '!"#$%&\()*+,-./:;<=>?@[\\]^_`{|}~'
    for char in punctuation:
        doc_text = doc_text.replace(char, " ")

    doc_text = re.sub(r"(\B')", " ", doc_text, flags=re.M)
    doc_text = re.sub(r"('\B)", " ", doc_text, flags=re.M)
    doc_text = re.sub(r"(\d+\S*)", "<number>", doc_text, flags=re.M)
    doc_text = doc_text.lower()
    #   text = ' '.join(text.split())
    return doc_text


def add_doc_inverted_dictionary(doc, doc_id):
    text = ""
    for node in doc:
        for p in node.findall("P"):
            text = text + ' ' + p.text
    text = treat_text(text)
    words = text.split()
    update_inverted_dictionary(words, doc_id)


def add_folder_inverted_dictionary(data_folder, temp_folder=None):
    """
    If we use merge-based, we will save b
    :param data_folder: data folder
    :return:
    """
    global nb_documents
    for file in os.listdir(data_folder):
        if "." not in file:
            with open(data_folder + "/" + file, "r") as my_file:
                data = "<root>" + my_file.read() + "</root>"
                root = ET.fromstring(data)
                for doc in root.findall("DOC"):
                    nb_documents = nb_documents + 1
                    doc_id = doc.find("DOCID").text.split()[0]
                    doc_id_by_file[doc_id] = (data_folder + "\\" + file)
                    add_doc_inverted_dictionary(doc, doc_id)
                    if nb_documents % 1000 == 0 and Configuration.merge_based :
                        save_inverted(nb_documents / 1000, temp_folder)
    if Configuration.merge_based :
        save_inverted(nb_documents/1000 + 1, temp_folder)
        save_dictionary_doc_by_id(doc_id_by_file)


def create_inverted_list():
    for key in inverted_dictionary.keys():
        doc_dict = inverted_dictionary[key]
        sorted_list =  sorted(doc_dict.items(), key=operator.itemgetter(1), reverse=True)
        inverted_list[key] = sorted_list


def get_dictionaries(path):
    add_folder_inverted_dictionary(path)
    create_inverted_list()
    return inverted_dictionary, inverted_list, nb_documents


def save_inverted(number, temp_folder):
    #print("tmp folder:", temp_folder)
    global inverted_dictionary
    global inverted_list
    for key in inverted_dictionary.keys():
        doc_dict = inverted_dictionary[key]
        sorted_list = sorted(doc_dict.items(), key=operator.itemgetter(0))
        inverted_list[key] = sorted_list
    final_list = sorted(inverted_list.items(), key=operator.itemgetter(0))
    file = open(temp_folder + "/file_%d" % number, "w+")
    line = ""
    for word in final_list:
        line += word[0] + "|"
        for document in word[1]:
            line += str(document[0]) + ":" + str(document[1]) + "; "
        line += "\n"
    file.write(line)
    file.close()
    inverted_dictionary = {}
    inverted_list = {}


def save_dictionary_doc_by_id(doc_id_by_file):
    json_list = json.dumps(doc_id_by_file)
    f = open(Configuration.json_path + "/doc_id_by_file.json", "w")
    f.write(json_list)
    f.close()


def delete_folder_files(folder):
    for file in os.listdir(folder):
        os.remove(folder+ "\\" + file)


def get_structures():
    """
    :return: the structures from the path to folder containing the jsons
    """
    json_path = Configuration.json_path

    for file in os.listdir(json_path):
        if file == "dict_with_dict.json":
            file = open(json_path + "\\" + file)
            dict_struct = json.load(file)
        elif file == "dict_with_list.json":
            file = open(json_path + "\\" + file)
            dict_list = json.load(file)
        elif file == "doc_id_by_file.json":
            file = open(json_path + "\\" + file)
            doc_id_by_file = json.load(file)
    print("The number of terms:", len(dict_list))
    print("The number of articles:", len(doc_id_by_file))
    return dict_struct, dict_list, doc_id_by_file
