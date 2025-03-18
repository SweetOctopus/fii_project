from flask import Flask
from flask import render_template
from flask import request
#from flask import Markup

#gestion db
import sqlite3
from flask import g

#produit scalaire
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import math

# the simplest flask project
app = Flask(__name__)

#pays code_names
country_codes = ["DZ","EG","IQ","JO","LY","MT","MA","SD","SY","TN","YE"] 


function_codes = ["1_locative_fii","2_temporal_fii","3_existential_fii","4_possesive_fii","5_modal_fii","6_partitive_fii", "7_genitive_fii","8_pluractional_intensive_fii","9_progressive_fii","10_serial_verb_constructions_fii","11_causativized_statives_fii"]

code_for_map_6_11 = {"6_partitive_fii":[5,7], "8_pluractional_intensive_fii":[1,5,9,11,13,17],"9_progressive_fii": [1,5,9,13,17,21,25,29,34,38,42,46], "10_serial_verb_constructions_fii":[1,5,9,13,17,21],"11_causativized_statives_fii":[5,7,18,20,26,28,30,32] }
#code pour savoir quelle phrase prendre en compte pour la map

value_map = [
    ['DZ', 1, 1, 2, 7, 7, 6, 5, 6, 5, 4, 1],
    ['EG', 1, 1, 3, 1, 7, 5, 3, 3, 7, 7, 2],
    ['IQ', 1, 1, 1, 7, 7, 3, 5, 7, 7, 7, 2],
    ['JO', 2, 2, 4, 1, 6, 3, 2, 7, 5, 6, 2],
    ['LY', 2, 1, 1, 1, 6, 4, 3, 6, 4, 4, 2],
    ['MT', 2, 1, 6, 7, 7, 2, 5, 6, 7, 7, 7],
    ['MA', 1, 1, 3, 7, 7, 5, 3, 6, 7, 6, 2],
    ['SD', 2, 1, 2, 2, 7, 4, 3, 7, 1, 5, 2],
    ['SY', 1, 1, 3, 1, 1, 5, 5, 6, 7, 7, 2],
    ['TN', 1, 1, 2, 7, 7, 6, 3, 7, 2, 2, 1],
    ['YE', 2, 1, 3, 2, 7, 2, 5, 2, 7, 7, 2]
]



color_mapping = {
    1: '#00FF00',    # Green
    2: '#99FF66',    # Light Green
    3: '#CCFF99',    # Greyish Green
    4: '#CCCCCC',    # Grey
    5: '#FFCCCC',    # Greyish Red
    6: '#FF6666',    # Light Red
    7: '#FF0000',    # Red
    -1: '#000000'    # Black for -1
}

for i in range(len(value_map)):
    for j in range(len(value_map[i])):
        if value_map[i][j] in color_mapping:
            value_map[i][j] = color_mapping[value_map[i][j]]

#def query?
#celle la retourn un (#nb de OK colonne 1, 2, 3)

def query_1(table, code_pays):# nouvelle query pour le tableau 1-0, attenttion car "else" return un string, et que "%1%" pourrait avoir un autre sens, attention egalement car Margherita à peut-etre décidé 1 = faux et 0 = vrai
    return "select count(*) as total,\
            sum(case when speaker_1 like '%1%' then 1 else 0 end) as speaker_1,\
            (case when speaker_2 is null then -1 else sum(case when speaker_2 like '%1%' then 1 else 0 end) end) as speaker_2,\
            (case when speaker_3 is null then -1 else sum(case when speaker_3 like '%1%' then 1 else 0 end) end) as speaker_3 \
            from '{}' where task like '%{}%';".format(table, code_pays)

