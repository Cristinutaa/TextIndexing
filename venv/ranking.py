import json
from nltk.stem import PorterStemmer
import numpy as np
import os
import sys
import time
import random
from sortedcontainers import SortedDict
from sklearn.externals import joblib
import xml.etree.ElementTree as ET
import operator

#personal imports
import configuration
import dataReading
import random_indexing


dict_struct = dict()
doc_id_by_file = dict()
corpus_by_doc_id = dict()
dict_list = dict()


def display_ranked_docs(ranked_docs):
    rank = 0
    for doc_id in ranked_docs:
        rank = rank + 1
        print("RANK:" + str(rank) + " - DOC_ID:" + str(doc_id))


def display_result_query(ranked_docs):
    """
    :param ranked_docs: sorted list of id of documents
    :return: None -  display text
    """
    print("The result of your query:")
    display_ranked_docs(ranked_docs)
    while input("Do you want to display the content of one document ? (yes/no)\n").lower() == "yes":
        try:
            print("REMINDER : the result of your query:")
            display_ranked_docs(ranked_docs)
            doc_id = int(input("What is the id of the document to display ? (ex : 2)\n"))
            rank = ranked_docs.index(str(doc_id))
            print("RANK:" + str(rank+1) + " - DOC_ID:" + str(doc_id))
            display_one_document(str(doc_id))
        except ValueError:
            print("The id of the document doesn't belong to the result of your query.")


def display_one_document(doc_id):
    start_time = time.time()
    path_to_file = doc_id_by_file[doc_id]
    with open(path_to_file, "r") as my_file:
        data = "<root>" + my_file.read() + "</root>"
        root = ET.fromstring(data)
        for doc in root.findall("DOC"):
            if doc.find("DOCID").text.split()[0] == doc_id:
                text = ""
                for node in doc:
                    for p in node.findall("P"):
                        text = text + ' ' + p.text
                print(text)
                print("time spent to display the content:", time.time() - start_time)


def generate_query(randomly=True, nb_terms=None):
    """
    :param randomly: Default = True. If False, the user will choose the terms of the query.
    :return: String containing a certain number of terms, separated with "OR"
    """
    if randomly and nb_terms:
        terms = random.sample(dict_struct.keys(), nb_terms)
        return __prepare_query__(" OR ".join(terms), True)
    elif randomly:
        nb_terms = random.randint(1, 4)
        terms = random.sample(dict_struct.keys(), nb_terms)
        return __prepare_query__(" OR ".join(terms), True)
    else:
        query = input("Please write your query (terms are separated by 'OR')\n")
        return __prepare_query__(query.upper(), False)



def naive(query, dict_struct):
    """
    Words of the query are only separated with OR. The keyword OR is capitalized since or is just a word.
    :param query: string that contains the query : w1 [OR w2 OR w3 ...]
    :param dict_struct: First structure of the IF whose values are also dicts
    :return: list of ranked docs id and time spent to process the request 
    """
    startTime = time.time()
    docs_score = {}
    # We remove the query terms that are not in dict_struct
    query_words = __remove_nonexisting_terms__(query, dict_struct)
    for qt in query_words:
        # print("final word:", qt)
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

    # We remove the query terms that are not in dict_struct
    qts = __remove_nonexisting_terms__(query, dict_struct)
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
            # qt is in dict_struct, according to function __remove_nonexisting_terms__
            C[k] += dict_struct[qt].get(k,0)

    # We want to get pairs (docscore, docid)
    # Since for now, C is composed of summed score, we will divide by #qts to get the average scores.
    scores_list = []  # list of pairs doc scores, docid)
    nwords = len(qts)
    for k, v in C.items():
        scores_list.append((v / nwords, k))
    scores_list.sort()
    """But we only want the ranked document id, not the scores."""
    ranked_docs = []
    for pair in reversed(scores_list):  # scores must be in decreasing order
        ranked_docs.append(pair[1])
    timespent = time.time() - startTime
    return ranked_docs, timespent


