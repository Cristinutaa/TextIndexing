import json
import math
import numpy as np
import os
import random
from sklearn.externals import joblib
from sklearn.neighbors import NearestNeighbors
from sortedcontainers import SortedDict
import time

#personal imports
import configuration

index_vectors = dict()
context_vectors = dict()
model = []


def build_index_and_context_vectors(inverted_dictionary, dimension_vector=100, nb_non_nulls=4):
    """
    :param inverted_dictionary: IF
    :param dimension_vector: (int) the dimension for the index and context vectors (default=100)
    :param nb_non_nulls: (int) the number of non null elements inside an index vector (default=4)
    :return: (tuple) one dictionary (key=doc_id, value=index_vector) & one dictionary (key=term, value=context_vector)
    """
    for term, pl in inverted_dictionary.items():
        context_vectors[term] = np.zeros(dimension_vector, dtype=int)
        for doc_id in pl.keys():
            if doc_id in index_vectors.keys():
                context_vectors[term] += index_vectors[doc_id]
            else:
                index_vectors[doc_id] = generate_index_vector(dimension_vector, nb_non_nulls)
                context_vectors[term] += index_vectors[doc_id]
    joblib.dump(index_vectors, r'resources/index_vectors.joblib')
    joblib.dump(context_vectors, r'resources/context_vectors.joblib')
    return index_vectors, context_vectors


def check_terms_exist(terms_to_check, context_vectors):
    existing_terms = []
    for term_to_check in terms_to_check:
        if term_to_check in context_vectors.keys():
            existing_terms.append(term_to_check)
        else:
            print(term_to_check + "doesn't belong to the corpus/inverted_file.")
    return existing_terms


def find_similar_vectors(terms_of_query, context_vectors, model):
    """
    :param terms_of_query: (list of strings)
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :param model: the KNN model already trained
    :return:
    """
    start_time = time.time()
    context_vectors_for_specific_terms = [context_vectors[term] for term in terms_of_query]
    indexes = model.kneighbors(context_vectors_for_specific_terms, return_distance=False)
    terms = list(context_vectors.keys())
    for i, term_of_query in enumerate(terms_of_query):
        for index in indexes[i]:
            print("term:", term_of_query, "- similar term:", terms[index])
    print("time spent:", time.time() - start_time)


def generate_index_vector(dimension_vector, nb_non_nulls):
    """
    :param dimension_vector: the dimension for the index and context vectors (default=100)
    :param nb_non_nulls: the number of non null elements inside an index vector (default=4)
    :return: an example of index_vector
    """
    index_vector = np.zeros(dimension_vector, dtype=int)
    nb_negative_value = math.ceil(nb_non_nulls/2)
    index_vector[range(nb_non_nulls)] = [-1 for i in range(nb_negative_value)] + [1 for i in range(nb_non_nulls-nb_negative_value)]
    random.shuffle(index_vector)
    return index_vector


def train_clustering_algorithm(context_vectors, n_neighbors=5):
    """
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :param n_neighbors: (int) the number of terms to send back (default=5)
    :return:
    """
    neigh = NearestNeighbors(n_neighbors=n_neighbors)
    neigh.fit(list(context_vectors.values()))
    joblib.dump(neigh, r'resources/model_random_indexing.joblib')
    return neigh


if __name__ == "__main__":
    json_path = configuration.get_json_path()
    for file in os.listdir(json_path):
        if file == "dict_with_dict.json":
            file = open(json_path + "\\" + file)
            inverted_file_dict = json.load(file)
            inverted_file_dict = SortedDict(inverted_file_dict)
        elif file == "dict_with_list.json":
            file = open(json_path + "\\" + file)
            inverted_file_list = json.load(file)
        elif file == "model_random_indexing.joblib":
            file = json_path + "\\" + file
            model = joblib.load(file)
        elif file == "index_vectors.joblib":
            file = json_path + "\\" + file
            index_vectors = joblib.load(file)
        elif file == "context_vectors.joblib":
            file = json_path + "\\" + file
            context_vectors = joblib.load(file)
    print("inverted_file_dict length:", len(inverted_file_dict))

    generate_new_model = False
    if not(index_vectors) or not(context_vectors):
        generate_new_model = True
        startTime = time.time()
        index_vectors, context_vectors = build_index_and_context_vectors(inverted_file_dict)
        print("time spent to build vectors:", time.time() - startTime)

    if not(model) or generate_new_model:
        startTime = time.time()
        model = train_clustering_algorithm(context_vectors)
        print("time spent to train the model:", time.time() - startTime)

    while input("Do you want to find similar terms ? (yes/no)\n").lower() == "yes":
        query = input("Tap a list of terms ? (separated by 'and')\n").lower()
        terms = check_terms_exist(list(set(query.split(" and "))), context_vectors)
        print("Your terms are:", terms)
        find_similar_vectors(terms, context_vectors, model)

