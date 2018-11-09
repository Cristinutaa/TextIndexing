import json
from nltk.stem import PorterStemmer
import numpy as np
import os
import time
import random
from sortedcontainers import SortedDict

#personal imports
import configuration
import dataReading
import random_indexing


dict_struct = dict()
corpus_by_doc_id = dict()
dict_list = dict()
context_vectors = dict()
index_vectors = dict()


def display_result_query(ranked_docs):
    """
    :param ranked_docs: sorted list of id of documents
    :return: None -  display text
    """
    print("The result of your query:")
    rank = 0
    for doc_id in ranked_docs:
        rank = rank+1
        print("RANK:" + str(rank) + " - DOC_ID:"+str(doc_id))
    display_docs = True if input("Do you want to display the content of the docs? (yes/no)\n").lower() == "yes" else False
    if display_docs:
        rank = 0
        for doc_id in ranked_docs:
            rank = rank+1
            print("RANK:" + str(rank) + " - DOC_ID:"+str(doc_id))
            print(corpus_by_doc_id[doc_id])


def generate_query(randomly=True):
    """
    :param randomly: Default = True. If False, the user will choose the terms of the query.
    :return: String containing a certain number of terms, separated with "OR"
    """
    if randomly:
        nb_terms = random.randint(1, 4)
        terms = []
        for i in range(0, nb_terms):
            terms.append(random.choice(dict_struct.keys()))
        return " OR ".join(terms)
    else:
        query = input("Please write your query (terms are separated by 'OR')\n")
        return query.upper()


def naive(query, dict_struct):
    """
    Words of the query are only separated with OR. The keyword OR is capitalized since or is just a word.
    :param query: string that contains the query : w1 [OR w2 OR w3 ...]
    :param dict_struct: First structure of the IF whose values are also dicts
    :return: list of ranked docs id and time spent to process the request 
    """
    startTime = time.time()
    #ps = PorterStemmer()
    docs_score = {}
    query_words = prepare_query(query)
    # We remove the query terms that are not in dict_struct
    query_words = remove_nonexisting_terms(query_words, dict_struct)
    for qt in query_words:
        #qt = ps.stem(qt) # finally, we stem the word
        # We have to check if at least one doc contains the qt
        for doc in dict_struct[qt].keys():
            if doc in docs_score:
                docs_score[doc] += dict_struct[qt][doc]
            else:
                docs_score[doc] = dict_struct[qt][doc]

    scores_list = [] # list of pairs (count,doc_id)
    nwords = len(query_words)
    for k,v in docs_score.items():
        scores_list.append((v/nwords, k))
    scores_list.sort()
    """But we only want the ranked document id, not the scores"""
    ranked_docs = []
    for pair in reversed(scores_list): # scores must be in decreasing order
        ranked_docs.append(pair[1])
    timespent = time.time() - startTime
    return ranked_docs, timespent


