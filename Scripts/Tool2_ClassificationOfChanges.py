# ChangeDetection toolbox
# Tool2 - Classification of land cover changes
# Lukas Zubrietovsky, Hana Bobalova

def classifyChanges(inFC, fieldChange, fieldArea, areaUnit, fieldType,
                   inConTable, tabFieldChange, tabFieldType, noChange,
                   outSumTable, outGraphAbs, outGraphRel):
    
    ''' The tool classifies changes to different types based on the user-provided 
        conversion table.This tool does not create a new change layer, it only 
        updates an existing change layer by adding a changetype attribute. It also
        creates a summary table of absolute and relative proportions of each type 
        of change in the total area and graphs based on these values.'''

    # import system
    import arcpy, os
    from arcpy import env

    # environment settings
    folder = inFC.rsplit("\\", 1)
    env.workspace = folder[0]
    env.overwriteOutput = True
    env.addOutputsToMap = False

    # add field for type of change
    arcpy.AddField_management(inFC, fieldType, "TEXT")


    # conversion table - from excel to arcgis table
    #inExcel = inConTable.rsplit("\\", 1)
    #inExcel = inExcel[0]
    #sheet = inExcel[1]
    #sheet = sheet[:-1]
    arcpy.ExcelToTable_conversion(inConTable, "memory\\inTable")

    # create dictionary from conversion table
    cursor = arcpy.SearchCursor("memory\\inTable")
    dictionary = {}
    with arcpy.da.SearchCursor("memory\\inTable", [tabFieldChange,tabFieldType] ) as cursor:
        for row in cursor:
            changeValue = str(row[0])
            typeValue = str(row[1])
            dictionary[changeValue] = typeValue


    # update layer attribute table with change types from conversion table

    with arcpy.da.UpdateCursor(inFC , (fieldChange,fieldType)) as cursor:
        for row in cursor:
            val = dictionary.get(row[0], "none")
            row[1] = val
            cursor.updateRow(row)

    # add layer to TOC
