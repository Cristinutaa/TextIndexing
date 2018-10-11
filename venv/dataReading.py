import os
import json
import xml.etree.ElementTree as ET
import string
import time
import re
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
sw = stopwords.words('english')


def build_dictionary(array):
    new_dictionary = {}
    for item in array:
        if item in new_dictionary:
            new_dictionary[item] += 1
        else:
            new_dictionary[item] = 1
    return new_dictionary


def treat_text(doc_text):
    doc_text = doc_text.replace("\n", " ")
    punctuation = '!"#$%&\()*+,-./:;<=>?@[\\]^_`{|}~'
    for char in punctuation:
        doc_text = doc_text.replace(char, " ")
    doc_text = re.sub(r"(\d+\S*)", "<number>", doc_text, flags=re.M)
    doc_text = doc_text.lower()
    #   text = ' '.join(text.split())
    return doc_text


def create_doc_dictionary(doc):
    text = ""
    for node in doc:
        for p in node.findall("P"):
            text = text + ' ' + p.text
    text = treat_text(text)
    words = text.split()
    doc_dictionary = build_dictionary(words)
    words_to_keep = set(doc_dictionary.keys()) - set(sw)
    final_dictionary = {key: doc_dictionary[key] for key in words_to_keep}
    return final_dictionary


def create_global_dictionary(folder):
    articles_dictionary = {}
    for file in os.listdir(folder):
        with open(folder + "/" + file, "r") as myfile:
            data = "<root>" + myfile.read() + "</root>"
            root = ET.fromstring(data)
            for doc in root.findall("DOC"):
                doc_id = doc.find("DOCID").text.split()[0]
                doc_dictionary = create_doc_dictionary(doc)
                #               doc_dictionary = {i:words.count(i) for i in set(words)}
                articles_dictionary[doc_id] = doc_dictionary
    return articles_dictionary


if __name__ == "__main__":
    data_path = input("Please write the path to the folder that contains the data \n")
    print("We are treating the data from " + data_path)
    startTime = time.time()
    dictionary = create_global_dictionary(data_path)
    print("The treatment took %s seconds" % (time.time() - startTime))
    export_json = input("Do you want to export the result dictionary in a json? (yes/anything else) \n")
    if export_json == "yes":
        json = json.dumps(dictionary)
        f = open("resources/dict.json", "w")
        f.write(json)
        f.close()
        print("Saved in resources/dict.json! Have a nice day!")
    else:
        print("Have a nice day!")
