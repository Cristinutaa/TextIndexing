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
from configuration import Configuration


def build_index_and_context_vectors(inverted_dictionary, dimension_vector, nb_non_nulls=4):
    """
    :param inverted_dictionary: IF
    :param dimension_vector: (int) the dimension for the index and context vectors (default=100)
    :param nb_non_nulls: (int) the number of non null elements inside an index vector (default=4)
    :return: (tuple) one dictionary (key=doc_id, value=index_vector) & one dictionary (key=term, value=context_vector)
    """
    index_vectors = dict()
    context_vectors = dict()
    for term, pl in inverted_dictionary.items():
        context_vectors[term] = np.zeros(dimension_vector, dtype=int)
        for doc_id in pl.keys():
            if doc_id in index_vectors.keys():
                context_vectors[term] += index_vectors[doc_id]
            else:
                index_vectors[doc_id] = generate_index_vector(dimension_vector, nb_non_nulls)
                context_vectors[term] += index_vectors[doc_id]
    joblib.dump(index_vectors, Configuration.json_path + r'/index_vectors.joblib')
    joblib.dump(context_vectors, Configuration.json_path + r'/context_vectors.joblib')
    return index_vectors, context_vectors


def check_terms_exist(terms_to_check, context_vectors):
    """
    :param terms_to_check: (list of string) one string represents one term of the query
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :return: (list of string) a sublist of terms_to_check (some words don't belong to the corpus)
    """
    existing_terms = []
    for term_to_check in terms_to_check:
        if term_to_check in context_vectors.keys():
            existing_terms.append(term_to_check)
        else:
            print(term_to_check + "doesn't belong to the corpus/inverted_file.")
    return existing_terms


def find_similar_terms(terms_of_query, context_vectors, model):
    """
    :param terms_of_query: (list of strings)
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :param model: the KNN model already trained
    :return: (list of string) represents the terms of the query and the similar terms
    """
    start_time = time.time()
    context_vectors_for_specific_terms = [context_vectors[term] for term in terms_of_query]
    _, indexes = model.kneighbors(context_vectors_for_specific_terms, return_distance=True)
    terms = list(context_vectors.keys())
    similar_terms = []
    for i, term_of_query in enumerate(terms_of_query):
        result_for_term = "term: " + term_of_query + " - similar terms: "
        for j, index in enumerate(indexes[i]):
            result_for_term += terms[index] + " / "
            similar_terms.append(terms[index])
        #print(result_for_term)
    #print("time spent:", time.time() - start_time)
    return similar_terms


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


def generate_vectors_and_model(dimension_vector=100):
    index_vectors = dict()
    context_vectors = dict()
    model = []
    json_path = Configuration.json_path
    for file in os.listdir(json_path):
        if file == "dict_with_dict.json":
            file = open(json_path + "\\" + file)
            inverted_file_dict = json.load(file)
            inverted_file_dict = SortedDict(inverted_file_dict)
        elif file == "model_random_indexing.joblib":
            file = json_path + "\\" + file
            model = joblib.load(file)
        elif file == "index_vectors.joblib":
            file = json_path + "\\" + file
            index_vectors = joblib.load(file)
        elif file == "context_vectors.joblib":
            file = json_path + "\\" + file
            context_vectors = joblib.load(file)

    generate_new_model = False
    if not(index_vectors) or not(context_vectors) or len(list(context_vectors.values())[0])!=dimension_vector:
        generate_new_model = True
        start_time = time.time()
        index_vectors, context_vectors = build_index_and_context_vectors(inverted_file_dict, dimension_vector)
        #print("time spent to build vectors:", time.time() - start_time)

    if not (model) or generate_new_model:
        start_time = time.time()
        model = train_clustering_algorithm(context_vectors)
        #print("time spent to train the model:", time.time() - start_time)

    return index_vectors, context_vectors, model


def train_clustering_algorithm(context_vectors, n_neighbors=5):
    """
    :param context_vectors: one dictionary (key=term, value=context_vector)
    :param n_neighbors: (int) the number of terms to send back (default=5)
    :return:
    """
    neigh = NearestNeighbors(n_neighbors=n_neighbors)
    neigh.fit(list(context_vectors.values()))
    joblib.dump(neigh, Configuration.json_path + r'/model_random_indexing.joblib')
    return neigh


if __name__ == "__main__":
    index_vectors, context_vectors, model = generate_vectors_and_model()

    while input("Do you want to find similar terms ? (yes/no)\n").lower() == "yes":
        query = input("Tap a list of terms ? (separated by 'and')\n").lower()
        terms = check_terms_exist(list(set(query.split(" and "))), context_vectors)
        print("Your terms are:", terms)
        print(find_similar_terms(terms, context_vectors, model))