#     mxd = arcpy.mapping.MapDocument("CURRENT")
#     df = mxd.activeDataFrame
#     addLayer = arcpy.mapping.Layer(inFC)
#     arcpy.mapping.AddLayer(df, addLayer, "AUTO_ARRANGE")
#     del mxd, addLayer

    ## ----------------------------- CREATE TABLE ------------------------

    # create summary table

    if noChange == "NO":
        arcpy.Select_analysis(inFC,"memory\\selectFC")
        with arcpy.da.UpdateCursor("memory\\selectFC", fieldChange) as cursor:
            for row in cursor:
                change = row[0]
                changeSplit = change.split("_")
                code1 = changeSplit[0]
                code2 = changeSplit[1]
                if code1 == code2:
                    cursor.deleteRow()
         
        arcpy.Statistics_analysis("memory\\selectFC", "memory\\sumTable", [[fieldArea, "SUM"]], fieldType)
    else:
        arcpy.Statistics_analysis(inFC, "memory\\sumTable", [[fieldArea, "SUM"]], fieldType)

    ## calculate proportions of area and frequency
    # 1. add proportion fields
    perArea = "per_area"
    perFreq = "per_freq"
    arcpy.AddField_management("memory\\sumTable", perFreq, "DOUBLE")
    arcpy.AddField_management("memory\\sumTable", perArea, "DOUBLE")

    # 2. calculate sum of frequency and area
    fieldFreq = "FREQUENCY"
    fieldSumArea = "SUM_" + fieldArea
    with arcpy.da.SearchCursor("memory\\sumTable",fieldFreq) as cursor:
        listFreq = {row[0] for row in cursor}
    with arcpy.da.SearchCursor("memory\\sumTable",fieldSumArea) as cursor:
        listArea = {row[0] for row in cursor}
    
    sumFreq = float(sum(listFreq))
    sumArea = float(sum(listArea))

    # 3. calculate proportions of frequency and area - add to table
    with arcpy.da.UpdateCursor("memory\\sumTable", (fieldType, fieldFreq, fieldSumArea, perArea, perFreq)) as cursor:
        for row in cursor:
            row[4] = ((row[1] / sumFreq) * 100)
            row[3] = ((row[2] / sumArea) * 100)
            cursor.updateRow(row)

    arcpy.TableToExcel_conversion("memory\\sumTable", outSumTable)

    ## ----------------------------------- GRAPHS ------------------------------

    if outGraphAbs != "" or outGraphRel != "":
        import numpy as np
        import matplotlib.pyplot as plt
    
        listType = [] 
        listAbs = [] 
        listRel = []  
        with arcpy.da.UpdateCursor("memory\\sumTable", (fieldType, fieldSumArea, perArea)) as cursor: 
            for row in cursor:
                listType.append(row[0])
                listAbs.append(row[1])
                listRel.append(row[2])

        # create graph with relative proportions
        if outGraphRel != "":
        
            plt.rcParams.update({'axes.labelsize':'large'})
            plt.rcParams.update({'xtick.labelsize':'large'})
            plt.rcParams.update({'ytick.labelsize':'large'})
        
            fig, ax = plt.subplots()
            distance = 0.3
            bar_width = 0.8
            number = len(listType) + distance
            position_x = np.arange(distance, number)
    
            ax.yaxis.grid()
            ax.set_axisbelow(True)
            graf = plt.bar(position_x, height = listRel)
    
            plt.xlabel('Type of change')
            plt.ylabel('Area (%)')
            plt.title('Proportions of change types')
            plt.xticks(position_x + bar_width/2 , (listType))
    
            plt.tight_layout()
            fig.savefig(outGraphRel) 
            plt.close(fig)

        # create graph with absolute proportions
        if outGraphAbs != "":
    
            dictionary = {"Ares":"a", "Hectares":"ha", "Square meters":"m2", "Square kilometers":"km2"}
            unit = dictionary[areaUnit]
            
            plt.rcParams.update({'axes.labelsize':'large'})
            plt.rcParams.update({'xtick.labelsize':'large'})
            plt.rcParams.update({'ytick.labelsize':'large'})
    
            fig, ax = plt.subplots()
            distance = 0.3
            bar_width = 0.8
            number = len(listType) + distance 
            position_x = np.arange(distance, number)
    
            ax.yaxis.grid()
            ax.set_axisbelow(True)
            graf = plt.bar(position_x, height = listAbs)
    
            plt.xlabel('Type of change')
            plt.ylabel('Area ' + '(' + unit + ')')
            plt.title('Proportions of change types')
            plt.xticks(position_x + bar_width/2 , (listType))
    
            plt.tight_layout()
            fig.savefig(outGraphAbs) 
            plt.close(fig)

if __name__ == '__main__':
    inFC = arcpy.GetParameterAsText(0)            # input feature class of LC changes 
    fieldChange = arcpy.GetParameterAsText(1)     # field with change codes
    fieldArea = arcpy.GetParameterAsText(2)       # area field
    areaUnit = arcpy.GetParameterAsText(3)        # area unit
    fieldType = arcpy.GetParameterAsText(4)       # new field with type of change
    inConTable = arcpy.GetParameterAsText(5)      # input conversion table
    tabFieldChange = arcpy.GetParameterAsText(6)  # field with change codes in conversion table
    tabFieldType = arcpy.GetParameterAsText(7)    # field with type of change in conversion table
    noChange = arcpy.GetParameterAsText(8)        # include areas without change in output statistics
    outSumTable = arcpy.GetParameterAsText(9)    # output summary table
    outGraphAbs = arcpy.GetParameterAsText(10)     # output graph of absolute area proportions of change types (optional)
    outGraphRel = arcpy.GetParameterAsText(11)    # output graph of relative area proportions of change types (optional)
   
    
    classifyChanges(inFC, fieldChange, fieldArea, areaUnit, fieldType,
                   inConTable, tabFieldChange, tabFieldType, noChange,
                   outSumTable, outGraphAbs, outGraphRel)
