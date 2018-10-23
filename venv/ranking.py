


def naive(query, dict_struct):
    """
    Words of the query are only separated with OR. The keyword OR is capitalized since or is just a word.
    :param query: string that contains the query : w1 [AND|OR w2 AND|OR w3]
    :param dict_struct: First structure of the IF whose values are also dicts
    # :param list_struct: Second structure of the IF whose values are lists
    :return: list of ranked docs id
    """
    docs_score = {}
    query_words = query.split(" OR ")
    for qt in query_words:
        qt = qt.lower()
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
    query = "a OR b"
    dict_struct = {
        "a": {
            1: 3,
            2: 1
        },
        "b": {
            1: 1,
            2: 1
        },
        "c": {
            1: 1,
            2: 1
        },
        "d": {
            2: 3
        }
    }
    print(naive(query,dict_struct))
