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
import configuration
import dataReading
import ranking


def main():

    # CONFIGURATION
    print("\n\n--------------- Configuration -----------------")
    data_path = configuration.get_row_data_path()
    json_path = configuration.get_json_path()
    print("Here are the chosen configurations:")
    print(" - Path to data: ", data_path)
    print(" - Path to save the structures (loadable in RAM): ", json_path)

    # DATA READING
    print("\n\n--------------- Reading the data from", data_path, "-----------------")
    startTime = time.time()
    dataReading.add_folder_inverted_dictionary(data_path)
    dataReading.create_inverted_list()
    print("The treatment took %s seconds" % (time.time() - startTime))
    print("Nombre de documents %d" % dataReading.nb_documents)

    if not os.path.exists("resources"):
        os.makedirs("resources")
    export_json = input(
        "Should we export the result dictionary with dictionaries in a json (to " +
        json_path + ")? (yes/anything else) \n")
    if export_json == "yes":
        json_dict = json.dumps(dataReading.inverted_dictionary)
        f = open(configuration.default_json_path + "/dict_with_dict.json", "w")
        f.write(json_dict)
        f.close()
        print("Saved in " + configuration.default_json_path + "/dict_with_dict.json!")
    export_json = input(
        "Should we export the result dictionary with lists in a json (to " +
        json_path + ")? (yes/anything else) \n")
    if export_json == "yes":
        json_list = json.dumps(dataReading.inverted_list)
        f = open(configuration.default_json_path + "/dict_with_list.json", "w")
        f.write(json_list)
        f.close()
        print("Saved in " + configuration.default_json_path + "/dict_with_list.json!")
    export_json = input(
        "Should we export the corpus dictionary in a json file (to " +
        json_path + ")? (yes/anything else) \n")
    if export_json == "yes":
        json_list = json.dumps(dataReading.corpus_by_doc_id)
        f = open(configuration.default_json_path + "/corpus_by_doc_id.json", "w")
        f.write(json_list)
        f.close()
        print("Saved in " + configuration.default_json_path + "/corpus_by_doc_id.json! Have a nice day!")

    # QUERYING : Contrarily to the independent module, we can directly use the value we got earlier7
    # Query as much as you need
    print("\n\n--------------- Querying -----------------")
    ranking.dict_struct, ranking.dict_list, ranking.corpus_by_doc_id = \
        dataReading.inverted_dictionary, dataReading.inverted_list, dataReading.corpus_by_doc_id
    while True:
        ask_again = True if input("Do you want to query something? (yes/no)\n").lower() == "yes" \
            else False
        if not ask_again:
            print("Fine, have a nice day!")
            break
        ranking.ask_query()


if __name__ == "__main__":
    main()