def query_1_2(table, code_pays):# nouvelle query pour le tableau 1-0, attenttion car "else" return un string, et que "%1%" pourrait avoir un autre sens, attention egalement car Margherita à peut-^^etre décidé 1 = faux et 0 = vrai
    
    q_builder = ""
    for code in code_for_map_6_11.get(table):
        q_builder += "task LIKE '%.{}.%{}%' OR ".format(code, code_pays )
    q_builder = q_builder[:-3];    
    
    return "select count(*) as total,\
            sum(case when speaker_1 like '%1%' then 1 else 0 end) as speaker_1,\
            (case when speaker_2 is null then -1 else sum(case when speaker_2 like '%1%' then 1 else 0 end) end) as speaker_2,\
            (case when speaker_3 is null then -1 else sum(case when speaker_3 like '%1%' then 1 else 0 end) end) as speaker_3 \
            from '{}' where {} ;".format(table, q_builder)
            
#query pour comparer la cosine similarity de tout les pays et 1 feature
#def query_2(table, code_pays):
    #return "select CASE WHEN speaker_1 LIKE '%1%' then 1 else 0 END AS speaker_1 from '{}' where task like '%{}%' UNION ALL\
            #select CASE WHEN speaker_2 LIKE '%1%' then 1 else 0 END AS speaker_2 from '{}' where task like '%{}%' UNION ALL\
            #select CASE WHEN speaker_3 LIKE '%1%' then 1 else 0 END AS speaker_3 from '{}' where task like '%{}%';".format(table, code_pays, table, code_pays, table, code_pays)
def query_2(table, code_pays):
    return "select CASE WHEN speaker_1 LIKE '%1%' then 1 else 0 END AS speaker_1,\
            CASE WHEN speaker_2 LIKE '%1%' then 1 else 0 END AS speaker_2,\
            CASE WHEN speaker_3 LIKE '%1%' then 1 else 0 END AS speaker_3 from '{}' where task like '%{}%';".format(table, code_pays, table, code_pays, table, code_pays)

#query pour comparer la cosine similarity d'un pays et une feature (speaker 1,2,3)
def query_3(table, code_pays):
    return "select CASE WHEN speaker_1 LIKE '%1%' then 1 else 0 END AS speaker_1,\
            CASE WHEN speaker_2 LIKE '%1%' then 1 else 0 END AS speaker_2,\
            CASE WHEN speaker_3 LIKE '%1%' then 1 else 0 END AS speaker_3\
            from '{}' where task like '%{}%'".format(table, code_pays)

#query pour comparer la cosine similarity de tout les pays et de toutes les features
def query_4(code_pays):
    res = ""
    for function in function_codes:
        res += query_2(function, code_pays)[:-1] + " UNION ALL "
    res = res[:-10] + ";"
    return res

def query_5(code_pays):
    res = ""
    for function in function_codes:
        res += query_3(function, code_pays) + " UNION ALL "
    res = res[:-10] + ";"
    return res

    



#utils
def results_to_percentage(tuple):
    #ici sortir les tuples qui ne sont pas des tuples
    #if tuple = 1:
        #return -1
    
    max = tuple[0]
    total = tuple[1] / max 
    nmb = 1
    le = len(tuple)
    
    for i in range(2, le):
        if tuple[i] >= 0:
            total += tuple[i] / max
            nmb += 1
    return total/nmb

def percentage_to_icon(num):
    num *= 100
    if num >= 90:
        return "icon1"
    elif num >= 75:
        return "icon2"
    elif num >= 55:
        return "icon3"
    elif num >= 45:
        return "icon4"
    elif num >= 25:
        return "icon5"
    elif num >= 15:
        return "icon6"
    elif num >= 0:
        return "icon7"
    else:
        return "icon0"


def percentage_to_rgb(num):
    r = int((1 - num) * 255)  # calculate red component
    g = int(num * 255)        # calculate green component
    return 'rgb(' + str(r) + ', ' + str(g) + ', 0)'

def percentage_to_hue_rotation(num):
    red = 140
    return str(red + int(num * 120)) + "deg"


#implémente le calclul de la feuille de margherita
def cosine_similarity_perso(tab, tab2):
    prod_scal = np.dot(tab,tab2)
    prod_scal = prod_scal / (math.sqrt() * len(tab2))#diviser par sqrt(\\tab\\) = tab[0]^2 + tab[1]^2 + tab[2]^2 etc...
    return math.cos(prod_scal)


