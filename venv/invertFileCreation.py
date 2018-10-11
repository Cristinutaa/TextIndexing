import dataReading
import os
import json
import xml.etree.ElementTree as ET
import string
import time
import re
import nltk
from nltk.corpus import stopwords


def create_inverted_map(dictionary):
    inverted_map = {}
    for doc_id in dictionary:
        word_dict = dictionary[doc_id]
        for word in word_dict:
            word_count = word_dict[word]
            if word in inverted_map:
                inverted_map[word][doc_id] = word_count
            else:
                inverted_map[word] = {doc_id: word_count}

    return inverted_map


if __name__ == "__main__":
    data_path = input("Please write the path to the folder that contains the data \n")
    print("We are treating the data from " + data_path)
    startTime = time.time()
    inverted_map = create_inverted_map(dataReading.create_global_dictionary(data_path))
    print("The treatment took %s seconds" % (time.time() - startTime))
    export_json = input("Do you want to export the result inverted file in a json? (yes/anything else) \n")
    if export_json == "yes":
        json = json.dumps(inverted_map)
        f = open("resources/inverted_file.json", "w")
        f.write(json)
        f.close()
        print("Saved in resources/inverted_file.json! Have a nice day!")
    else:
        print("Have a nice day!")