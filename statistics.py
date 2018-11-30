from configuration import Configuration

import plotly
import plotly.plotly as py
plotly.tools.set_credentials_file(username=Configuration.username_statistics, api_key=Configuration.api_statistics)
# https://plot.ly/~Cristinutaa/#/
import plotly.graph_objs as go
from ranking import generate_query, naive, fagins_topk, fagins_ta, get_structures


# Creates the graphics
def create_line_graphics(x_axe, y_lists, names, graphic_name = "default"):
    data = []
    for i in range(len(y_lists)):
        trace = go.Scatter(
            x = x_axe,
            y = y_lists[i],
            name = names[i]
        )
        data.append(trace)
    print(py.iplot(data, filename=graphic_name))


# Compare naive and top k
def stats_naive_topk(dict_struct, dict_list, k=10, nb_queries=20, max_terms=20):
    x_axe = []
    naive_y = []
    topk_y = []
    for i in range(1,max_terms+1):
        sum_naive = 0
        sum_topk = 0 
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            _, duration_naive = naive(query, dict_struct)
            sum_naive += duration_naive        
            _, duration_topk = fagins_topk(query, k, dict_struct, dict_list)
            sum_topk += duration_topk
        average_naive = sum_naive/nb_queries
        average_topk = sum_topk/nb_queries
        x_axe.append(i)    
        naive_y.append(average_naive)
        topk_y.append(average_topk)
    create_line_graphics(x_axe, [naive_y, topk_y], ["naive", "top "+ str(k)], "Naive vs Top " + str(k))


# Compare naive and threshold
def stats_naive_threshold(dict_struct, dict_list, k=10, epsilon=0.1, nb_queries=20, max_terms=20):
    x_axe = []
    naive_y = []
    threshold_y = []
    for i in range(1,max_terms+1):
        print(i)
        sum_naive = 0
        sum_threshold = 0        
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            _, duration_naive = naive(query, dict_struct)
            sum_naive += duration_naive        
            _, duration_threshold = fagins_ta(query, k, dict_struct, dict_list, epsilon)
            sum_threshold += duration_threshold  
        average_naive = sum_naive/nb_queries
        average_threshold = sum_threshold/nb_queries
        x_axe.append(i)    
        naive_y.append(average_naive)
        threshold_y.append(average_threshold)
    create_line_graphics(x_axe, [naive_y, threshold_y], ["naive", "threshold "+ str(k) + "  " + str(epsilon)], "Naive vs Threshold " + str(k) + "  " + str(epsilon) + " with an average of " + str(nb_queries) + " queries" )


# Compare topk for different k put in k_list
def stats_topk(dict_struct, dict_list, k_list, nb_queries=20, max_terms=20):
    x_axe = []
    y_axes = [[]]*len(k_list)
    labels = []
    for i in range(1,max_terms+1):
        print("Number of terms: " + str(i))
        sums = [0] * len(k_list)
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            for length in range(len(k_list)):
                k = k_list[length]
                _, duration = fagins_topk(query, k, dict_struct, dict_list)
                sums[length] += duration
        for length in range(len(k_list)):
            average = sums[length]/nb_queries
            y_axes[length].append(average)
        x_axe.append(i)    
    for k in k_list:
        labels.append("top " + str(k))
    create_line_graphics(x_axe, y_axes, labels, "Fagins Top Comparaison")


# Compare top k and threshold
def stats_topk_threshold(dict_struct, dict_list, k=10, epsilon=0, nb_queries=20, max_terms=20):
    x_axe = []
    threshold_y = []
    topk_y = []
    for i in range(1,max_terms+1):
        print(i)
        sum_threshold = 0
        sum_topk = 0
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            _, duration_threshold = fagins_ta(query, k, dict_struct, dict_list, epsilon)
            sum_threshold += duration_threshold  
            _, duration_topk = fagins_topk(query, k, dict_struct, dict_list)
            sum_topk += duration_topk
        average_threshold = sum_threshold/nb_queries
        average_topk = sum_topk/nb_queries
        x_axe.append(i)    
        threshold_y.append(average_threshold)
        topk_y.append(average_topk)
    create_line_graphics(x_axe, [threshold_y, topk_y], ["threshold", "top "+ str(k)], "threshold " + str(k) + " " + str(epsilon) + " vs Top " + str(k))


# Compare stem and no stem
def stats_stem_no_stem(dict_struct, dict_list, dict_struct_stem, dict_list_stem, nb_queries=20, max_terms=20):
    x_axe = []
    stem_y = []
    no_stem_y = []
    for i in range(1,max_terms+1):
        sum_stem = 0
        sum_no_stem = 0
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            _, duration_no_stem = naive(query, dict_struct)
            sum_no_stem += duration_no_stem
            query = generate_query(True, i, dict_struct_stem, dict_list_stem)
            _, duration_stem = naive(query, dict_struct_stem)
            sum_stem += duration_stem
        average_no_stem = sum_no_stem/nb_queries
        average_stem = sum_stem/nb_queries
        x_axe.append(i)    
        no_stem_y.append(average_no_stem)
        stem_y.append(average_stem)
    create_line_graphics(x_axe, [no_stem_y, stem_y], ["No Stemming", "Stemming"], "No Stemming vs Stemming ")

# Compare threshold for different epsilons put in epsilon_list
def stats_ta(epsilon_list, dict_struct, dict_list, nb_queries=20, max_terms=20):
    x_axe = []
    y_axes = [[]]*len(epsilon_list)
    labels = []
    for i in range(1,max_terms+1):
        print("Number of terms: " + str(i))
        sums = [0] * len(epsilon_list)
#       Creates and apply algorithms on nb_queries queries of length i
        for j in range(nb_queries):
            query = generate_query(True, i, dict_struct, dict_list)
            for length in range(len(epsilon_list)):
                epsilon = epsilon_list[length]
                _, duration = fagins_ta(query, 10, dict_struct, dict_list, epsilon)
                sums[length] += duration
        for length in range(len(epsilon_list)):
            average = sums[length]/nb_queries
            y_axes[length].append(average)
        x_axe.append(i)    
    for k in epsilon_list:
        labels.append("Threshold 10 eps " + str(k))
    create_line_graphics(x_axe, y_axes, labels, "Fagins Threshold Comparaison")


if __name__ == "__main__":
    dict_struct, dict_list, corpus_by_doc_id = get_structures()

