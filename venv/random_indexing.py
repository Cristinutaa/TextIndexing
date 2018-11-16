import json
import math
import numpy as np
import os
import random
from sklearn.neighbors import NearestNeighbors
from sortedcontainers import SortedDict
import time

#personal imports
import configuration

index_vectors = dict()
context_vectors = dict()


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
    return index_vectors, context_vectors


def find_similar_vectors(terms_of_query, context_vectors, n_neighbors=5):
    """
    :param terms_of_query: (list of strings)
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :param n_neighbors: (int) the number of terms to send back (default=5)
    :return:
    """
    start_time = time.time()
    neigh = NearestNeighbors(n_neighbors=n_neighbors)
    neigh.fit(list(context_vectors.values()))
    print("time spent to train KNN:", time.time() - start_time)
    context_vectors_for_specific_terms = [context_vectors[term] for term in terms_of_query]
    print("time spent to get the context vectors for specific terms:", time.time() - start_time)
    indexes = neigh.kneighbors(context_vectors_for_specific_terms, return_distance=False)
    print("time spent to find similar context_vectors:", time.time() - start_time)
    terms = list(context_vectors.keys())
    print("time spent to convert the values as list terms:", time.time() - start_time)
    print(indexes)
    for indexes_for_one_term in indexes:
        for index in indexes_for_one_term:
            print(index)
            print("term:", terms[index])
    print("time spent final:", time.time() - start_time)


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
    print("inverted_file_dict length:", len(inverted_file_dict))

    startTime = time.time()
    index_vectors, context_vectors = build_index_and_context_vectors(inverted_file_dict)
    print("time spent:", time.time() - startTime)

    while input("Do you want to find similar terms ? (yes/no)\n").lower() == "yes":
        query = input("Tap a list of terms ? (separated by 'and')\n").lower()
        terms = list(set(query.split(" and ")))
        print("Your terms are:", terms)
        find_similar_vectors(terms, context_vectors)

