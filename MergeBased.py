import os
import pickle
import math

import score

class MergeBased:
    def __init__( self, dir_input , file_output_binary , nb_documents):
        self.dir_input = dir_input
        self.file_output_binary = file_output_binary

        self.nb_documents = nb_documents
        # save the first line of each file
        self.lines = []

        # all files
        self.files = []

        # tables of all files names
        self.files_names = os.listdir( self.dir_input )

        # file to merge all files
        #self.file_all = open( self.file_output , 'w+')

        # save the number of files
        self.file_number = len( self.files_names )

        # last inserted line
        self.last_inserted_line = ""

        #dictionnaire pour mot offset
        self.dict = {}

        # save all files in a list
        for file_index in range(0, self.file_number):
            self.files.append(open(self.dir_input+ '/' + self.files_names[file_index], 'r'))

        # variable to save the readed line in each iteration
        self.the_first_line = []

    ''' function to know if all files are ended or no '''
    def isEndOfFiles( self , the_first_line  ):
        for  i in range(0, len( the_first_line ) ):
            if  the_first_line[i] != '':
                return False
        return True

    ''' compare the element to insert with the last inserted element '''
    def estLastEqualToInserted( self, last, inserted):
        if ( last == "" ):
            return False

        last_token = (last.split('|'))[0]
        inserted_token = (inserted.split('|'))[0]

        if last_token == inserted_token:
            return True
        return False

    def merge(self, last, inserted):
        #print((last.split('|'))[0] + "|" + (last.split('|'))[1] + (inserted.split('|'))[1])
        return (last.split('|'))[0] + "|" + (inserted.split('|'))[1].rstrip("\n\r") + (last.split('|'))[1]

    def closeFiles( self ):
        # fermer tous les fichier
        for file_index in range(0, self.file_number):
            self.files[file_index].close()

       #self.file_all.close()

    def getIndiceFileMinLine(self , the_first_line):
        tokens = []
        for i in range(0, len(the_first_line)):
            tokens.append((the_first_line[i].split('|'))[0])

        sorted_lines = sorted(tokens);

        ''' delete spaces( <=> empty lines ) from the first line  '''
        while '' in sorted_lines: sorted_lines.remove('')

        return tokens.index(sorted_lines[0])

    '''def print_merged_file(self):
        print("-----------------------------------------------------")
        with open(self.file_output, 'r') as all_fichier:
            while True:
                line = all_fichier.readline()
                if ("" == line):
                    break

        all_fichier.close()'''


    def calculate_scores(self , record):

        # new record integrate score
        new_record =  record.split('|')[0] + '|'

        # we extract a | [ d1 : 2 ; ...]
        docs_scores = record.split('|')[1]

        # extract pair <doc:numbers>
        scores = docs_scores.split(';')

        #nombre de docs dans le terme apparus
        number_docs = len(scores) - 1


        for i in range( 0 , number_docs ):
            new_record +=  scores[i].split(':')[0] + ":"

            score_element = score.tf_idf( int(scores[i].split(':')[1]) , number_docs , self.nb_documents )

            new_record += str( score_element ) + ";"


        return new_record + "\n"

    def merge_all_files(self):

        #declarer le fichier binaire:
        binary_file = open(self.file_output_binary, 'wb')
        mon_pickler = pickle.Pickler(binary_file)

        #intialiser notre dictionnaire qui contient mot , offset , lenght
        dict = {}

        # intialise the table : the_first_line = []
        for file_index in range(0, self.file_number):
            self.the_first_line.append( self.files[file_index].readline() )

        # variable used to be sure that we can read more data from files : there is a file note ended
        end_files = self.isEndOfFiles( self.the_first_line )

        # variable to know if we are in the first iteration or no
        iteration = 1

        #last readed line and not insered yet
        last_readed_line = "";

        # pointer of positions in the file
        last_position_file = 0

        while end_files == False:



            #get indice of min line
            self.indice_min_line = self.getIndiceFileMinLine( self.the_first_line )

            if(self.the_first_line[self.indice_min_line] == "\n"):

                self.indice_min_line = self.getIndiceFileMinLine(self.the_first_line)
            elif( last_readed_line == "" or last_readed_line == "\n" or last_readed_line == " "):
                last_readed_line = self.the_first_line[ self.indice_min_line ]


            elif ( self.estLastEqualToInserted( last_readed_line ,  self.the_first_line[self.indice_min_line] ) == True ):
                last_readed_line = self.merge( last_readed_line, self.the_first_line[self.indice_min_line])

            else:
                last_readed_line = self.calculate_scores( last_readed_line )

                #add in binary file:
                mot = last_readed_line.split('|')[0]
                dict[mot] = {}
                dict[mot]["offset"] = binary_file.tell()


                mon_pickler.dump(last_readed_line.split('|')[1])

                dict[mot]["length"] = binary_file.tell()

                #/add in binary file
                #self.file_all.write( last_readed_line )
                last_readed_line = self.the_first_line[self.indice_min_line]

            self.the_first_line[self.indice_min_line] = self.files[self.indice_min_line].readline()

            iteration += 1

            end_files = self.isEndOfFiles( self.the_first_line )

            if( end_files == True):
                last_readed_line = self.calculate_scores( last_readed_line )

                #add in binary file
                mot = last_readed_line.split('|')[0]
                dict[mot] = {}
                dict[mot]["offset"] = binary_file.tell()

                mon_pickler.dump(last_readed_line.split('|')[1])

                dict[mot]["length"] = binary_file.tell()
                # /binary file
                #self.file_all.write(last_readed_line)


        # fermer tous les fichier
        self.closeFiles()
        binary_file.close()

        self.dict = dict
        return self.dict

    def getDocsByWord(self , word ):
        #use to get the offset from dictionnaire
        offset_word = 0;

        if word in self.dict.keys():

            offset = self.dict[word]["offset"]

            #read from binary file and search the word
            binary_file = open(self.file_output_binary, 'rb')

            mon_depickler = pickle.Unpickler(binary_file)

            binary_file.seek( offset , os.SEEK_SET )

            WordDocsList = mon_depickler.load()

            #convert string to list
            dict_docs = {}

            ListDocScore = WordDocsList.split(';')

            number_docs = len(ListDocScore) - 1

            for i in range(0 , number_docs  ):
                dict_docs[ (ListDocScore[i].split(':'))[0] ] = (ListDocScore[i].split(':'))[1]

            return dict_docs


        else:
            return -1


#on intialise les fichiers dont notre algorithme de "merge based" va travailler
#mb  = MergedBased( "dossier" ,"out.dat" , 10000)

#print( mb.merge_all_files() )

#print(mb.getDocsByWord( "a" ))






