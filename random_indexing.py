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


class Random_Indexing:
    def __init__(self, dimension_vector, nb_non_nulls=4):
        self.index_vectors = dict()
        self.context_vectors = dict()
        self.model = []
        self.dimension_vector = dimension_vector
        self.nb_non_nulls = nb_non_nulls

    def build_index_and_context_vectors(self, inverted_dictionary):
        """
        :param inverted_dictionary: IF as a dictionary of dictionary
        :return: (tuple) one dictionary (key=doc_id, value=index_vector) & one dictionary (key=term, value=context_vector)
        """
        for file in os.listdir(Configuration.json_path):
            if file == "model_random_indexing.joblib" or file == "index_vectors.joblib" or file == "context_vectors.joblib":
                os.remove(Configuration.json_path + "\\" + file)
        for term, pl in inverted_dictionary.items():
            self.context_vectors[term] = np.zeros(self.dimension_vector, dtype=int)
            for doc_id, frequency in pl.items():
                if doc_id in self.index_vectors.keys():
                    self.context_vectors[term] += (self.index_vectors[doc_id]*frequency)
                else:
                    self.index_vectors[doc_id] = self.__generate_index_vector__()
                    self.context_vectors[term] += (self.index_vectors[doc_id]*frequency)
        self.__save_index_and_context_vectors__()

    def __check_terms_exist__(self, terms_to_check):
        """
        Used by the method find_similar_terms
        :param terms_to_check: (list of string) one string represents one term of the query
        :return: (list of string) a sublist of terms_to_check (some words don't belong to the corpus)
        """
        existing_terms = []
        for term_to_check in terms_to_check:
            if term_to_check in self.context_vectors.keys():
                existing_terms.append(term_to_check)
            else:
                print(term_to_check + "doesn't belong to the corpus/inverted_file.")
        return existing_terms

    def find_similar_terms(self, terms_of_query):
        """
        :param terms_of_query: (list of strings)
        :return: (list of string) represents the terms of the query and the similar terms
        """
        start_time = time.time()
        terms_of_query = self.__check_terms_exist__(terms_of_query)
        try:
            context_vectors_for_specific_terms = [self.context_vectors[term] for term in terms_of_query]
            _, indexes = self.model.kneighbors(context_vectors_for_specific_terms, return_distance=True)
            terms = list(self.context_vectors.keys())
            similar_terms = []
            for i, term_of_query in enumerate(terms_of_query):
                result_for_term = "term: " + term_of_query + " - similar terms: "
                for j, index in enumerate(indexes[i]):
                    result_for_term += terms[index] + " / "
                    similar_terms.append(terms[index])
                #print(result_for_term)
            #print("time spent:", time.time() - start_time)
            return similar_terms
        except ValueError:
            #it means that __check_terms_exist__ at send back an empty list so there is no result for the terms
            return []

    def __generate_index_vector__(self):
        """
        Used by the method build_index_and_context_vectors
        :param dimension_vector: the dimension for the index and context vectors (default=100)
        :param nb_non_nulls: the number of non null elements inside an index vector (default=4)
        :return: an example of index_vector
        """
        index_vector = np.zeros(self.dimension_vector, dtype=int)
        nb_negative_value = math.ceil(self.nb_non_nulls/2)
        index_vector[range(self.nb_non_nulls)] = [-1 for i in range(nb_negative_value)] + [1 for i in range(self.nb_non_nulls-nb_negative_value)]
        random.shuffle(index_vector)
        return index_vector

    def download_vectors_and_model(self):
        json_path = Configuration.json_path
        for file in os.listdir(json_path):
            if file == "model_random_indexing.joblib":
                file = json_path + "\\" + file
                self.model = joblib.load(file)
            elif file == "index_vectors.joblib":
                file = json_path + "\\" + file
                self.index_vectors = joblib.load(file)
            elif file == "context_vectors.joblib":
                file = json_path + "\\" + file
                self.context_vectors = joblib.load(file)

        if not(self.index_vectors) or not(self.context_vectors) or len(list(self.context_vectors.values())[0])!=self.dimension_vector:
            index_vectors_not_downloadable = str(not(self.index_vectors))
            context_vectors_not_downloadable = str(not(self.context_vectors))
            dimension_vector_incorrect = str(len(list(self.context_vectors.values())[0])!=self.dimension_vector)
            message = 'index_vectors_not_downloadable: ' + index_vectors_not_downloadable + '\n'
            message = message + 'context_vectors_not_downloadable:' + context_vectors_not_downloadable + '\n'
            message = message + 'dimension_vector_incorrect:' + dimension_vector_incorrect
            raise Exception('The downloading during Random indexing wzs wrong', message)

        if not (self.model):
            start_time = time.time()
            self.__train_clustering_algorithm__()
            #print("time spent to train the model:", time.time() - start_time)

    def __save_index_and_context_vectors__(self):
        """
        Used by the method build_index_and_context_vectors.
        Once the index vectors and context vectors have been computed, we should save it as joblib
        :return: None
        """
        joblib.dump(self.index_vectors, Configuration.json_path + r'/index_vectors.joblib')
        joblib.dump(self.context_vectors, Configuration.json_path + r'/context_vectors.joblib')

    def __train_clustering_algorithm__(self, n_neighbors=5):
        """
        Used by the method download_vectors_and_model
        :param n_neighbors: (int) the number of terms to send back (default=5)
        :return: None
        """
        self.model = NearestNeighbors(n_neighbors=n_neighbors)
        self.model.fit(list(self.context_vectors.values()))
        joblib.dump(self.model, Configuration.json_path + r'/model_random_indexing.joblib')


if __name__ == "__main__":
    Configuration.json_path = input("Please specify path where to save/load jolib : ")
    Configuration.dimension_vector_random_indexing = input("Specify the dimension of vector indexing (must be a nb) : ")
    ri = Random_Indexing(Configuration.dimension_vector_random_indexing)
    ri.download_vectors_and_model()

    while input("Do you want to find similar terms ? (yes/no)\n").lower() == "yes":
        query = input("Tap a list of terms ? (separated by 'and')\n").lower()
        terms = list(set(query.split(" and ")))
        print("Your terms are:", terms)
        print(ri.find_similar_terms(terms))

