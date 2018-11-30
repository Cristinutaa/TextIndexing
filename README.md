# TextIndexing


## Presentation
This project is named "Indexing and Querying text". We have 732 files representing 131896 articles (475 Mo). They were written and published in english by LA Times between 1989 and 1990. The aim is to build an information retrieval system allowing to research key concepts/specified terms inside this set of articles. Our system will only work for conjonctive queries (i.e. OR). If we do not use the merge based system, the score of a term for a particular document is computed as the count of the word in the document. The score of a document for a specified query will then be computed as the mean of the scores of the query terms in the given document.

## User's Manual
Run the main.py file.

### Configuration
It will display "Do you want to use a configuration file (careful, it must be complete)?  (yes/anything else)". If you say "yes", you will need to specify the path to the configuration file (e.g. F:\laela\Desktop\PDC - Text Indexing\TextIndexing\configuration_samples\conf.json). A summary of the configuration properties will be displayed.

### Getting structures
It will display "Do you want to create the structures from the data or to load pre-created structures from *your folder* (yes=create the structures/anything else=use pre-created)?".

### Querying
It will display "Do you want to query something? (yes/no)". You should say "yes". Then , you can choose "Do you want to randomly generate a query ? (yes/no)". If your answer is yes, it will ask "Please specify a number of terms (anything else for a number between 1 and 4):". If your answer is no, it will ask to enter your query.

#### Random indexing
It will display "Do you want to query something? (yes/no)". You should say "yes". Then , you can choose "Do you want to randomly generate a query ? (yes/no)". If your answer is yes, it will ask "Please specify a number of terms (anything else for a number between 1 and 4):". If your answer is no, it will ask to enter your query.

Then, you can choose which query algorithm will be used : "Do you want to use naive, fagin's or fagin's threshold algorithm? Naive:0, Fagin's:1, Fagin's threshold:2". The result will then be displayed under the format "RANK:1 - DOC_ID:197774". You can then display the content of a document "What is the id of the document to display ? (e.g. 2)".


## Code Structure
There are 7 python files in our project, each one for a specific task.
### 1/ Configuration
Represented by configuration.py. 
It will analyse a json configuration file, which contains global variables to configure the program. The variables are commented.
### 2/ Data reading
Represented by dataReading.py
It allows, from a folder of document files, to build the data structures that the other modules of the program (e.g. ranking) will need in order to work. If we work with the merge-based algorithm, it generates the partial inverted files. Otherwise, it generates the final inverted file directly.
### 3/ Ranking
Represented by ranking.py
It asks the user to enter his/her query or generates a random query, and either with the naïve, Fagin’s Top k or Fagin’s threshold algorithms (user’s choice), delivers the ranking of the first documents for the given query terms.
### 4/ Random_indexing
Represented by random_indexing.py
Once the terms of the query are defined, the user can choose to "enrich" the terms by finding synonyms or similar key concepts to the original terms.
### 5/ Merge_based
Represented by MergeBased.py
This part generates an inverted file from the partial ones. It works by merging the similar words among the first lines of the partial inverted files, and appending the word with its score, calculated with TF-IDF, to the final inverted file. We work with binary inverted files for more efficiency.
### 6/ Statistics
Represented by statistics.py
This file was used to generate statistics and plots about the performance of the different querying algorithms (Naive, Fagin’s Top k, Fagin’s threshold).
### 7/ Main
Represented by main.py
This file concatenates the calls to all modules. The running of this file will allow the user to select/generate his data files, generate a query and display the interesting documents for this particular query.

