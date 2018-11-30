import os
import json
import xml.etree.ElementTree as ET
import string
import time
import re
import nltk
import operator
import math
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# personal imports
from configuration import Configuration
from random_indexing import Random_Indexing
import score

class DataReading:

    def __init__(self):
        nltk.download('stopwords')
        self.sw = stopwords.words('english')
        self.doc_id_by_file = dict()
        self.inverted_dictionary = dict()
        self.inverted_list = dict()
        self.nb_documents = 0


    def update_inverted_dictionary(self, array, doc_id):
        if Configuration.stemming:
            ps = PorterStemmer()
            for word in array:
                item = ps.stem(word)
                if item in self.sw:
                    continue
                elif item in self.inverted_dictionary:
                    if doc_id in self.inverted_dictionary[item]:
                        self.inverted_dictionary[item][doc_id] += 1
                    else:
                        self.inverted_dictionary[item][doc_id] = 1
                else:
                    self.inverted_dictionary[item] = {doc_id: 1}
        else:
            for item in array:
                if item in self.sw:
                    continue
                elif item in self.inverted_dictionary:
                    if doc_id in self.inverted_dictionary[item]:
                        self.inverted_dictionary[item][doc_id] += 1
                    else:
                        self.inverted_dictionary[item][doc_id] = 1
                else:
                    self.inverted_dictionary[item] = {doc_id: 1}


    def treat_text(self, doc_text):
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


    def add_doc_inverted_dictionary(self, doc, doc_id):
        text = ""
        for node in doc:
            for p in node.findall("P"):
                text = text + ' ' + p.text
        text = self.treat_text(text)
        words = text.split()
        self.update_inverted_dictionary(words, doc_id)


    # Calculate the score with tf-idf in case we don't use merge-based
    def calculate_score_inverted_dictionary(self):
        for word in self.inverted_dictionary:
            for doc in self.inverted_dictionary[word]:
                self.inverted_dictionary[word][doc] = score.tf_idf(self.inverted_dictionary[word][doc], len(self.inverted_dictionary[word]), self.nb_documents)

    def add_folder_inverted_dictionary(self, data_folder, temp_folder=None):
        """
        If we use merge-based, we will save b
        :param data_folder: data folder
        :return:
        """
        for file in os.listdir(data_folder):
            if "." not in file:
                with open(data_folder + "/" + file, "r") as my_file:
                    data = "<root>" + my_file.read() + "</root>"
                    root = ET.fromstring(data)
                    for doc in root.findall("DOC"):
                        self.nb_documents = self.nb_documents + 1
                        doc_id = doc.find("DOCID").text.split()[0]
                        self.doc_id_by_file[doc_id] = (data_folder + "\\" + file)
                        self.add_doc_inverted_dictionary(doc, doc_id)
                        if self.nb_documents % 1000 == 0 and Configuration.merge_based :
                            self.save_inverted(self.nb_documents / 1000, temp_folder)
        if Configuration.random_indexing:
            ri = Random_Indexing(Configuration.dimension_vector_random_indexing)
            ri.build_index_and_context_vectors(self.inverted_dictionary)
        if Configuration.merge_based:
            self.save_inverted(self.nb_documents/1000 + 1, temp_folder)
            self.save_dictionary_doc_by_id()


    def create_inverted_list(self):
        for key in self.inverted_dictionary.keys():
            doc_dict = self.inverted_dictionary[key]
            sorted_list =  sorted(doc_dict.items(), key=operator.itemgetter(1), reverse=True)
            self.inverted_list[key] = sorted_list


    def get_dictionaries(self, path):
        self.add_folder_inverted_dictionary(path)
        self.create_inverted_list()
        return self.inverted_dictionary, self.inverted_list, self.nb_documents


    def save_inverted(self, number, temp_folder):
        #print("tmp folder:", temp_folder)
        for key in self.inverted_dictionary.keys():
            doc_dict = self.inverted_dictionary[key]
            sorted_list = sorted(doc_dict.items(), key=operator.itemgetter(0))
            self.inverted_list[key] = sorted_list
        final_list = sorted(self.inverted_list.items(), key=operator.itemgetter(0))
        file = open(temp_folder + "/file_%d" % number, "w+")
        line = ""
        for word in final_list:
            line += word[0] + "|"
            for document in word[1]:
                line += str(document[0]) + ":" + str(document[1]) + "; "
            line += "\n"
        file.write(line)
        file.close()
        self.inverted_dictionary = dict()
        self.inverted_list = dict()


    def save_dictionary_doc_by_id(self):
        json_list = json.dumps(self.doc_id_by_file)
        f = open(Configuration.json_path + "/doc_id_by_file.json", "w")
        f.write(json_list)
        f.close()


    def delete_folder_files(self, folder):
        for file in os.listdir(folder):
            os.remove(folder+ "\\" + file)


    def get_structures(self):
        """
        :return: the structures from the path to folder containing the jsons
        """
        json_path = Configuration.json_path

        for file in os.listdir(json_path):
            if file == "dict_with_dict.json":
                file = open(json_path + "\\" + file)
                self.inverted_dictionary = json.load(file)
            elif file == "dict_with_list.json":
                file = open(json_path + "\\" + file)
                self.inverted_list = json.load(file)
            elif file == "doc_id_by_file.json":
                file = open(json_path + "\\" + file)
                self.doc_id_by_file = json.load(file)
        print("The number of terms:", len(self.inverted_list))
        print("The number of articles:", len(self.doc_id_by_file))
        return self.inverted_dictionary, self.inverted_list, self.doc_id_by_file
