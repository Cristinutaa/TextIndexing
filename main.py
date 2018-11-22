import os
import json
import time

# personal imports
import dataReading
import ranking
from configuration import Configuration


def main():

    # CONFIGURATION
    print("\n\n--------------- Configuration -----------------")
    Configuration.configure()
    data_path = Configuration.row_data_path

    # STRUCTURES CREATION OR READING
    print("\n\n--------------- Getting structures -----------------")
    choice = input("Do you want to create the structures from the data or to load pre-created structures from "
                   + Configuration.json_path + "?   "
                   "(yes=create the structures/anything else=use pre-created)")
    if choice == "yes":
        print("Please wait until the data have been treated...")
        startTime = time.time()
        dataReading.add_folder_inverted_dictionary(data_path)
        dataReading.create_inverted_list()
        print("The treatment took %s seconds" % (time.time() - startTime))
        print("Nombre de documents %d" % dataReading.nb_documents)
        toexport = input("Should we export the created structures from the data ?   (yes/anything else)")
        if toexport == "yes":
            if not hasattr(Configuration, 'json_path'):
                Configuration.json_path = input("Please specify a folder path to save the jsons : ")
            json_path = Configuration.json_path
            export_json = input(
            "Should we export the result dictionary with dictionaries in a json (to " +
            json_path + ")? (yes/anything else) \n")
            if export_json == "yes":
                json_dict = json.dumps(dataReading.inverted_dictionary)
                f = open(Configuration.json_path + "/dict_with_dict.json", "w")
                f.write(json_dict)
                f.close()
                print("Saved in " + Configuration.json_path + "/dict_with_dict.json!")
            export_json = input(
                "Should we export the result dictionary with lists in a json (to " +
                json_path + ")? (yes/anything else) \n")
            if export_json == "yes":
                json_list = json.dumps(dataReading.inverted_list)
                f = open(Configuration.json_path + "/dict_with_list.json", "w")
                f.write(json_list)
                f.close()
                print("Saved in " + Configuration.json_path + "/dict_with_list.json!")
            export_json = input(
                "Should we export the corpus dictionary in a json file (to " +
                json_path + ")? (yes/anything else) \n")
            if export_json == "yes":
                json_list = json.dumps(dataReading.doc_id_by_file)
                f = open(Configuration.json_path + "/doc_id_by_file.json", "w")
                f.write(json_list)
                f.close()
                print("Saved in " + Configuration.json_path + "/doc_id_by_file.json! Have a nice day!")
            ranking.dict_struct, ranking.dict_list, ranking.doc_id_by_file = \
                dataReading.inverted_dictionary, dataReading.inverted_list, dataReading.doc_id_by_file
    else:
        print("Fine. Fetching json files from " + Configuration.json_path + "...")
        ranking.dict_struct, ranking.dict_list, ranking.doc_id_by_file = ranking.get_structures()

    # QUERYING : Contrarily to the independent module, we can directly use the values we got earlier
    # Query as much as you need
    print("\n\n--------------- Querying -----------------")
    while True:
        ask_again = True if input("Do you want to query something? (yes/no)\n").lower() == "yes" \
            else False
        if not ask_again:
            print("Fine, have a nice day!")
            break
        ranking.ask_query()


if __name__ == "__main__":
    main()