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
import random_indexing
from configuration import Configuration
from MergeBased import MergeBased


# dict_struct = dict()
# doc_id_by_file = dict()
# dict_list = dict()


class QueryProcess:
    """In this class, the two methods to use are __init__ and ask_query"""

    def __init__(self, doc_id_by_file, merge_based= None, dict_struct= None, dict_list=None):
        """
        :param doc_id_by_file: Each key is doc id, value is "la" document that contains element doc.
        :param merge_based: A prepared mergeBased instance. To specify if Configuration.merge_based = True
        :param dict_struct: If Configuration.merge_based = False, a partial representation of the IF (is updated with
        words that are in the last query); in that case don't specify it in init. Else, a representation of the IF
        :param dict_list: idem
        """
        self.doc_id_by_file = doc_id_by_file
        self.merge_based = merge_based
        self.dict_struct = dict_struct
        self.dict_list = dict_list
        # Variable values for sure:
        self.qws = [] # a variable to store list of query words
        self.ranked_docs = []  # top docs of last query
        self.duration = 0  # duration of last query
        #print("A query process has been loaded.")

    def ask_query(self):
        """A function to represent the process of asking queries to user"""

        # 1/ Getting the word queries
        q_generation = True if input(
            "Do you want to randomly generate a query ? (yes/no)\n").lower() == "yes" else False
        nb_terms = None
        candidate_terms = []  # only used when q_generation = True. In this case, will be filled.
        if q_generation:
            nb_terms = input("Please specify a number of terms (anything else for a number between 1 and 4):    ")
            try:
                nb_terms = int(nb_terms)
                if nb_terms < 1:
                    nb_terms = None
            except:
                nb_terms = None
            if Configuration.merge_based:
                candidate_terms = self.merge_based.dict.keys()
                #print("candidate terms for merged_based:",candidate_terms)
            else:
                candidate_terms = self.dict_struct.keys()
        self.qws = generate_query_terms(q_generation, nb_terms, candidate_terms)
        # print("Your query is : " + query)

        # 2/ Updating the queryProcess's fields for the ranking algorithm:
        # - update dict_struct and dict_list when we use merge-based
        # - remove the words in the query we don't know from the data when we use RAM
        self.__update_fields__()

        # 3/ Using a ranking algorithm
        opt = -117
        K = -117
        epsilon = None
        while opt not in [0, 1, 2]:
            opt = int(input("Do you want to use naive, fagin's or fagin's threshold algorithm? "
                            "Naive:0, Fagin's:1, Fagin's threshold:2 \n"))
        if opt == 0:
            self.naive()
        elif opt == 1:
            K = int(input("Please enter K:  "))
            self.fagins_topk(K)
        else:
            K = int(input("Please enter K:  "))
            try:
                epsilon = float(input("Please enter an epsilon (anything that's not a number for not using it): \n"))
            except:
                epsilon = None
            self.fagins_ta(K, epsilon)
        self.display_result_query()
        print("size of result:", len(self.ranked_docs))
        print("time spent:", self.duration)

    def naive(self):
        """
        Compute list of ranked docs id and time spent to process the request that are saved in the instance fields
        ranked_docs and duration
        """
        startTime = time.time()
        docs_score = {}
        if len(self.qws) == 0:
            return [], time.time() - startTime
        for qt in self.qws: # now we can call them query terms because the list has been filtered from words not in data
            # print("final word:", qt)
            # We have to check if at least one doc contains the qt
            for doc in self.dict_struct[qt].keys():
                if doc in docs_score:
                    docs_score[doc] += float(self.dict_struct[qt][doc])
                else:
                    docs_score[doc] = float(self.dict_struct[qt][doc])

        scores_list = []  # list of pairs (count,doc_id)
        nwords = len(self.qws)
        for k, v in docs_score.items():
            scores_list.append((float(v) / nwords, k))
        scores_list.sort()
        """But we only want the ranked document id, not the scores"""
        ranked_docs = []
        for pair in reversed(scores_list):  # scores must be in decreasing order
            ranked_docs.append(pair[1].strip())
        timespent = time.time() - startTime
        self.ranked_docs, self.duration = ranked_docs, timespent

    def fagins_topk(self, K):
        """
        Compute list of ranked docs id and time spent to process the request that are saved in the instance fields
        ranked_docs and duration
        :param K: Capital K to avoid confusing with k variable used in loops
        """
        startTime = time.time()
        C = {}
        M = {}
        #print("kept qts:", self.qws)
        if len(self.qws) == 0:
            return [], time.time() - startTime

        # We get the lists of pairs [docid, count of qt in doc] for the query terms
        qtdoc_ranking = []  # each element = a list of pairs [docid, count of qt in doc] for respective qt, sorted by score
        qtdoc_nb = []  # number of docs for each query term that are in C
        # print("qts now:", qts)
        for qt in self.qws:
            qtdoc_ranking.append(self.dict_list[qt])
            qtdoc_nb.append(len(self.dict_list[qt]))
        # We fill the 'implicit list' used for Fagin's top-k
        implicit_list = []
        # --- We have to watch all lists in parallel. Number of 'watches' is the max size of a list.
        filling_loops = max(qtdoc_nb)
        for j in range(filling_loops):
            for i in range(len(qtdoc_ranking)):
                if j < len(qtdoc_ranking[i]):
                    implicit_list.append(qtdoc_ranking[i][j])
        # print("implicit_list:", implicit_list) # OK

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
            if seen_for_terms[pair[0]] == len(self.qws):
                C[pair[0]] = M[pair[0]]
                del M[pair[0]]
            # print("pair:", pair)
            # print("M:", M)
            # print("C:", C)
            # print("seen_for_terms:", seen_for_terms)

        # For each (pair ) d in M, we (re)compute the score
        for k, v in M.items():
            C[k] = 0
            for qt in self.qws:  # for each dict of each qt
                # qt is in dict_struct, according to function __remove_nonexisting_terms__
                C[k] += float(self.dict_struct[qt].get(k, 0))

        # We want to get pairs (docscore, docid)
        # Since for now, C is composed of summed score, we will divide by #qts to get the average scores.
        scores_list = []  # list of pairs doc scores, docid)
        nwords = len(self.qws)
        for k, v in C.items():
            scores_list.append((float(v) / nwords, k))
        scores_list.sort()
        """But we only want the ranked document id, not the scores."""
        ranked_docs = []
        for pair in reversed(scores_list):  # scores must be in decreasing order
            ranked_docs.append(pair[1].strip())
            if len(ranked_docs) == K:
                break
        timespent = time.time() - startTime
        self.ranked_docs, self.duration = ranked_docs, timespent

    def fagins_ta(self, K, epsilon=None):
        """
        Fagin's threshold algorithm
        :param K: Capital K to avoid confusing with k variable used in loops
        :param epsilon: if None, we don't use an epsilon. Else, replace loop condition ">=tau" by ">=tau/(1+epsilon)"
        :return:
        Extreme cases, not specified in FA algorithm about while computing tau for one loop:
        we exclude a qt for the computation of tau during the current loop:
        - When there is no next doc for the qt
        - When the next doc is the first doc (so when the qt list has not been reached yet)
        """
        #
        startTime = time.time()
        if len(self.qws) == 0:
            return [], time.time() - startTime
        nb_qts = len(self.qws)
        finish_qts = set([])  # qts whose list is entirely browsed

        # Variables' initialization: from algorithm and also intermediary variables

        C = {}  # a dict whose keys are docs d, values are mu(d). It also contains docs whose mu has been computed
        computed_docs = []  # docs whose score has been computed. Not all are in C : those that have been removed.
        tau = sys.maxsize
        mu_min = sys.maxsize  # It is also the minimum score in C
        firster_for_at_least_one_doc = []  # the list of qts whose loop for which we compute at least one mu_d
        j = 0  # n° of while loop "Repeat until k docs in C [...]"

        criterion = tau
        if epsilon:
            criterion = tau / (1 + epsilon)

        # The big loop
        while not (len(C.keys()) == K and mu_min >= criterion) and len(
                finish_qts) < nb_qts:  # Repeat until k docs in C...
            # ... and minimum score mu is >= tau and the qts lists still have docs to compute
            mu_min, _ = get_mu_min_d_min(C)
            # print("mu_min:", mu_min)
            # print("\n\n ----- Repeat until k docs in C and minimum score mu is >= tau -----")
            for qt in self.qws:  # Sorted access in parallel to each query term
                # print("--- Sorted access in parallel to each query term. qt:", qt, "---")
                if j < len(self.dict_list[qt]):
                    d = self.dict_list[qt][next_studied_term_index(self.dict_list[qt], computed_docs, j)][
                        0]  # Let d be the doc met
                    if d not in C:  # (We check of d score is not already computed)
                        if qt not in firster_for_at_least_one_doc:
                            firster_for_at_least_one_doc.append(qt)
                        mud = 0  # random access to all remaining qt to compute the combined score mu(d)
                        for qtrand in self.qws:
                            mud += float(self.dict_struct[qtrand].get(d, 0))
                        mud /= nb_qts
                        computed_docs.append(d)
                        if len(C) < K:
                            C[d] = mud
                            mu_min, _ = get_mu_min_d_min(C)
                        elif mu_min < mud:
                            mu_min, d_min = get_mu_min_d_min(
                                C)  # We store the doc from C with the min score as well as the min score for instruction below
                            del C[d_min]
                            C[d] = mud
                            mu_min, _ = get_mu_min_d_min(C)
                else:
                    finish_qts.add(qt)
                    pass
                # print("C:", C)
                # print("mu_min:", mu_min)
                # print("computed_docs:", computed_docs)
                if len(firster_for_at_least_one_doc) == nb_qts:
                    # if at_least_one_seen_everywhere:
                    tau = 0

                    for qt in self.qws:
                        # print("for qt", qt)
                        next_studied_qt = next_studied_term_index(self.dict_list[qt], computed_docs, j)
                        if next_studied_qt == -1 or next_studied_qt == 0:  # If there is no nex doct for the current qt or
                            # the next doc is the first doc, we ignore it
                            finish_qts.add(qt)
                        else:
                            tau += float(self.dict_list[qt][next_studied_qt - 1][1])
                    tau /= nb_qts
                    # print("tau:", tau)
                    if epsilon:
                        criterion = tau / (1 + epsilon)
                    else:
                        criterion = tau
            mu_min, _ = get_mu_min_d_min(C)
            j += 1

        # Preparing the results
        scores_list = []  # list of pairs mu(d), d
        for k, v in C.items():
            scores_list.append((v, k))
        scores_list.sort()
        """But we only want the ranked document id, not the scores. And until K elements"""
        ranked_docs = []
        for pair in reversed(scores_list):  # scores must be in decreasing order
            ranked_docs.append(pair[1].strip())
            if len(ranked_docs) == K:
                break
        timespent = time.time() - startTime
        self.ranked_docs, self.duration = ranked_docs, timespent

    def display_result_query(self):
        print("The result of your query:")
        self.__display_ranked_docs__()
        while input("Do you want to display the content of one document ? (yes/no)\n").lower() == "yes":
            try:
                print("REMINDER : the result of your query:")
                self.__display_ranked_docs__()
                doc_id = int(input("What is the id of the document to display ? (ex : 2)\n"))
                rank = self.ranked_docs.index(str(doc_id))
                print("RANK:" + str(rank + 1) + " - DOC_ID:" + str(doc_id))
                try:
                    self.__display_one_document__(str(doc_id))
                except:
                    print("If you are in option merge-based and haven't specified a json_path to a"
                          " valid doc_id_by_file.json, this feature cannot be used.")
                    break
            except :
                print("The id of the document doesn't belong to the result of your query.")

    def __display_ranked_docs__(self):
        rank = 0
        for doc_id in self.ranked_docs:
            rank = rank + 1
            print("RANK:" + str(rank) + " - DOC_ID:" + str(doc_id))

    def __display_one_document__(self, doc_id):
        start_time = time.time()
        path_to_file = self.doc_id_by_file[doc_id]
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

    def __update_fields__(self):
        """When we use merge-based, we don't load whole IF into the structures that are updated
        at each new query (the words in the query that are not stored in our data are implicitly discarded).
        When we use only RAM, we remove the words of the list that are not in our data.
        """
        if Configuration.merge_based:
            self.__fill_structs_from_query_words__()
        else:
            self.__remove_nonexisting_terms__()

    def __fill_structs_from_query_words__(self):
        """Called when we use merge-based. We fill the structures with only the terms of interest.
        Words that are not in our data are discarded.
        Careful:
        - scores are strings => in the algorithm, when we get them, they must be converted to float
        - doc ids can be surrounded with spaces => => in the algorithm, when we get them, they must be trimmed
        """
        self.dict_struct = {}
        self.dict_list = {}
        qws = self.qws.copy()
        for qw in qws:
            res = self.merge_based.getDocsByWord(qw)
            if res != -1:
                self.dict_struct[qw] = res
                self.dict_list[qw] = word_dict_2_word_list(self.dict_struct[qw])
            else:
                self.qws.remove(qw)
        #("dict_struct:", self.dict_struct)
        #print("dict_list:", self.dict_list)

    def __remove_nonexisting_terms__(self):
        """
        Called when we use RAM. Removes from the query words the words not in dict_struct
        :return:
        """
        qws = self.qws.copy()
        for qw in qws:
            if qw not in self.dict_struct:
                self.qws.remove(qw)


