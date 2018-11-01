stemming = False
default = True
default_row_data_path = r'F:\laela\Desktop\latimes\latimes'
default_json_path = r'.\resources'


def get_row_data_path():
    """
    :return: A string which is the path to the row data files.
    """
    if default:
        print("We are treating the data from " + default_row_data_path)
        return default_row_data_path
    else:
        row_data_path = input("Please write the path to the folder that contains the data.\n")
        print("We are treating the data from " + row_data_path)
        return row_data_path


def get_json_path():
    """
    :return: A string which is the path to the json files.
    """
    if default:
        print("We are treating the data from " + default_json_path)
        return default_json_path
    else:
        json_path = input("Please write the path to the folder that contains the json files.\n")
        print("We are treating the data from " + json_path)
        return json_path
