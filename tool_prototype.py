
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:19:50 2025

@author: pnavaro
"""

#%% Import libraries and define global variables

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
import squarify
import plotly.graph_objects as go
import plotly.io as pio
import os
pio.renderers.default='browser'

#folder_path=r"C:\Users\pnavaro\OneDrive - ETH Zurich\Desktop\1-UP2030\2-Tool development\tutorial_example"#C:\Users\pnavaro\tool_up2030
plt.rcParams["font.family"] = "serif"

#%% Import the excels to dataframe

def import_excels(folder_path,city_file_path):
    #City data
    DFcity_data=pd.read_excel(city_file_path, sheet_name = 'added_geom_info')
    #DFcity_data = DFcity_data.set_index('fid')
    
    #INIES database
    DFinies=pd.read_excel(folder_path+'\lca_database.xlsx', sheet_name = 'lca_data')
    DFinies = DFinies.set_index('nom_fdes')
    
    return ([DFcity_data,DFinies])

#LD=import_excels(folder_path)
#DFcity_data=LD[0]
#DFinies=LD[1]

#%% Add case of reuse in environmental impact of INIES database

def add_reuse_inies(DFinies):
    DFinies=DFinies.fillna(0)
    DFinies['climate change - reuse (B-C)']=DFinies['changement_climatique_total_total_cycle_de_vie']-DFinies['changement_climatique_total_etape_de_production']
    return(DFinies)

#DFinies=add_reuse_inies(DFinies)
#%% Import Façade options data

def load_facade_blocks(path, sheet_name=0):
    # 1) Read entire sheet without interpreting any row as header
    df = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=object)

    blocks = {}
    i = 0
    N = len(df)

    while i < N:
        row = df.iloc[i]
        cellA = str(row[0]).strip() if pd.notna(row[0]) else ''

        # 2) Detect start of a block
        if cellA == 'Facade':
            # key = content of B at this row
            key = row[1]
            # 3) Find the "Material" header row within this block
            j = i + 1
            while j < N:
                rjA = df.iloc[j, 0]
                if isinstance(rjA, str) and rjA.strip() == 'Material':
                    break
                j += 1
            else:
                raise ValueError(f"'Material' not found after Facade at line {i}")

            # 4) Use that row j as column-headers
            header = df.iloc[j].tolist()

            # 5) Find the "Ref" row that ends this block
            k = j + 1
            while k < N:
                rkA = df.iloc[k, 0]
                if isinstance(rkA, str) and rkA.strip() == 'Ref':
                    break
                k += 1
            else:
                raise ValueError(f"'Ref' not found after Material (line {j})")

            # 6) Slice the data between Material+1 and Ref (exclusive)
            data = df.iloc[j + 1:k+1].copy()
            data.columns = header
            

            # 7) Drop any columns whose header cell is empty or NaN
            valid_cols = [col for col in header if pd.notna(col) and str(col).strip() != '']
            data = data[valid_cols].reset_index(drop=True)
            data = data.set_index('Material')
            data = data.transpose()

            # 8) Store in dict
            blocks[key] = data

            # 9) Jump past this block
            i = k + 1
        else:
            i += 1

    return blocks

"""
# Example usage:
blocks = load_facade_blocks(folder_path+"\\facade_options.xlsx", sheet_name="all")

# Now blocks is a dict. To see your keys:
print(blocks.keys())

# And inspect one of the DataFrames:
print(blocks[next(iter(blocks))].head(8))

print(blocks["brick wall with insulation"].loc["brick", 
                      "Unit"])