def fagins_topk(query, K, dict_struct, dict_list):
    """

    :param query:
    :param K: Capital K to avoid confusing with k variable used in loops
    :param dict_struct:
    :param dict_list:
    :return:
    """
    startTime = time.time()
    C = {}
    M = {}
    qts = prepare_query(query) # query terms dict_struct

    # We remove the query terms that are not in dict_struct
    qts = remove_nonexisting_terms(qts, dict_struct)
    print("kept qts:", qts)

    # We get the lists of pairs [docid, count of qt in doc] for the query terms
    qtdoc_ranking = [] # each element = a list of pairs [docid, count of qt in doc] for respective qt, sorted by score
    qtdoc_nb = [] # number of docs for each query term that are in C
    print("qts now:", qts)
    for qt in qts:
        qtdoc_ranking.append(dict_list[qt])
        qtdoc_nb.append(len(dict_list[qt]))
    # We fill the 'implicit list' used for Fagin's top-k
    implicit_list = []
    # --- We have to watch all lists in parallel. Number of 'watches' is the max size of a list.
    filling_loops = max(qtdoc_nb)
    for j in range(filling_loops):
        for i in range(len(qtdoc_ranking)):
            if j<len(qtdoc_ranking[i]):
                implicit_list.append(qtdoc_ranking[i][j])
    #print("implicit_list:", implicit_list) # OK

    # "Repeat until |C| = K"
    seen_for_terms = {}  # keys are doc ids, values are number of terms for which the docs have been seen
    for pair in implicit_list:
        if len(C.keys()) == K:
            break
        if pair[0] not in M:
            M[pair[0]] = pair[1]
            seen_for_terms[pair[0]] = 1
        else:
            M[pair[0]] += pair[1]
            seen_for_terms[pair[0]] += 1
        if seen_for_terms[pair[0]] == len(qts):
            C[pair[0]] = M[pair[0]]
            del M[pair[0]]
        # print("pair:", pair)
        # print("M:", M)
        # print("C:", C)
        # print("seen_for_terms:", seen_for_terms)

    # For each (pair ) d in M, we (re)compute the score
    for k,v in M.items():
        C[k] = 0
        for qt in qts: # for each dict of each qt
            # qt is in dict_struct, according to function remove_nonexisting_terms
            C[k] += dict_struct[qt].get(k,0)

    # We want to get pairs (docscore, docid)
    # Since for now, C is composed of summed score, we will divide by #qts to get the average scores.
    scores_list = []  # list of pairs ocscore, docid)
    nwords = len(qts)
    for k, v in C.items():
        scores_list.append((v / nwords, k))
    scores_list.sort()
    """But we only want the ranked document id, not the scores. And until k elements"""
    ranked_docs = []
    for pair in reversed(scores_list):  # scores must be in decreasing order
        ranked_docs.append(pair[1])
        if len(ranked_docs) == K:
            break
    timespent = time.time() - startTime
    return ranked_docs, timespent


def prepare_query(query):
    """
    :param query: the query in string to convert into a list of "conjuncted" words/terms
    :return: a set of query terms
    """
    query_words = query.split(" OR ")
    query_words = list(set(query_words))  # only keeps unique words
    for i in range(len(query_words)):
        query_words[i] = query_words[i].lower()
        query_words[i] = query_words[i].strip()
    #random_indexing.find_similar_vectors(query_words, context_vectors)
    return query_words


def remove_nonexisting_terms(qts, dict_struct):
    """
    Removes from qts the terms not in dict_struct
    :param qts: query terms list where we remove the non-existing terms
    :return:
    """
    newqts = qts.copy()
    for qt in qts:
        if qt not in dict_struct:
            newqts.remove(qt)
    return newqts


if __name__ == "__main__":
    json_path = configuration.get_json_path()

    for file in os.listdir(json_path):
        if file == "dict_with_dict.json":
            file = open(json_path + "\\" + file)
            dict_struct = json.load(file)
            dict_struct = SortedDict(dict_struct)
        elif file == "dict_with_list.json":
            file = open(json_path + "\\" + file)
            dict_list = json.load(file)
        elif file == "corpus_by_doc_id.json":
            file = open(json_path + "\\" + file)
            corpus_by_doc_id = json.load(file)
        elif file == "index_vectors.json":
            file = open(json_path + "\\" + file)
            index_vectors = json.load(file)
        elif file == "context_vectors.json":
            file = open(json_path + "\\" + file)
            context_vectors = json.load(file)
    print("dict_struct length:", len(dict_struct))
    print("dict_list length:", len(dict_list))
    print("corpus_by_doc_id length:", len(corpus_by_doc_id))

    startTime = time.time()
    index_vectors, context_vectors = random_indexing.build_index_and_context_vectors(dict_struct)
    print("time spent:", time.time() - startTime)

    query = generate_query(True if input("Do you want to randomly generate a query ? (yes/no)\n").lower() == "yes" else False)
    print("Your query is : " + query)
    opt = -117
    while opt not in [0,1]:
        opt = int(input("Do you wanna use naive or fagin's algorithm? Naive:0, Fagin's:1\n"))
    if opt == 0:
        ranked_docs, duration = naive(query, dict_struct)
    else:
        ranked_docs, duration = fagins_topk(query, 10, dict_struct, dict_list)
    display_result_query(ranked_docs)
    print("time spent:", duration)