def tuple_to_list(tuple):
    
    return [item[0] for item in tuple]


#temporaire, à ameliorer quand il y'aura plus de pays
#en gros il faut tout init à zero (de la taille de country_codes et des fonctions (a creer egalement))
def check(pays, fonctions):
    tab = [[0]*11,[0]*11]
    
    i = 0
    for code in country_codes:
        if code in pays:
            tab[0][i] = 1
        i += 1
    
    
    i = 0
    for code in function_codes:
        if code in fonctions:

            tab[1][i] = 1
        i += 1

    
    return tab

def display_dict_to_tab(dict):
    display = """<thead>
                        <tr>
                        <th></th>
                        <th>DZ</th>                            
                        <th>EG</th>
                        <th>IQ</th>
                        <th>JO</th>
                        <th>LY</th>
                        <th>MT</th>
                        <th>MA</th>
                        <th>SD</th>
                        <th>SY</th>
                        <th>TN</th>
                        <th>YE</th>
                        </tr>
                    </thead>
                    <tbody>"""
    for codei in country_codes:
        display += "<tr><th>{}</th>  ".format(codei)
        for codej in country_codes:
            #if codei != codej:
            display += "<th>{}</th>".format(round(dict[codei+codej], 2))
            #else:
                #display += "<th class='case_noire'></th>"
        display += "</tr>"
        
        
    display +="</tbody>"
    return display

#THE FLASK APP

@app.route('/', methods=['GET', 'POST'])
def index():
    
    #position de base
    map_pos = "[26, 17], 3"
    numero_fii = -1
    
    # handle form submission
    if request.method == 'POST':
        fii_type = request.form['fii_type']
        #pays_form = request.form.get('pays', None) sert à plus rien non plus car plus de cosine similarity ici
        map_pos = request.form['map_pos']
        
        type2 = False
        

        # modify your database query based on the selected fii type
        type_fii = ""
        if fii_type == 'locative':
            type_fii = "1_locative_fii"
            numero_fii = 1
        elif fii_type == 'temporal':
            type_fii = "2_temporal_fii"
            numero_fii = 2
        elif fii_type == 'existential':
            type_fii = "3_existential_fii"
            numero_fii = 3
        elif fii_type == 'possesive':
            type_fii = "4_possesive_fii"
            numero_fii = 4
        elif fii_type == 'modal':
            type_fii = "5_modal_fii"
            numero_fii = 5
        elif fii_type == 'partitive':
            type2 = True
            type_fii = "6_partitive_fii"
            numero_fii = 6
        elif fii_type == 'genitive':
            type_fii = "7_genitive_fii"
            numero_fii = 7
        elif fii_type == 'pluractional_intensive':
            type2 = True
            type_fii = "8_pluractional_intensive_fii"
            numero_fii = 8
        elif fii_type == 'progressive':
            type2 = True
            type_fii = "9_progressive_fii"
            numero_fii = 9
        elif fii_type == 'serial_verb_constructions':
            type2 = True
            type_fii = "10_serial_verb_constructions_fii"
            numero_fii = 10
        elif fii_type == 'causativized_statives':
            type2 = True
            type_fii = "11_causativized_statives_fii"
            numero_fii = 11


        display = {}

        for l in value_map:
            display[l[0]]=l[numero_fii]

        # pass the cursor object to the template
        return render_template("index.html", display = display, fii_type = fii_type, map_pos = map_pos)

    # handle GET request
    else:
    
    ###supprimer ici après la mise à joir bbd 0-1
    
        #display "locative_fii" by default

        display = {}

        for l in value_map:
            display[l[0]]=l[1]

        fii_type = 'locative'
        return render_template('index.html', display=display, fii_type = fii_type, map_pos = map_pos)

@app.route('/a_propos', methods=['GET', 'POST'])
def a_propos():
    return render_template("a_propos.html")

@app.route('/language_clustering', methods=['GET', 'POST'])
def language_clustering():
    return render_template("language_clustering.html")

@app.route('/bibliography', methods=['GET', 'POST'])
def bibliography():
    return render_template("bibliography.html")

