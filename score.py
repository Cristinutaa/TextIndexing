import math


# Gives the score for a term with regards to a document
# n : Frequency of the term in the document
# d : Number of documents that contain the term
# nb_docs : total number of documents
def tf_idf(n, d, nb_docs):
    score = 0
    if n > 0:
        score = (1 + math.log(n)) * math.log(nb_docs / (1 + d))
    return round(score, 2)