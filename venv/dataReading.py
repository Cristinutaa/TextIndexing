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


nltk.download('stopwords')
sw = stopwords.words('english')
inverted_dictionary = {}
inverted_list = {}
nb_documents = 0


def update_inverted_dictionary(array, doc_id):
    global inverted_dictionary
    global inverted_list
    #ps = PorterStemmer()
    #word
    for item in array:
        #item = ps.stem(word)
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


def add_folder_inverted_dictionary(folder):
    global nb_documents
    for file in os.listdir(folder):
        with open(folder + "/" + file, "r") as my_file:
            data = "<root>" + my_file.read() + "</root>"
            root = ET.fromstring(data)
            for doc in root.findall("DOC"):
                nb_documents = nb_documents + 1
                doc_id = doc.find("DOCID").text.split()[0]
                add_doc_inverted_dictionary(doc, doc_id)


def create_inverted_list():
    for key in inverted_dictionary.keys():
        doc_dict = inverted_dictionary[key]
        sorted_list =  sorted(doc_dict.items(), key=operator.itemgetter(1), reverse=True)
        inverted_list[key] = sorted_list


def get_dictionaries(path):
    add_folder_inverted_dictionary(path)
    create_inverted_list()
    return inverted_dictionary, inverted_list, nb_documents


if __name__ == "__main__":
    data_path = input("Please write the path to the folder that contains the data \n")
    print("We are treating the data from " + data_path)
    startTime = time.time()
    add_folder_inverted_dictionary(data_path)
    create_inverted_list()
    print("The treatment took %s seconds" % (time.time() - startTime))
    print("Nombre de documents %d" % nb_documents)
    if not os.path.exists("resources"):
        os.makedirs("resources")
    export_json = input(
            "Should we export the result dictionary with dictionaries in a json? (yes/anything else) \n")
    if export_json == "yes":
        json_dict = json.dumps(inverted_dictionary)
        f = open("resources/dict_with_dict.json", "w")
        f.write(json_dict)
        f.close()
        print("Saved in resources/dict_with_dict.json!")
    export_json = input(
            "Should we export the result dictionary with lists in a json? (yes/anything else) \n")
    if export_json == "yes":
        json_list = json.dumps(inverted_list)
        f = open("resources/dict_with_list.json", "w")
        f.write(json_list)
        f.close()
        print("Saved in resources/dict_with_list.json! Have a nice day!")
