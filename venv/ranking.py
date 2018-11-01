import json
from nltk.stem import PorterStemmer
import os
import random
from sortedcontainers import SortedDict

#personal imports
import configuration
import dataReading


dict_struct = dict()
corpus_by_doc_id = dict()


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
    :return: list of ranked docs id
    """
    #ps = PorterStemmer()
    docs_score = {}
    query_words = prepare_query(query)
    for qt in query_words:
        qt = qt.lower()
        qt = qt.strip() # strip takes care about parasite spaces in the query term
        #qt = ps.stem(qt) # finally, we stem the word
        # We have to check if at least one doc contains the qt
        if qt not in dict_struct:
            continue
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
    return ranked_docs


def prepare_query(query):
    """
    :param query: the query in string to convert into a list of "conjuncted" words/terms
    :return: a set of query terms
    """
    query_words = query.split(" OR ")
    query_words = set(query_words)  # only keeps unique words
    return query_words


if __name__ == "__main__":
    json_path = configuration.get_json_path()
    for file in os.listdir(json_path):
        if file == "dict_with_dict.json":
            file = open(json_path + "\\" + file)
            dict_struct = json.load(file)
            dict_struct = SortedDict(dict_struct)
        elif file == "corpus_by_doc_id.json":
            file = open(json_path + "\\" + file)
            corpus_by_doc_id = json.load(file)

    query = generate_query(True if input("Do you want to randomly generate a query ? (yes/no)\n").lower() == "yes" else False)
    print("Your query is : " + query)
    ranked_docs = naive(query, dict_struct)
    display_result_query(ranked_docs)