@app.route('/similarity', methods=['GET', 'POST'])
def similarity():
    
    if request.method == 'POST':
        fii_type = request.form['fii_type']
        pays_form = request.form.get('pays', None) 
        #sim_form = request.form.get['sim', None]
        
        type_fii = ""
        if fii_type == 'locative':
            type_fii = "1_locative_fii"
        elif fii_type == 'temporal':
            type_fii = "2_temporal_fii"
        elif fii_type == 'existential':
            type_fii = "3_existential_fii"
        elif fii_type == 'possesive':
            type_fii = "4_possesive_fii"
        elif fii_type == 'modal':
            type_fii = "5_modal_fii"
        elif fii_type == 'partitive':
            type2 = True
            type_fii = "6_partitive_fii"
        elif fii_type == 'genitive':
            type_fii = "7_genitive_fii"
        elif fii_type == 'pluractional_intensive':
            type2 = True
            type_fii = "8_pluractional_intensive_fii"
        elif fii_type == 'progressive':
            type2 = True
            type_fii = "9_progressive_fii"
        elif fii_type == 'serial_verb_constructions':
            type2 = True
            type_fii = "10_serial_verb_constructions_fii"
        elif fii_type == 'causativized_statives':
            type2 = True
            type_fii = "11_causativized_statives_fii"


        with app.app_context():
            db = get_db()
            display = ""

            if pays_form == "ALL":

                display = """   <thead>
                                <tr>
                                <th></th>
                                <th>DZ</th>                            
                                <th>EG</th>
                                <th>IQ</th>
                                <th>JO</th>
                                <th>LY</th>
                                <th>MT</th>
                                <th>MA</th>
                                <th>SD</th>
                                <th>SY</th>
                                <th>TN</th>
                                <th>YE</th>
                                </tr>
                                </thead>
                                <tbody>     """

                matrix = []
                for code in country_codes:
                    if fii_type == "ALL":
                        query = query_4(code)
                    else:
                        query = query_2(type_fii, code)
                    cursor1 = db.execute(query)
                    tab1 = cursor1.fetchall()#tab contenant le vecteur de comparaison
                    tab1 = [sum(triplet) / len(triplet) for triplet in tab1]
                    tab1 = np.array(tab1)  
                    
                    tab1 = tab1.reshape(1,-1)#est apparemment demandé par cosine_similarity
                    
                    matrix.append(tab1)
                
                     
                i = 0
                for tab1 in matrix:
                    display += "<tr><th>{}</th>  ".format(country_codes[i])
                    j = 0
                    for tab2 in matrix:
                        if i != j:
                            #if type_fii == "10_serial_verb_constructions_fii" and (i == 1 or i == 7 or j == 1 or j == 7):
                                #display += "<th class='case_noire'></th>"
                            #else:
                            
                            # ICI ON A tab1 et tab2 qui sont les tableaux des langues !!!!!!!!
                            #A sortir : Cas ou un des deux vector est tout à 0
                            #A sortit aussi: Cas ou les deux vectors sont à 0
                            #Cas à laisser, si les deux sont inverse (par ex. 01001110001 et 10110001110), qui donne un vrai 0
                            #l'idée, faire la diff de A1B1 + A2B2 + A3B3 + A4B4 + ...), qui si donne 0 alors on peut mettre 1 (identité), qui si donne 1 alors on peut dire qu'ils sont opposé et mettre 0
                            # et s'il donne 0.5 mais que la cosine_similarity donne 0, alors on a un cas de 1 des 2 vecteurs est 00000000000
                            
                            ###ESPACE TEST

                            
                            cosim = round(cosine_similarity(tab1, tab2).item(), 2)

                            if cosim == 0:
                                taille_tab = len(tab1[0])
                                sum_tab1 = 0
                                sum_tab2 = 0
                                for k in range(taille_tab):
                                    sum_tab1+= tab1[0][k]
                                    sum_tab2 += tab2[0][k]

                                if sum_tab1 == 0:
                                    if sum_tab2 == 0: 
                                        display += "<th style='color: #FFD500;'>{}</th>".format("1.0")     #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! v1 et v2 nuls
                                    else:
                                        display += "<th style='color: red;'>{}</th>".format("-")   #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! v1 nul
                                elif sum_tab2 == 0:
                                    display += "<th style='color: red;'>{}</th>".format("-")   #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! v2 nul
                                else:
                                    display += "<th>{}</th>".format(cosim)
                            else:
                                display += "<th>{}</th>".format(cosim)
                        else:
                            display += "<th class='case_noire'></th>"
                        j += 1
                    display += "</tr>"
                    i += 1

                display +="</tbody>"
            
            elif pays_form in country_codes:
                
                display = """   <thead>
                    <tr>
                    <th></th>
                    <th>Speaker 1</th>                            
                    <th>Speaker 2</th>
                    <th>Speaker 3</th>
                    </tr>
                    </thead>
                    <tbody>     """#.format(fii_type.replace("_"," ").capitalize())   mettre {} dans la première balise th si voulu
                    
                if fii_type == "ALL":
                    query = query_5(pays_form)
                else:
                    query = query_3(type_fii, pays_form)
                cursor1 = db.execute(query)
                tab = cursor1.fetchall()#tab contenant le vecteur de comparaison
                tab = list(zip(*tab))


                
                for i in range(len(tab)):

                    tab[i] = list(tab[i])
                    
                    tab[i] = np.array(tab[i])
                    
                    tab[i] = tab[i].reshape(1,-1)
                
                i = 0 
                speaker = ""
                for tab1 in tab:
                    if i == 0:
                        speaker = "Speaker 1"
                    if i == 1:
                        speaker = "Speaker 2"
                    if i == 2:
                        speaker = "Speaker 3"
                        
                    display += "<tr><th>{}</th>  ".format(speaker)
                    j = 0
                    for tab2 in tab:
                        if i != j:
                                cosimilarity = round(cosine_similarity(tab1, tab2).item(), 2)
                                if cosimilarity == 0:
                                    display += "<th style='color: #FFD500;' >{}</th>".format("1.0")#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                                else :
                                    display += "<th>{}</th>".format(cosimilarity)
                        else:
                            display += "<th class='case_noire'></th>"
                        j += 1
                    display += "</tr>"
                    i += 1

                display +="</tbody>"
                
        return render_template("similarity.html",display = display, fii_type = fii_type, pays_form = pays_form)
    else:
        return render_template("similarity.html", display = "   <thead><tr><th></th><th>DZ</th><th>EG</th><th>IQ</th><th>JO</th><th>LY</th><th>MT</th><th>MA</th><th>SD</th><th>SY</th><th>TN</th><th>YE</th></tr></thead><tbody>     <tr><th>DZ</th>  <th class='case_noire'></th><th>0.99</th><th>0.99</th><th>0.98</th><th>0.93</th><th>0.96</th><th>0.99</th><th>0.93</th><th>0.99</th><th>0.99</th><th>0.92</th></tr><tr><th>EG</th>  <th>0.99</th><th class='case_noire'></th><th>0.98</th><th>0.97</th><th>0.9</th><th>0.93</th><th>0.99</th><th>0.9</th><th>0.97</th><th>0.98</th><th>0.88</th></tr><tr><th>IQ</th>  <th>0.99</th><th>0.98</th><th class='case_noire'></th><th>0.97</th><th>0.95</th><th>0.96</th><th>0.96</th><th>0.92</th><th>0.96</th><th>0.97</th><th>0.92</th></tr><tr><th>JO</th>  <th>0.98</th><th>0.97</th><th>0.97</th><th class='case_noire'></th><th>0.9</th><th>0.95</th><th>0.97</th><th>0.89</th><th>0.97</th><th>0.98</th><th>0.86</th></tr><tr><th>LY</th>  <th>0.93</th><th>0.9</th><th>0.95</th><th>0.9</th><th class='case_noire'></th><th>0.95</th><th>0.89</th><th>0.93</th><th>0.91</th><th>0.89</th><th>0.94</th></tr><tr><th>MT</th>  <th>0.96</th><th>0.93</th><th>0.96</th><th>0.95</th><th>0.95</th><th class='case_noire'></th><th>0.92</th><th>0.92</th><th>0.94</th><th>0.94</th><th>0.91</th></tr><tr><th>MA</th>  <th>0.99</th><th>0.99</th><th>0.96</th><th>0.97</th><th>0.89</th><th>0.92</th><th class='case_noire'></th><th>0.91</th><th>0.99</th><th>0.99</th><th>0.88</th></tr><tr><th>SD</th>  <th>0.93</th><th>0.9</th><th>0.92</th><th>0.89</th><th>0.93</th><th>0.92</th><th>0.91</th><th class='case_noire'></th><th>0.96</th><th>0.93</th><th>0.98</th></tr><tr><th>SY</th>  <th>0.99</th><th>0.97</th><th>0.96</th><th>0.97</th><th>0.91</th><th>0.94</th><th>0.99</th><th>0.96</th><th class='case_noire'></th><th>0.99</th><th>0.93</th></tr><tr><th>TN</th>  <th>0.99</th><th>0.98</th><th>0.97</th><th>0.98</th><th>0.89</th><th>0.94</th><th>0.99</th><th>0.93</th><th>0.99</th><th class='case_noire'></th><th>0.9</th></tr><tr><th>YE</th>  <th>0.92</th><th>0.88</th><th>0.92</th><th>0.86</th><th>0.94</th><th>0.91</th><th>0.88</th><th>0.98</th><th>0.93</th><th>0.9</th><th class='case_noire'></th></tr></tbody>", fii_type = "locative", pays_form = "ALL")

