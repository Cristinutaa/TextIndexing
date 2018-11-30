import os
import json
import time
import sys

# personal imports
from dataReading import DataReading
import ranking
from configuration import Configuration
from MergeBased import MergeBased


def main():

    # CONFIGURATION
    print("\n\n--------------- Configuration -----------------")
    Configuration.configure()
    data_path = Configuration.row_data_path

    dr = DataReading()

    # STRUCTURES CREATION OR READING : only for RAM option since for Merge-based,
    # we need to get them on the fly for each query
    if not Configuration.merge_based:
        print("\n\n--------------- Getting structures -----------------")
        choice = input("Do you want to create the structures from the data or to load pre-created structures from "
                       + Configuration.json_path + "?   "
                       "(yes=create the structures/anything else=use pre-created)")
        if choice == "yes":
            print("Please wait until the data has been treated...")
            startTime = time.time()
            dr.add_folder_inverted_dictionary(data_path)
            dr.calculate_score_inverted_dictionary()
            dr.create_inverted_list()
            print("The treatment took %s seconds" % (time.time() - startTime))
            print("Number of documents %d" % dr.nb_documents)
            toexport = input("Should we export the created structures from the data ?   (yes/anything else)")
            if toexport == "yes":
                if not hasattr(Configuration, 'json_path'):
                    Configuration.json_path = input("Please specify a folder path to save the jsons : ")
                json_path = Configuration.json_path
                export_json = input(
                "Should we export the result dictionary with dictionaries in a json (to " +
                json_path + ")? (yes/anything else) \n")
                if export_json == "yes":
                    json_dict = json.dumps(dr.inverted_dictionary)
                    f = open(Configuration.json_path + "/dict_with_dict.json", "w")
                    f.write(json_dict)
                    f.close()
                    print("Saved in " + Configuration.json_path + "/dict_with_dict.json!")
                export_json = input(
                    "Should we export the result dictionary with lists in a json (to " +
                    json_path + ")? (yes/anything else) \n")
                if export_json == "yes":
                    json_list = json.dumps(dr.inverted_list)
                    f = open(Configuration.json_path + "/dict_with_list.json", "w")
                    f.write(json_list)
                    f.close()
                    print("Saved in " + Configuration.json_path + "/dict_with_list.json!")
                export_json = input(
                    "Should we export the corpus dictionary in a json file (to " +
                    json_path + ")? (yes/anything else) \n")
                if export_json == "yes":
                    json_list = json.dumps(dr.doc_id_by_file)
                    f = open(Configuration.json_path + "/doc_id_by_file.json", "w")
                    f.write(json_list)
                    f.close()
                    print("Saved in " + Configuration.json_path + "/doc_id_by_file.json! Have a nice day!")
            dict_struct, dict_list, doc_id_by_file = \
                dr.inverted_dictionary, dr.inverted_list, dr.doc_id_by_file
        else:
            print("Fine. Fetching json files from " + Configuration.json_path + "...")
            dict_struct, dict_list, doc_id_by_file = dr.get_structures()

    # 1/ Init a query process
    if Configuration.merge_based:
        temp = "./temp_ressources"  # Temporary directory to put blocks of structure
        if not os.path.exists(temp):
            os.makedirs(temp)
        dr.delete_folder_files(temp) # We clean the folder to use for the blocks of structure
        dr.add_folder_inverted_dictionary(Configuration.row_data_path, temp) # Save blocks of structure
        mb = MergeBased(temp, "binary_file_out.txt", dr.nb_documents)
        mb.merge_all_files()

        #print("doc_id_by_file:", doc_id_by_file)
        # QUERYING : Contrarily to the independent module, we can directly use the values we got earlier
        # Query as much as you need
        print("\n\n--------------- Querying -----------------")
        query_process = ranking.QueryProcess(dr.doc_id_by_file, merge_based=mb)
        pass
    else:
        # QUERYING : Contrarily to the independent module, we can directly use the values we got earlier
        # Query as much as you need
        print("\n\n--------------- Querying -----------------")
        query_process = ranking.QueryProcess(doc_id_by_file, dict_struct=dict_struct, dict_list=dict_list)
    while True:
        ask_again = True if input("Do you want to query something? (yes/no)\n").lower() == "yes" \
            else False
        if not ask_again:
            print("Fine, have a nice day!")
            sys.exit()
        query_process.ask_query()


if __name__ == "__main__":
    main()