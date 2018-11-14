# TextIndexing

## Workflow
There are 3 modules in our project, each one for a specific task.
### 1/ Configuration
Represented by configuration.py.
It contains global variables to configure the program. The variables are commented.
### 2/ Data reading
Represented by dataReading.py
It allows, from a folder of document files, to build the data structures that the last module of the program, ranking, needs in order to work.
### 3/ Ranking
Represented by ranking.py
It asks the user to enter his/her query or generates a random query, and either with the naïve, Fagin’s Top k or Fagin’s threshold algorithms (user’s choice), delivers the ranking of the first documents for the given query terms.

## What are the scores (to be completed/modified then)
### Score of a term in a document
To compute the score of a term in a document, we first use the count of the word in the document.
### Score of a document for the query terms
This is the mean of the scores of the query terms in the given document.

