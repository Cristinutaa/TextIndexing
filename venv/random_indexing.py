import numpy as np
import random
from sklearn.neighbors import NearestNeighbors


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


def find_similar_vectors(terms_of_query, samples, n_neighbors=5):
    """
    :param terms_of_query: (list of strings)
    :param samples: one dictionary (key=term, value=context_vector)
    :param n_neighbors: (int) the number of terms to send back (default=5)
    :return:
    """
    neigh = NearestNeighbors(n_neighbors=n_neighbors)
    neigh.fit(np.fromiter(samples.values(), dtype=float))
    context_vectors_for_specific_terms = [samples[term] for term in terms_of_query]
    indexes = neigh.kneighbors(context_vectors_for_specific_terms, return_distance=False)
    print(indexes)


def generate_index_vector(dimension_vector, nb_non_nulls):
    """
    :param dimension_vector: the dimension for the index and context vectors (default=100)
    :param nb_non_nulls: the number of non null elements inside an index vector (default=4)
    :return: an example of index_vector
    """
    index_vector = np.zeros(dimension_vector, dtype=int)
    index_vector[range(nb_non_nulls)] = [random.choice([-1, 1]) for i in range(nb_non_nulls)]
    random.shuffle(index_vector)
    return index_vector