def __prepare_query__(query, random=True):
    """
    :param query: the query in string to convert into a list of "conjuncted" words/terms
    :return: a set of query terms
    """
    ps = PorterStemmer()  # if configuration True, it is used, otherwise not.
    query_words = query.split(" OR ")
    query_words = list(set(query_words))  # only keeps unique words
    for i in range(len(query_words)):
        query_words[i] = query_words[i].lower()
        query_words[i] = query_words[i].strip()
        if configuration.stemming and not random:
            query_words[i] = ps.stem(query_words[i]) # finally, we stem the word
    if configuration.random_indexing:
        _, context_vectors, model = random_indexing.generate_vectors_and_model(configuration.dimension_vector_random_indexing)
        query_words = random_indexing.find_similar_terms(query_words, context_vectors, model)
    print("query words :", query_words)
    return query_words


def __remove_nonexisting_terms__(qts, dict_struct):
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


def fagins_ta(query, K, dict_struct, dict_list, epsilon=None):
    """
    Fagin's threshold algorithm
    :param query: query in the form t1 OR t2 OR t3...
    :param K: Capital K to avoid confusing with k variable used in loops
    :param dict_struct:
    :param dict_list:
    :param epsilon: if None, we don't use an epsilon. Else, replace loop condition ">=tau" by ">=tau/(1+epsilon)"
    :return:
    Extreme cases, not specified in FA algorithm about while computing tau for one loop:
    we exclude a qt for the computation of tau during the current loop:
    - When there is no next doc for the qt
    - When the next doc is the first doc (so when the qt list has not been reached yet)
    """
    #
    qts = __remove_nonexisting_terms__(query, dict_struct)  # We remove the query terms that are not in dict_struct
    nb_qts = len(qts)
    finish_qts = set([])  # qts whose list is entirely browsed

    # Variables' initialization: from algorithm and also intermediary variables
    startTime = time.time()
    C = {}  # a dict whose keys are docs d, values are mu(d). It also contains docs whose mu has been computed
    computed_docs = []  # docs whose score has been computed. Not all are in C : those that have been removed.
    tau = sys.maxsize
    mu_min = sys.maxsize  # It is also the minimum score in C
    firster_for_at_least_one_doc = []  # the list of qts whose loop for which we compute at least one mu_d
    j = 0  # n° of while loop "Repeat until k docs in C [...]"

    criterion = K
    if epsilon:
        criterion = tau / (1 + epsilon)

    # The big loop
    while not (len(C.keys()) == criterion and mu_min >= tau) and len(finish_qts) < nb_qts:  # Repeat until k docs in C...
        # ... and minimum score mu is >= tau and the qts lists still have docs to compute
        mu_min, _ = __get_mu_min_d_min__(C)
        # print("mu_min:", mu_min)
        # print("\n\n ----- Repeat until k docs in C and minimum score mu is >= tau -----")
        for qt in qts:  # Sorted access in parallel to each query term
            # print("--- Sorted access in parallel to each query term. qt:", qt, "---")
            if j < len(dict_list[qt]):
                d = dict_list[qt][__next_studied_term_index__(dict_list[qt], computed_docs, j)][
                    0]  # Let d be the doc met
                if d not in C:  # (We check of d score is not already computed)
                    if qt not in firster_for_at_least_one_doc:
                        firster_for_at_least_one_doc.append(qt)
                    mud = 0  # random access to all remaining qt to compute the combined score mu(d)
                    for qtrand in qts:
                        mud += dict_struct[qtrand].get(d,0)
                    mud /= nb_qts
                    computed_docs.append(d)
                    if len(C) < K:
                        C[d] = mud
                        mu_min, _ = __get_mu_min_d_min__(C)
                    else:
                        mu_min, d_min = __get_mu_min_d_min__(
                            C)  # We store the doc from C with the min score as well as the min score for instruction below
                        del C[d_min]
                        C[d] = mud
                        mu_min, _ = __get_mu_min_d_min__(C)
            else:
                finish_qts.add(qt)
                pass
            # print("C:", C)
            # print("mu_min:", mu_min)
            # print("computed_docs:", computed_docs)
            if len(firster_for_at_least_one_doc) == nb_qts:
                # if at_least_one_seen_everywhere:
                tau = 0

                for qt in qts:
                    # print("for qt", qt)
                    next_studied_qt = __next_studied_term_index__(dict_list[qt], computed_docs, j)
                    if next_studied_qt == -1 or next_studied_qt == 0: # If there is no nex doct for the current qt or
                                                                    # the next doc is the first doc, we ignore it
                        finish_qts.add(qt)
                    else:
                        tau += dict_list[qt][next_studied_qt - 1][1]
                tau /= nb_qts
                # print("tau:", tau)
        mu_min, _ = __get_mu_min_d_min__(C)
        j += 1

    # Preparing the results
    scores_list = []  # list of pairs mu(d), d
    for k, v in C.items():
        scores_list.append((v, k))
    scores_list.sort()
    """But we only want the ranked document id, not the scores. And until K elements"""
    ranked_docs = []
    for pair in reversed(scores_list):  # scores must be in decreasing order
        ranked_docs.append(pair[1])
        if len(ranked_docs) == K:
            break
    timespent = time.time() - startTime
    return ranked_docs, timespent


