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

from MergedBased import MergedBased

#personal imports
import configuration

nltk.download('stopwords')
sw = stopwords.words('english')
corpus_by_doc_id = dict()
inverted_dictionary = {}
inverted_list = {}
nb_documents = 0


def update_inverted_dictionary(array, doc_id):
    global inverted_dictionary
    global inverted_list
    if configuration.stemming:
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
    corpus_by_doc_id[doc_id] = text
    text = treat_text(text)
    words = text.split()
    update_inverted_dictionary(words, doc_id)


def add_folder_inverted_dictionary(folder):
    global nb_documents
    for file in os.listdir(folder):
        if "." not in file: #file is without extension
            with open(folder + "/" + file, "r") as my_file:
                data = "<root>" + my_file.read() + "</root>"
                root = ET.fromstring(data)
                for doc in root.findall("DOC"):
                    nb_documents = nb_documents + 1
                    doc_id = doc.find("DOCID").text.split()[0]
                    add_doc_inverted_dictionary(doc, doc_id)
                    if nb_documents % 1000 == 0:
                        save_inverted(nb_documents / 1000)

    save_inverted(nb_documents/1000 + 1)


def save_inverted(number):
    global inverted_dictionary
    global inverted_list
    for key in inverted_dictionary.keys():
        doc_dict = inverted_dictionary[key]
        sorted_list = sorted(doc_dict.items(), key=operator.itemgetter(0))
        inverted_list[key] = sorted_list
    final_list = sorted(inverted_list.items(), key=operator.itemgetter(0))
    file = open("resources/file_%d" % number, "w+")
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

def delete_folder_files(folder):
    for file in os.listdir(folder):
        os.remove(folder+ "\\" + file)


if __name__ == "__main__":
    delete_folder_files("resources")
    data_path = configuration.get_row_data_path()
    startTime = time.time()
    add_folder_inverted_dictionary(data_path)
    print("The treatment took %s seconds" % (time.time() - startTime))
    print("Nombre de documents %d" % nb_documents)

    mb = MergedBased( configuration.get_json_path() , "result/out.txt", nb_documents)
    print(mb.merge_all_files())
