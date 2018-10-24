import json
from sortedcontainers import SortedDict


def prepare_query(query):
    """
    :param query: the query in string to convert into a list of "conjuncted" words/terms
    :return: a set of query terms
    """
    query_words = query.split(" OR ")
    query_words = set(query_words)  # only keeps unique words
    return query_words


def naive(query, dict_struct):
    """
    Words of the query are only separated with OR. The keyword OR is capitalized since or is just a word.
    :param query: string that contains the query : w1 [OR w2 OR w3 ...]
    :param dict_struct: First structure of the IF whose values are also dicts
    :return: list of ranked docs id
    """
    docs_score = {}
    query_words = prepare_query(query)
    for qt in query_words:
        qt = qt.lower()
        qt = qt.strip() # strip takes care about parasite spaces in the query term
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


if __name__ == "__main__":
    query = " OR monday OR tortillon" # forbid the nothingness (will give an empty list)
    # dict_struct = {
    #     "a": {
    #         1: 3,
    #         2: 1
    #     },
    #     "b": {
    #         1: 1,
    #         2: 1
    #     },
    #     "c": {
    #         1: 1,
    #         2: 1
    #     },
    #     "d": {
    #         2: 3
    #     }
    # }
    #file = open("resources/dict_with_dict.json")
    file = open("F:\Ecole\Insa-5e_annee\Indexing\saved_inverted/dict_with_dict.json")
    dict_struct = json.load(file)
    dict_struct = SortedDict(dict_struct)
    # for k, v in dict_struct.items():
    #     print("k:", k, "; v:", v)
    print(naive(query,dict_struct))