"""

#%% Determine which façade corresponds to which building

def determine_facade_building(DFcity_data):
    facade_type=[]
    for height in DFcity_data['Height']:
        if height<7:
            facade_type.append('brick wall without insulation')
        elif height<10:
            facade_type.append('concrete block without insulation')
        else :
            facade_type.append('concrete wall without insulation')

    DFcity_data['facade_type']=facade_type
    return(DFcity_data)
    
#determine_facade_building(DFcity_data)

#%% Calculate material quantities of the facade before renovation

def calculate_mat_quant_before_reno(DFcity_data,blocks):

    #Get the facade surface
    DFcity_data['facade_surface']=DFcity_data['Height']*DFcity_data['perimeter']
    
    #Get the material for the facade
    #For this purpose a dictionary Dmaterials_LCA is created and contains the materials and LCA
    #It is linked to DFcity_data as the key of Dmaterials_LCA are the fid identifier
    Dmat_bef_reno={}
    for i in range(len(DFcity_data['facade_type'])):
        facade_type=DFcity_data.loc[i,"facade_type"]
        print(facade_type)
        DFmat=blocks[facade_type].copy()
        DFmat['Quantity in building for LCA']=DFmat['Quantity for LCA (FU)']*DFcity_data.loc[i,"facade_surface"]
        DFmat['Quantity in building for MFA']=DFmat['Quantity for 1m2 of facade']*DFcity_data.loc[i,"facade_surface"]
        
    
        #Add doors
        Ddoor={#'Index':'door',
           'Unit':'',
           'Quantity for 1m2 of material':'',
           'Quantity for 1m2 of facade':'',
           'Quantity for LCA (FU)':'',
           'Life span':'',
           'Inies name':'Bloc porte extérieur ACIER ? modèles non vitrés - ZILTEN - Acier 48',
           'Ref':'',
           'Low reuse':0.3,
           'High reuse':0.6,
           'Max reuse': 1,
           'Quantity in building for LCA':DFcity_data.loc[i,"perimeter"]/15*2*0.83, #a door of 2*0.83 every 15m around the perimeter of the building
           'Quantity in building for MFA':DFcity_data.loc[i,"perimeter"]/15*2*0.83} # ajouter les kg
        
        DFmat.loc['door'] = Ddoor
        Dmat_bef_reno[DFcity_data.loc[i,"fid"]]=DFmat
    print(Dmat_bef_reno)
    return(Dmat_bef_reno)

#Dmat_bef_reno=calculate_mat_quant_before_reno(DFcity_data,blocks)
#%% Calculate the future avoided impacts from reusing the deconstructed materials 

def calculate_avoided_impact_before_reno(Dmat_aft_reno,DFcity_data,DFinies):

    Lavoided=[]
    Limpact_low_reuse=[]
    Limpact_high_reuse=[]
    Limpact_max_reuse=[]
    Limpact_no_reuse=[]
    
    for fid in Dmat_aft_reno.keys():
        Lbc_impact=[]
        Lac_impact=[]
        Lprob_low=[]
        Lprob_high=[]
        Lprob_max=[]
        for mat in Dmat_aft_reno[fid].index.tolist():
            inies_name=Dmat_aft_reno[fid].loc[mat,"Inies name"]
            Lbc_impact.append(DFinies.loc[inies_name,'climate change - reuse (B-C)'])
            Lac_impact.append(DFinies.loc[inies_name,'changement_climatique_total_total_cycle_de_vie'])
            Lprob_low.append(Dmat_aft_reno[fid].loc[mat,"Low reuse"])
            Lprob_high.append(Dmat_aft_reno[fid].loc[mat,"High reuse"])
            Lprob_max.append(Dmat_aft_reno[fid].loc[mat,"Max reuse"])
        
        
        Dmat_aft_reno[fid]['Climate change A-C material']=Lac_impact
        Dmat_aft_reno[fid]['Climate change A-C building']=Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        
        Dmat_aft_reno[fid]['Prob reuse low']=Lprob_low
        Dmat_aft_reno[fid]['Prob reuse high']=Lprob_high
        Dmat_aft_reno[fid]['Prob reuse max']=Lprob_max
        
        Dmat_aft_reno[fid]['Climate change reuse A4-C material']=Lbc_impact
        Dmat_aft_reno[fid]['Climate change reuse A4-C building']=Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - low reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse low']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse low'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - high reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse high']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse high'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - max reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse max']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse max'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        
        
        Dmat_aft_reno[fid]['Avoided from reuse A1-3 building']=Dmat_aft_reno[fid]['Climate change A-C building']-Dmat_aft_reno[fid]['Climate change - max reuse A4-C building']
        
        Lavoided.append(Dmat_aft_reno[fid]['Avoided from reuse A1-3 building'].sum())
        Limpact_low_reuse.append(Dmat_aft_reno[fid]['Climate change - low reuse A4-C building'].sum())
        Limpact_high_reuse.append(Dmat_aft_reno[fid]['Climate change - high reuse A4-C building'].sum())
        Limpact_max_reuse.append(Dmat_aft_reno[fid]['Climate change - max reuse A4-C building'].sum())
        Limpact_no_reuse.append(Dmat_aft_reno[fid]['Climate change A-C building'].sum())
        
    DFcity_data['future_avoided']=Lavoided
    DFcity_data['future_impact_low_reuse']=Limpact_low_reuse
    DFcity_data['future_impact_high_reuse']=Limpact_high_reuse
    DFcity_data['future_impact_max_reuse']=Limpact_max_reuse
    DFcity_data['future_impact_no_reuse']=Limpact_no_reuse
    DFcity_data['future_avoided']=Lavoided
    DFcity_data['future_avoided/m2']=DFcity_data['future_avoided']/(DFcity_data['AREA_M2']*DFcity_data['N_StairsAb'])
    
#calculate_mat_quant_before_reno(Dmat_bef_reno,DFcity_data,DFinies)

#%% Calculate material quantities of the facade after renovation

def get_correspondance_dict(path):
    # Load the Excel file
    df = pd.read_csv(path)
    
    # Convert first two columns to dictionary
    result_dict = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    
    return(result_dict)


def calculate_mat_quant_after_reno(DFcity_data,blocks,folder_path):
    #Get the correspondance dictionary for façade
    Dcorres=get_correspondance_dict(folder_path+"/correspondance_table.csv")
    #Get the facade surface
    DFcity_data['facade_surface']=DFcity_data['Height']*DFcity_data['perimeter']
    
    #Get the material for the facade
    #For this purpose a dictionary Dmaterials_LCA is created and contains the materials and LCA
    #It is linked to DFcity_data as the key of Dmaterials_LCA are the fid identifier
    Dmat_aft_reno={}
    for i in range(len(DFcity_data['facade_type'])):
        init_facade=DFcity_data.loc[i,"facade_type"]
        if init_facade in Dcorres.keys():
            facade_type=Dcorres[DFcity_data.loc[i,"facade_type"]]
        else:
            facade_type=init_facade
        DFmat=blocks[facade_type].copy()
        DFmat['Quantity in building for LCA']=DFmat['Quantity for LCA (FU)']*DFcity_data.loc[i,"facade_surface"]
        DFmat['Quantity in building for MFA']=DFmat['Quantity for 1m2 of facade']*DFcity_data.loc[i,"facade_surface"]
        
        #Add doors
        Ddoor={#'Index':'door',
           'Unit':'',
           'Quantity for 1m2 of material':'',
           'Quantity for 1m2 of facade':'',
           'Quantity for LCA (FU)':'',
           'Life span':'',
           'Low reuse':0.3,
           'High reuse':0.6,
           'Max reuse': 1,
           'Inies name':'Bloc porte extérieur ACIER ? modèles non vitrés - ZILTEN - Acier 48',
           'Ref':'',
           'Quantity in building for LCA':DFcity_data.loc[i,"perimeter"]/15*2*0.83, #a door of 2*0.83 every 15m around the perimeter of the building
           'Quantity in building for MFA':DFcity_data.loc[i,"perimeter"]/15*2*0.83} # ajouter les kg
        
        DFmat.loc['door'] = Ddoor
        
        Dmat_aft_reno[DFcity_data.loc[i,"fid"]]=DFmat
        
    return(Dmat_aft_reno)

#Dmat_aft_reno=calculate_mat_quant_after_reno(DFcity_data,blocks)
    
#%% Calculate avoided impact from using reused material for the renovation


def calculate_avoided_impact_after_reno(Dmat_aft_reno,DFcity_data,DFinies):
    
    Lavoided=[]
    Limpact_low_reuse=[]
    Limpact_high_reuse=[]
    Limpact_max_reuse=[]
    Limpact_no_reuse=[]
    
    for fid in Dmat_aft_reno.keys():
        Lbc_impact=[]
        Lac_impact=[]
        Lprob_low=[]
        Lprob_high=[]
        Lprob_max=[]
        for mat in Dmat_aft_reno[fid].index.tolist():
            inies_name=Dmat_aft_reno[fid].loc[mat,"Inies name"]
            Lbc_impact.append(DFinies.loc[inies_name,'climate change - reuse (B-C)'])
            Lac_impact.append(DFinies.loc[inies_name,'changement_climatique_total_total_cycle_de_vie'])
            Lprob_low.append(Dmat_aft_reno[fid].loc[mat,"Low reuse"])
            Lprob_high.append(Dmat_aft_reno[fid].loc[mat,"High reuse"])
            Lprob_max.append(Dmat_aft_reno[fid].loc[mat,"Max reuse"])
        
        
        Dmat_aft_reno[fid]['Climate change A-C material']=Lac_impact
        Dmat_aft_reno[fid]['Climate change A-C building']=Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        
        Dmat_aft_reno[fid]['Prob reuse low']=Lprob_low
        Dmat_aft_reno[fid]['Prob reuse high']=Lprob_high
        Dmat_aft_reno[fid]['Prob reuse max']=Lprob_max
        
        Dmat_aft_reno[fid]['Climate change reuse A4-C material']=Lbc_impact
        Dmat_aft_reno[fid]['Climate change reuse A4-C building']=Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - low reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse low']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse low'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - high reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse high']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse high'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        Dmat_aft_reno[fid]['Climate change - max reuse A4-C building']=Dmat_aft_reno[fid]['Prob reuse max']*Dmat_aft_reno[fid]['Climate change reuse A4-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA'] + (1-Dmat_aft_reno[fid]['Prob reuse max'])*Dmat_aft_reno[fid]['Climate change A-C material']*Dmat_aft_reno[fid]['Quantity in building for LCA']
        
        
        Dmat_aft_reno[fid]['Avoided impact from using reuse']=Dmat_aft_reno[fid]['Climate change A-C building']-Dmat_aft_reno[fid]['Climate change - max reuse A4-C building']
        
        Lavoided.append(Dmat_aft_reno[fid]['Avoided impact from using reuse'].sum())
        Limpact_low_reuse.append(Dmat_aft_reno[fid]['Climate change - low reuse A4-C building'].sum())
        Limpact_high_reuse.append(Dmat_aft_reno[fid]['Climate change - high reuse A4-C building'].sum())
        Limpact_max_reuse.append(Dmat_aft_reno[fid]['Climate change - max reuse A4-C building'].sum())
        Limpact_no_reuse.append(Dmat_aft_reno[fid]['Climate change A-C building'].sum())
        
    DFcity_data['reno_avoided']=Lavoided
    DFcity_data['reno_impact_low_reuse']=Limpact_low_reuse
    DFcity_data['reno_impact_high_reuse']=Limpact_high_reuse
    DFcity_data['reno_impact_max_reuse']=Limpact_max_reuse
    DFcity_data['reno_impact_no_reuse']=Limpact_no_reuse
    
    DFcity_data['reno_avoided/m2']=DFcity_data['reno_avoided']/(DFcity_data['AREA_M2']*DFcity_data['N_StairsAb'])
    
    DFcity_data['compacity']=DFcity_data['AREA_M2']*DFcity_data['N_StairsAb']/DFcity_data['perimeter']
    

#calculate_mat_quant_after_reno(Dmat_aft_reno,DFcity_data,DFinies)
#%% export data

def export_lca_ca(folder_path,DFcity_data,Dmat_aft_reno,Dmat_bef_reno):
    DFcity_data.to_csv(folder_path+"\city_data_with_ca_lca.csv")
    os.makedirs(folder_path+'\OUT_using_reused_material', exist_ok=True)
    os.makedirs(folder_path+'\OUT_reusing_from_deconstruction', exist_ok=True)
    
    for fid in Dmat_aft_reno.keys():
        Dmat_aft_reno[fid].to_csv(folder_path+'\OUT_using_reused_material\\'+str(fid)+"_using_reused_material.csv")
        
    for fid in Dmat_bef_reno.keys():
        Dmat_bef_reno[fid].to_csv(folder_path+'\OUT_reusing_from_deconstruction\\'+str(fid)+"_reusing_from_deconstruction.csv")

#export_lca_ca(DFcity_data,Dmat_aft_reno,Dmat_bef_reno)
#%% Plot the contribution of elements avoided impacts for every building

Dmat_color={'concrete wall':'lightgrey' ,
'steel rebar': 'blue',
'window': 'plum',
'door': 'lavender',
'concrete block':'grey' ,
'mortar': 'gold',
'coating': 'moccasin' ,
'brick':'lightcoral' ,
'insulation': 'lightblue'
}

def plot_histo(folder_path,D,name_avoided_impact,title='Per building impact'):
    
    
    
    #get the material
    Dmaterials={}
    for building in D.keys():
        for mat in list(D[building].index):
            Dmaterials[mat]=[]
            
    
    #Get the LCA values
    for mat in Dmaterials:
        #print("'"+mat+"': ,")
        for building in D.keys():
            if mat in list(D[building].index):
                Dmaterials[mat].append(D[building].loc[mat,name_avoided_impact])
            else :
                Dmaterials[mat].append(0)
                
    #Plot the histogram of materials LCA depending on the building
    
    
    
    fig, ax = plt.subplots()
    thickness_bar=0.6
    X_axis = np.arange(0,len(D.keys())*(thickness_bar*(2)),thickness_bar*(2))
    Y_offset = np.zeros(len(X_axis))
    for mat in Dmaterials:
        if mat != 'steel rebar' and mat != 'mortar':
            ax.bar(X_axis,Dmaterials[mat],  bottom = Y_offset,color=Dmat_color[mat], 
                               width=thickness_bar,label=mat,edgecolor='black',linewidth=0.5)
            Y_offset = Y_offset+np.array(Dmaterials[mat])
        
    plt.legend(bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
    plt.xticks(X_axis, D.keys())
    plt.xlabel('building fid') 
    plt.ylabel('kgCO2eq') 
    plt.suptitle(title) 
    fig.set_figheight(4)
    fig.set_figwidth(8)
    ax.yaxis.grid(color='gray', linestyle='dashed')
    
    os.makedirs(folder_path+'\OUT_FIG', exist_ok=True)
    
    plt.savefig(folder_path+'\OUT_FIG\\per_building_'+name_avoided_impact+'.jpg',bbox_inches='tight',dpi=150) 
    plt.draw()

#plot_histo(Dmat_bef_reno,'Avoided from reuse A1-3 building')
#plot_histo(Dmat_aft_reno,'Avoided impact from using reuse')

#%% Plot the contribution of elements avoided impacts for every level of reuse

def plot_histo_level_reuse(folder_path,D,title='Per level of reuse'):
    
    Dlevel_reuse={}
    Llevel_reuse=['Climate change A-C building',
                        'Climate change - low reuse A4-C building',
                        'Climate change - high reuse A4-C building',
                        'Climate change - max reuse A4-C building']
    Lxlabel=['no reuse',
                        'low reuse',
                        'high reuse',
                        'max reuse']
    for level_reuse in Llevel_reuse:
        
        #get the material
        Dmaterials={}
        for building in D.keys():
            for mat in list(D[building].index):
                Dmaterials[mat]=0
            
        #Get the LCA values
        for mat in Dmaterials:
            #print("'"+mat+"': ,")
            for building in D.keys():
                if mat in list(D[building].index):
                    Dmaterials[mat]+=D[building].loc[mat,level_reuse]
                else :
                    Dmaterials[mat]+=0
                    
        Dlevel_reuse[level_reuse]=Dmaterials
        
    fig, ax = plt.subplots()
    thickness_bar=0.6
    X_axis = np.arange(0,len(Llevel_reuse)*(thickness_bar*(2)),thickness_bar*(2))
    Y_offset = np.zeros(len(X_axis))
    print(Dlevel_reuse[Llevel_reuse[0]].keys())
    for mat in Dlevel_reuse[Llevel_reuse[0]].keys():
        print([Dlevel_reuse[level_reuse][mat] for level_reuse in Llevel_reuse])
        if mat != 'steel rebar' and mat != 'mortar':
            Y_values=[Dlevel_reuse[level_reuse][mat] for level_reuse in Llevel_reuse]
            ax.bar(X_axis,Y_values,  bottom = Y_offset,color=Dmat_color[mat], 
                               width=thickness_bar,label=mat,edgecolor='black',linewidth=0.5)
            Y_offset = Y_offset+np.array(Y_values)
        
    plt.legend(bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
    plt.xticks(X_axis, Lxlabel)
    #plt.xlabel('building fid') 
    plt.ylabel('kgCO2eq') 
    plt.suptitle(title) 
    fig.set_figheight(4)
    fig.set_figwidth(8)
    ax.yaxis.grid(color='gray', linestyle='dashed')
    
    os.makedirs(folder_path+'\OUT_FIG', exist_ok=True)
    
    plt.savefig(folder_path+'\OUT_FIG\\'+title+'.jpg',bbox_inches='tight',dpi=150) 
    plt.draw()
    


#%% Plot the overall material avoided impact

def plot_square(folder_path,D,name_avoided_impact,title='Material contribution'):
    plt.figure() 
    Dmaterials={}
    for building in D.keys():
        for mat in list(D[building].index):
            Dmaterials[mat]=0
            
    for building in D.keys():
        for mat in list(D[building].index):
            Dmaterials[mat]+=D[building].loc[mat,name_avoided_impact]
    

    # plot it
    tot=sum([Dmaterials[key] for key in Dmaterials.keys() if Dmaterials[key]!=0])
    squarify.plot(sizes=[Dmaterials[key] for key in Dmaterials.keys() if Dmaterials[key]!=0], 
                  label=[key+'\n'+str(round(Dmaterials[key]/tot*100))+'%' for key in Dmaterials.keys() if Dmaterials[key]!=0], 
                  alpha=.8,
                  #ec = 'white',
                  color=[Dmat_color[key] for key in Dmaterials.keys() if Dmaterials[key]!=0])
    plt.axis('off')
    plt.suptitle(title) 
    plt.savefig(folder_path+'\OUT_FIG\\all_'+name_avoided_impact+'.jpg',bbox_inches='tight',dpi=150) 
    plt.draw()
    
#plot_square(Dmat_bef_reno,'Avoided from reuse A1-3 building','Reusing the elements')
#plot_square(Dmat_aft_reno,'Avoided impact from using reuse','Using reused mat')


#%% Plot sankey of material flows

def plot_sankey_mat_flow(folder_path,Dmat_bef_reno,Dmat_aft_reno):

    Llabel = []
    Lcolor = []
    Lx = []
    
    #Preparatory work
    Dmat_bef={}
    for building in Dmat_bef_reno.keys():
        for mat in list(Dmat_bef_reno[building].index):
            Dmat_bef[mat]=0
            
    Dmat_aft={}
    for building in Dmat_aft_reno.keys():
        for mat in list(Dmat_aft_reno[building].index):
            Dmat_aft[mat]=0
            
    
    #Defining the nodes
    Dcorres_mat_bef={}
    for mat in Dmat_bef.keys():
        Llabel.append('out-'+mat)
        Lcolor.append(Dmat_color[mat])
        Lx.append(0.1)
        Dcorres_mat_bef[mat]=len(Llabel)-1
    
    Dcorres_building={}
    for building in Dmat_aft_reno.keys():
        Llabel.append(building)
        Lcolor.append('grey')
        Lx.append(0.3)
        Dcorres_building[building]=len(Llabel)-1
    
    Dcorres_mat_aft={}
    for mat in Dmat_aft.keys():
        Llabel.append('in-'+mat)
        Lcolor.append(Dmat_color[mat])
        Lx.append(0.5)
        Dcorres_mat_aft[mat]=len(Llabel)-1
        
    #Defining the links
    Lsource=[]
    Ltarget=[]
    Lvalue=[]
    Lcolor_link=[]
    for building in Dmat_bef_reno.keys():
        for mat in list(Dmat_bef_reno[building].index):
            Lsource.append(Dcorres_mat_bef[mat])
            Ltarget.append(Dcorres_building[building])
            Lvalue.append(Dmat_bef_reno[building].loc[mat,'Quantity in building for MFA'])
            Lcolor_link.append(Dmat_color[mat])
    
    for building in Dmat_aft_reno.keys():
        for mat in list(Dmat_aft_reno[building].index):
            Lsource.append(Dcorres_building[building])
            Ltarget.append(Dcorres_mat_aft[mat])
            Lvalue.append(Dmat_aft_reno[building].loc[mat,'Quantity in building for MFA'])
            Lcolor_link.append(Dmat_color[mat])
            
    
    #Plotting
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = Llabel,
          color = Lcolor,
          x = Lx
        ),
        link = dict(
          source = Lsource, # indices correspond to labels, eg A1, A2, A1, B1, ...
          target = Ltarget,
          value = Lvalue,
          color = Lcolor_link
      ))])
    
    fig.write_html(folder_path+"\OUT_FIG\sanky_mfa.html")
    fig.show()

#%%
#%% RUN THE TOOL

def run_circular_urban_planning(folder_path,city_file_path):
    
    #Import the excels to dataframe
    LD=import_excels(folder_path,city_file_path)
    DFcity_data=LD[0]
    DFinies_1=LD[1]
    
    #Add case of reuse in environmental impact of INIES database
    DFinies=add_reuse_inies(DFinies_1)
    
    #Import Façade options data
    blocks = load_facade_blocks(folder_path+"\\facade_options.xlsx", sheet_name="all")

    #Determine which façade corresponds to which building
    determine_facade_building(DFcity_data)
    
    #Calculate material quantities of the facade before renovation
    Dmat_bef_reno=calculate_mat_quant_before_reno(DFcity_data,blocks)
    
    #Calculate the future avoided impacts from reusing the deconstructed materials 
    calculate_avoided_impact_before_reno(Dmat_bef_reno,DFcity_data,DFinies)
    
    #Calculate material quantities of the facade after renovation
    Dmat_aft_reno=calculate_mat_quant_after_reno(DFcity_data,blocks,folder_path)
    
    #Calculate avoided impact from using reused material for the renovation
    calculate_avoided_impact_after_reno(Dmat_aft_reno,DFcity_data,DFinies)
    
    
    #export data
    export_lca_ca(folder_path,DFcity_data,Dmat_aft_reno,Dmat_bef_reno)
    
    #Plot the contribution of elements avoided impacts for every building
    plot_histo(folder_path,Dmat_bef_reno,'Avoided from reuse A1-3 building','Potential avoided impact per building if elements are reused')
    plot_histo(folder_path,Dmat_aft_reno,'Avoided impact from using reuse', 'Potential avoided impact per building if renovation is conducted with reused elements')
    plot_histo_level_reuse(folder_path,Dmat_bef_reno,'Per level of reuse - Deconstruction')
    plot_histo_level_reuse(folder_path,Dmat_aft_reno,'Per level of reuse - Renovation')
    #Plot the overall material avoided impact
    plot_square(folder_path,Dmat_bef_reno,'Avoided from reuse A1-3 building','Potential avoided impact contribution if elements are reused')
    plot_square(folder_path,Dmat_aft_reno,'Avoided impact from using reuse','Potential avoided impact contribution if renovation is conducted with reused elements')
    
    
#run_circular_urban_planning(folder_path,r"C:\Users\pnavaro\OneDrive - ETH Zurich\Desktop\1-UP2030\2-Tool development\tutorial_example\lisbon_data_with_perimeter.xlsx")