#gestion database
DATABASE = "sqlite.db"

def get_db():
    db = getattr(g,'_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g,'_database', None)
    if db is not None:
        db.close()

#test pour onglet recherche
@app.route('/recherche', methods=['GET', 'POST'])
def recherche():
    display = """<div>
                        <table id="table_recherche">
                        <thead>
                            <tr>
                            <th>Language</th>                            
                            <th>Condition</th>
                            <th>Feature</th>
                            <th>Intended meaning</th>
                            <th>Number</th>
                            <th>Sentence in Arabic</th>
                            <th>Phonetic / Gloss</th>
                            <th>Speaker 1</th>
                            <th>Speaker 2</th>
                            <th>Speaker 3</th>
                            </tr>
                        </thead>
                        <tbody>
                    </tbody> </table></div>"""
    checked = [[0]*11,[0]*11] #contien une liste pour les pays et une liste pour les fonctions
    hide = [0,0,0,0,0,2,3,1,3,1,3,1,1,1] #(le numéro des colonnes à hide, puisque actuellement je recup * de la base sql)
    functions_void = False
    pays_void = False

    if request.method == 'POST':
        pays = request.form.getlist('pays[]')
        fonctions = request.form.getlist('fonctions[]')
        
        if len(pays) == 0 and len(fonctions) == 0:
            return render_template("recherche.html",display = display, checked = checked )
        
        if len(fonctions) ==0 :
            fonctions = function_codes
            functions_void = True
        if len(pays) ==0:
            pays = country_codes
            pays_void = True
            
        text_input = request.form['text-input']
        
        #ici gerer la partie ENTREE DE CODE 
        if len(text_input) ==0:
            text_input = False
        elif "-" not in text_input and "," not in text_input:
            #on part du principe que seul un nombre est rentré
            text_input = [text_input]
        else:
            text_input = text_input.replace(' ','')
            text_input = text_input.split(",")
            
            text_input_final = []
            for nb in text_input:
                if '-' in nb:
                    start, end = nb.split("-")
                    start = int(start)
                    end = int(end)
                    for i in range(start,end + 1): 
                        text_input_final.append(i)
                else:
                    text_input_final.append(nb)
            text_input = text_input_final
            
        #ecrire en cas de input unique et de range avec -
        

        
        if not functions_void:
            
            if not pays_void:
                checked = check(pays,fonctions)
            else:
                checked = check([],fonctions)
        else:
            checked = check(pays, [])
        

        #query = ''
        #début du tableau pour display les resultats de la recherche, avec les en-têtes
        display = """
                        <table id="table_recherche">
                        <thead>
                            <tr>
                            <th>Language</th>                            
                            <th>Condition</th>
                            <th>Feature</th>
                            <th>Intended meaning</th>
                            <th>Number</th>
                            <th>Speaker 0</th>
                            <th>Phonetic / Gloss</th>
                            <th>Speaker 1</th>
                            <th>Speaker 2</th>
                            <th>Speaker 3</th>
                            </tr>
                        </thead>
                        <tbody>
                    """
        
        #ici je dois build un max de 4 query, et ensuite les fetch et rassembler les resultats dans un seul tableau
        

        query1 = ""
        query2 = ""
        query3 = ""
        query4 = ""
        
        if "1_locative_fii" in fonctions:
            query1 += query_builder(text_input,"1_locative_fii", pays ) + " UNION "
        if  "2_temporal_fii" in fonctions:
            query1 += query_builder(text_input,"2_temporal_fii", pays ) + " UNION "
        if "3_existential_fii" in fonctions:
            query1 += query_builder(text_input,"3_existential_fii", pays ) + " UNION "
        if "4_possesive_fii" in fonctions:
            query1 += query_builder(text_input,"4_possesive_fii", pays ) + " UNION "
        if "5_modal_fii" in fonctions:
            query1 += query_builder(text_input,"5_modal_fii", pays ) + " UNION "
        
        if query1.endswith("UNION "):
            query1 = query1[:-6] #+ " ORDER BY TASK;"
            query1 = nest_query_sort_roman(query1)
            
        if "6_partitive_fii" in fonctions:
            query2 += query_builder(text_input,"6_partitive_fii", pays ) #+ " ORDER BY TASK;"    
            query2 = nest_query_sort_roman(query2)  

        if "7_genitive_fii" in fonctions:
            query3 += query_builder(text_input,"7_genitive_fii", pays ) #+ " ORDER BY TASK;"  
            query3 = nest_query_sort_roman(query3)  
             
        if "8_pluractional_intensive_fii" in fonctions:
            query4 += query_builder(text_input,"8_pluractional_intensive_fii", pays ) + " UNION "                   
        if "9_progressive_fii" in fonctions:
            query4 += query_builder(text_input,"9_progressive_fii", pays ) + " UNION "
        if "10_serial_verb_constructions_fii" in fonctions:
            query4 += query_builder(text_input,"10_serial_verb_constructions_fii", pays ) + " UNION "     
        if "11_causativized_statives_fii" in fonctions:
            query4 += query_builder(text_input,"11_causativized_statives_fii", pays ) + " UNION "
            
        if query4.endswith("UNION "):
            query4 = query4[:-6] #+ " ORDER BY TASK;"
            query4 = nest_query_sort_roman(query4)
            
        querys = [query1, query2, query3, query4]           

        # execute the modified query
        with app.app_context():
            db = get_db()
            #ici pour changer le type de query
            results = []
            
            alternance = 0 #gere si c'est un cas 1 ou 2
            
            for q in querys:
                

                try:
                    cursor = db.execute(q)
                except:
                    cursor =db.execute("Select * from '1_locative_fii' where 1=0")#faire ATTENTION AUX RESULTATS FANTOMES
                
                result = cursor.fetchall()
                
                if alternance % 2 == 1:
                    #gerer les lignes en trop
                    temp_res = []
                    for row in result:
                        row = [str(row[0]) + " // " + str(row[1]) + " // " + str(row[2]), row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13]] 
                        temp_res.append(row)
                    #si oui, faire fusionner row[0] avec row[1] et row[2] ainsi que fusionner row9 et 10, 12 et 13, 15 et 16
                    result = temp_res
                alternance += 1
                
                #rempli le tableau selon les lignes de la requete, eventuellement trier avant
                results += result

            
            for row in results:
                display += '<tr>'
                display += '<td>'+ task_to_language(row[2]) +'</td>'
                display += '<td>'+ task_to_fonction(row[2]) +'</td>'                

                i = 0
                glosse =""
                for element in row:
                    
                    if hide[i] == 0 or hide[i] == 3:
                        if hide[i] == 3:
                            element = int(element)
                            if element == 0:
                                element = "*"
                            elif element == 1:
                                element = "OK"
                        #    element = convert_to_OK(element)
                        display += '<td>'
                        display += str(element)
                        display += '</td>'
                    elif hide[i] == 2:
                        glosse = str(element)
                    i += 1
                display += '<tr><td></td><td></td><td></td><td></td><td></td><td></td><td>'+ glosse +'</td><td></td><td></td></tr>'
                display += '</tr>'

        #fini le tableau
        display +=   '</tbody> </table>'

    #okay, la recherche fonctionne, mtn il faut s'occuper de l'afficher sur la page
    # la boulce 'element in row' permet d'acceder cellule par cellule (row est un tuple, c'est à dire une liste heterogène)
    # results est une liste de row
    return render_template("recherche.html",display = display, checked = checked )

