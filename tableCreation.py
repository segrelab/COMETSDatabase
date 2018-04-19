import os
import os.path
import cobra
import pandas
import pymysql
import cgi
import cgitb
cgitb.enable()

# Methods
# connect to the mySQL database and return the cursor and connection 
def connect(username,password, database, host):
    import pymysql
    connection = pymysql.connect(host=host, db = database, user=username, passwd=password)
    cursor = connection.cursor()
    return cursor, connection

def insert_model():
    connection = pymysql.connect()
    cursor = connection.cursor()
    query = "INSERT INTO MODEL (NAME) VALUES("
    for i in MODELS["NAME"]:
        query += '"' + i + '"'+"),("
    query = query[0:-2]
    query += ";"
    cursor.execute(query)
    connection.commit()
    
def insert_reactions():
    connection = pymysql.connect()
    cursor = connection.cursor()
    query = "INSERT INTO REACTIONS (NAME, EC) VALUES("
    for index, row in REACTIONS.iterrows():
        query += '"' + row["NAME"] + '"'+"," + '"' + row["ec-code"] + '"'+"),("
    query = query[0:-2]
    query += ";"
    cursor.execute(query)
    connection.commit()

def insert_metabolites():
    connection = pymysql.connect()
    cursor = connection.cursor()
    query = "INSERT INTO METABOLITES (NAME, STRING_NAME) VALUES("
    for index, row in METABOLITES.iterrows():
        query += '"' + row["NAME"] + '"'+"," + '"' + row["Str_NAME"] + '"'+"),("
    query = query[0:-2]
    query += ";"
    cursor.execute(query)
    connection.commit()

def notInTable(ID, DF):
    if sum(DF.isin({"NAME": [ID]})["NAME"]) < 0:
    #if DF[DF.NAME == ID].any():
        return False
    else:
        return True

def inStoich(metID, rxnID, VALUE, STOICH):
    #b =(STOICH["METABOLITESID"] == metID).any()
    b = ( (STOICH["METABOLITESID"] == metID) & (STOICH["REACTIONSID"] == rxnID) & (STOICH["VALUE"] == VALUE) ).all()
    #test = STOICH.loc[ STOICH[( (STOICH["METABOLITESID"] == metID) & (STOICH["REACTIONSID"] == rxnID) & (STOICH["VALUE"] == VALUE))]]
    return b#test

    
def loadingAgora(directory):
    # get all the model files in the agora folder, hold in a list
    model_files = os.listdir(directory)[0:2]
    return model_files

def addToReactions(reaction, model, current_reaction_id, REACTIONS, MOD_REACT):
    name = reaction.id
    str_name = reaction.name
    try:
        ec = reaction.annotation['ec-code']
    except KeyError:
        ec = 'NA'    
    REACTIONS = REACTIONS.append({"RID": current_reaction_id ,"NAME": name, "Str_NAME": str_name, "ec-code": ec}, ignore_index=True)
    MOD_REACT = MOD_REACT.append( { "MOD_NAME": model, "REACT_NAME": name }, ignore_index=True)
    return REACTIONS, MOD_REACT

def addToMetabolites(metid, met, model, METABOLITES): 
    name = str(met.id).split('__91__')[0]
    str_name = met.name
    compartment = met.compartment 
    
    try:
        kegg = model.metabolites.get_by_id(met.id).annotation["kegg.compound"]
    except KeyError:
        kegg = 'NA'
    try:
        pubchem = model.metabolites.get_by_id(met.id).annotation["pubchem.compound"]
    except KeyError:
        pubchem = 'NA'
    try:
        inchi = model.metabolites.get_by_id(met.id).annotation["inchi"]
    except KeyError:
        inchi = 'NA'
    
    if notInTable(name,METABOLITES):
        METABOLITES = METABOLITES.append({"METABOLITESID":metid, "NAME": name,"Str_NAME": str_name,"COMPARTMENT": compartment, "KEGG": kegg, "PUBCHEM": pubchem, "INCHI": inchi}, 
                                         ignore_index=True)
    return METABOLITES

def addToStoich(metid, rid, coeff, STOICH):
    STOICH = STOICH.append({"REACTIONSID": rid,"METABOLITESID": metid,"VALUE": coeff}, ignore_index=True)
    return STOICH

# Main script
# import modules
MODELS = pandas.DataFrame(columns = ["MID","NAME"])
MOD_REACT = pandas.DataFrame(columns = ["MOD_NAME","REACT_NAME"])
REACTIONS = pandas.DataFrame(columns = ["RID","NAME","ec-code"])
METABOLITES = pandas.DataFrame(columns = ["METABOLITESID", "NAME","Str_Name","COMPARTMENT","KEGG","PUBCHEM","INCHI"])
STOICH = pandas.DataFrame(columns = ["REACTIONSID","METABOLITESID","VALUE"])
# connect to the database 
#cursor = connect()
# read each model in the Agora file 
model_files = loadingAgora("Agora-1.02/sbml")

current_model_id = 0
current_reaction_id = 0
current_metabolite_id = 0
# read each model and get the ID
for i in model_files:
    model = cobra.io.read_sbml_model('Agora-1.02/sbml/%s'%i) #read model
    print(model)
    # check if model is already in the table. if not, add to the table 
    if notInTable(model.id, MODELS):
        current_model_id += 1
        MODELS = MODELS.append({"MID": current_model_id ,"NAME": model.id}, ignore_index=True)
        print(MODELS)
        
        # Get reactions in the model 
        for j in model.reactions:
            if notInTable(j.id, REACTIONS):
                current_reaction_id += 1
                REACTIONS, MOD_REACT = addToReactions(j, model.id, current_reaction_id,REACTIONS, MOD_REACT)
                
                # get metabolites and coefficients
                for met,coeff in j.metabolites.items():                
            
    
                    if notInTable(str(met.id).split('__91__')[0], METABOLITES):
                        current_metabolite_id += 1
                        METABOLITES = addToMetabolites(current_metabolite_id, met, model, METABOLITES)
                        
                    metID = METABOLITES['METABOLITESID'].where(METABOLITES['NAME'] == str(met.id).split('__91__')[0])
                    
 
                    # Add to STOICH
                    STOICH = addToStoich( metID, current_reaction_id, coeff, STOICH )
                    
                    # Add to METABOLITES
                    #if notInTable(metID,METABOLITES):
                     #   METABOLITES = addToMetabolites(current_metabolite_id, met, model, METABOLITES)
                        
    else:
        break
#print(MODELS)
#print(REACTIONS)
print(METABOLITES)
#print(MOD_REACT)
print(STOICH)