def __word_dict_2_word_list__(word_dict):
    """
    Convert a value of dict_struct to the associated value of dict_list
    :param word_dict: a dict of pairs docid-word_score
    :return: a list where pairs docid-word_score are sorted by word_score
    """
    word_list = []
    for d, sc in word_dict.items():
        word_list.append([d, sc])
    word_list.sort(key=operator.itemgetter(1))
    word_list.reverse()
    return word_list


def __get_mu_min_d_min__(C):
    """
    :param C:
    """
    mu_min = sys.maxsize
    d_min = ''
    for d in C:
        if mu_min > C[d]:
            mu_min = C[d]
            d_min = d
    return mu_min, d_min


def __next_studied_term_index__(qt_doc_ranking, computed_docs, j):
    """Return the minimum index/position among those of the documents that are in the list qt_doc_ranking.
    Ex: For the list [['2', 0.9], ['5', 0.8], ['6', 0.7], ['4', 0.6], ['1', 0.5], ['3', 0.4]] and with computed_docs = ['2', '6'],
    the returned value will be 1 (the position of ['5', 0.8])
    """
    next_studied_ind = j
    try:
        while qt_doc_ranking[next_studied_ind][0] in computed_docs:
            next_studied_ind += 1
    except:  # It happens that the list has no more next doc
        return -1
    return next_studied_ind


def ask_query():
    """A function to represent the process of asking queries to user"""
    query = generate_query(
        True if input("Do you want to randomly generate a query ? (yes/no)\n").lower() == "yes" else False)
    #print("Your query is : " + query)
    opt = -117
    K = -117
    epsilon = None
    while opt not in [0, 1, 2]:
        opt = int(input("Do you want to use naive, fagin's or fagin's threshold algorithm? "
                        "Naive:0, Fagin's:1, Fagin's threshold:2 \n"))
    if opt == 0:
        ranked_docs, duration = naive(query, dict_struct)
    elif opt == 1:
        K = int(input("Please enter K:  "))
        ranked_docs, duration = fagins_topk(query, K, dict_struct, dict_list)
    else:
        K = int(input("Please enter K:  "))
        try:
            epsilon = float(input("Please enter an epsilon (anything that's not a number for not using it): \n"))
        except:
            epsilon = None
        ranked_docs, duration = fagins_ta(query, K, dict_struct, dict_list, epsilon)
    display_result_query(ranked_docs)
    print("size of result:", len(ranked_docs))
    print("time spent:", duration)


def get_structures():
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
        elif file == "doc_id_by_file.json":
            file = open(json_path + "\\" + file)
            doc_id_by_file = json.load(file)
    print("dict_struct length:", len(dict_struct))
    print("dict_list length:", len(dict_list))
    print("corpus_by_doc_id length:", len(corpus_by_doc_id))
    return dict_struct, dict_list, corpus_by_doc_id


if __name__ == "__main__":
    dict_struct, dict_list, corpus_by_doc_id = get_structures()
    while True:
        print("-------------- ASKING A QUERY TO THE USER ------------------")
        ask_again = True if input("Do you want to query something? (yes/no)\n").lower() == "yes" \
            else False
        if not ask_again:
            print("Fine, have a nice day!")
            break
        ask_query()