def query_builder(text_input, fonction, pays):
    query = ''
    if not text_input:

        query += f"select * from '{fonction}' where "
        for j in range(len(pays)):
            query += f"task like '%.{pays[j]}%' or " #ici ce serait mieux de ne pas avoir à utiliser %.{pays[j]}%, mais simplement %.{pays[j]}, le probleme c'est qu'il y a plein de caractères fantomes dans ma BDD, qu'il faut que je TRIM
        query = query[:-4]
        #il faut ajouter un "order by task qqpart"
    else :

        query += f"select * from '{fonction}' where "
        for j in range(len(pays)):
            for code in text_input:                    
                query += f"task like '%.{code}.{pays[j]}%' or "
        query = query[:-4]
    return query

def nest_query_sort_roman(query):
    if len(query)>0:
    
        return f"""SELECT *
                FROM (
                    SELECT *,
                        CASE 
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'I' THEN 1
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'II' THEN 2
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'III' THEN 3
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'IV' THEN 4
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'V' THEN 5
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'VI' THEN 6
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'VII' THEN 7
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'VIII' THEN 8
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'IX' THEN 9
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'X' THEN 10
                            WHEN SUBSTR(Task, 1, INSTR(Task, '.') - 1) = 'XI' THEN 11
                            -- Add more cases as needed for larger Roman numerals
                        END AS RomanNumeral,
                        CAST(SUBSTR(Task, INSTR(Task, '.') + 1) AS INTEGER) AS NumericPart
                    FROM (
                        {query}
                    )
                )
                ORDER BY RomanNumeral, NumericPart;"""
    else:
        return ""