def generate_query_terms(randomly=True, nb_terms=None, candidate_words = []):
    """ Used by class QueryProcess
    :param candidate_words = a list of words in which to select query terms. Musn't be empty if randomly.
    :param randomly: Default = True. If False, the user will choose the terms of the query.
    If true, randomly select words from list candidate_words
    :return: String containing a certain number of terms, separated with "OR"
    """
    if randomly and nb_terms:
        terms = random.sample(candidate_words, nb_terms)
        return prepare_query(" OR ".join(terms), True)
    elif randomly:
        nb_terms = random.randint(1, 4)
        terms = random.sample(candidate_words, nb_terms)
        return prepare_query(" OR ".join(terms), True)
    else:
        query = input("Please write your query (terms are separated by 'OR')\n")
        return prepare_query(query.upper(), False)


def prepare_query(query, random=True):
    """ Used by class QueryProcess
    :param query: the query in string to convert into a list of "disjuncted" words/terms.
    :return: a set of query terms
    """
    ps = PorterStemmer()  # if Configuration.stemming True, it is used, otherwise not.
    query_words = query.split(" OR ")
    query_words = list(set(query_words))  # only keeps unique words
    for i in range(len(query_words)):
        query_words[i] = query_words[i].lower()
        query_words[i] = query_words[i].strip()
        if Configuration.stemming and not random:
            query_words[i] = ps.stem(query_words[i]) # finally, we stem the word
    if Configuration.random_indexing:
        _, context_vectors, model = \
            random_indexing.generate_vectors_and_model(Configuration.dimension_vector_random_indexing)
        query_words = random_indexing.find_similar_terms(query_words, context_vectors, model)
    print("query words :", query_words)
    return query_words


def word_dict_2_word_list(word_dict):
    """ Used by class QueryProcess
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


def get_mu_min_d_min(C):
    """ Used by class QueryProcess
    :param C:
    """
    mu_min = sys.maxsize
    d_min = ''
    for d in C:
        if mu_min > C[d]:
            mu_min = C[d]
            d_min = d
    return mu_min, d_min


def next_studied_term_index(qt_doc_ranking, computed_docs, j):
    """ Used by class QueryProcess
    Return the minimum index/position among those of the documents that are in the list qt_doc_ranking.
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
