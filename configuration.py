import json


class Configuration():
    @staticmethod
    def configure():
        """Fill the attribute of global variable Configuration"""
        using_configfile = input("Do you want to use a configuration file (careful, it must be complete)? "
                                 " (yes/anything else)")
        if using_configfile == "yes":
            valid_file = False
            conf = {}
            while not valid_file:
                config_file = input("Please specify path to configuration file: \n")
                try:
                    file = open(config_file)
                    conf = json.load(file)
                    valid_file = True
                except:
                    print("Invalid json file.")
                    valid_file = False
            print("Here are the chosen configurations:")
            for k, v in conf.items():
                print("-", k, ":", v)
            if conf["stemming"] == "True":
                Configuration.stemming = True
            else:
                Configuration.stemming = False
            if conf["random_indexing"] == "True":
                Configuration.random_indexing = True
            else:
                Configuration.random_indexing = False
            if conf["merge_based"] == "True":
                Configuration.merge_based = True
            else:
                Configuration.merge_based = False
            Configuration.row_data_path = conf["row_data_path"]
            Configuration.json_path = conf["json_path"]
            Configuration.dimension_vector_random_indexing = conf["dimension_vector_random_indexing"]

        else:  # Configurations to enter
            # 1/ Stemming or not
            choice = input("Do you want to use stemming?  (yes/anything else)")
            if choice == "yes":
                Configuration.stemming = True
            else:
                Configuration.stemming = False
            # 2/ random indexing or not
            choice = input("Do you want to use random indexing?  (yes/anything else)")
            if choice == "yes":
                Configuration.random_indexing = True
                valid = False
                while not valid:
                    Configuration.dimension_vector_random_indexing = input("Please specify dimension : ")
                    try:
                        Configuration.dimension_vector_random_indexing \
                            = int(Configuration.dimension_vector_random_indexing)
                        valid = True
                    except:
                        print("Invalid entry")
            else:
                Configuration.random_indexing = False
            # 3/ merge-based or not
            choice = input("Do you want to use merge-based?  (yes/anything else)")
            if choice == "yes":
                Configuration.merge_based = True
            else:
                Configuration.merge_based = False
            # 4/ Data path
            Configuration.row_data_path = input("Please specify path to data : ")