def task_to_fonction(task):
    task = task.split(".", 1)[0]
    if task == "I":
        return "Locative"    
    elif task == "II":
        return "Temporal"
    elif task == "III":
        return "Existential"
    elif task == "IV":
        return "Possesive"
    elif task == "V":
        return "Modal"
    elif task == "VI":
        return "Partitive"
    elif task == "VII":
        return "Genitive"
    elif task == "VIII":
        return "Pluractional Intensive"
    elif task == "IX":
        return "Progressive"
    elif task == "X":
        return "Serial Verb Constructions"
    elif task == "XI":
        return "Causativized statives"
    else:
        return "unknown"

def task_to_language(task):
    task = task.strip() #A cause des espaces fantomes dans la BDD
    task = task[-2:] 
    
    
    if task == "DZ":
        return "Algeria"    
    elif task == "EG":
        return "Egypt"
    elif task == "IQ":
        return "Iraq"
    elif task == "JO":
        return "Jordan"
    elif task == "LY":
        return "Libya"
    elif task == "MT":
        return "Malta"
    elif task == "MA":
        return "Morocco"
    elif task == "SD":
        return "Sudan"
    elif task == "SY":
        return "Syria"
    elif task == "TN":
        return "Tunisia"
    elif task == "YE":
        return "Yemen"
    else:
        return "unknown"

# pour appeler l'app en python
if __name__ == "__main__":
    app.run(debug= True)
