# ChangeDetection toolbox
# Tool 3 - Hierarchy of land cover changes
# Lukas Zubrietovsky, Hana Bobalova


def detectHierarchy(inFC, fieldChange, fieldArea, areaUnit,
               fieldHL, noChange, outSumTable,
               outGraphAbs, outGraphRel):

    '''Tool determines the hierarchy level of land cover (LC) change (if applicable). 
       A new field with hierarchy level is added to the attribute table of LC change 
       feature class. Summary table is calculated and graphs of area proportions of 
       hierarchy levels are optionally created.  '''

    # import system moduls
    import arcpy, os
    from arcpy import env

    # environment settings
    folder = inFC.rsplit("\\", 1)
    env.workspace = folder[0]
    env.overwriteOutput = True

    # add field 
    arcpy.AddField_management(inFC, fieldHL, "TEXT")

    # calculate values of hierarchy of change and insert to table
    cursor = arcpy.UpdateCursor(inFC, [fieldChange, fieldHL])
    for row in cursor:
        change = row.getValue(fieldChange)
        changeSplit = change.split("_")
        code1 = changeSplit[0]
        code2 = changeSplit[1]
        if code1 == code2:
            row.setValue(fieldHL, 0)
        else:
            counter = 1
            for i in range(len(code1)):
                if code1[i] == code2[i]:
                    counter += 1
                else:
                    break
            hierLevel = str(counter)
            row.setValue(fieldHL, hierLevel)
        cursor.updateRow(row)
    del cursor
    del row

    # add layer to TOC
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = mxd.activeDataFrame
    addLayer = arcpy.mapping.Layer(inFC)
    arcpy.mapping.AddLayer(df, addLayer, "AUTO_ARRANGE")
    del mxd, addLayer

    ## -------------------------------- CREATE TABLE -----------------------------

    if noChange == "NO":
        whereClause = "{} <> '0'".format(arcpy.AddFieldDelimiters(inFC, fieldHL))
        arcpy.Select_analysis(inFC,"in_memory\\selectFC",whereClause)
        arcpy.Statistics_analysis("in_memory\\selectFC", "in_memory\\sumTable", [[fieldArea, "SUM"]], fieldHL)
    else:
        arcpy.Statistics_analysis(inFC, "in_memory\\sumTable", [[fieldArea, "SUM"]], fieldHL)

    ## calculate proportions of area and frequency
    # 1. add proportion fields
    perArea = "per_area"
    perFreq = "per_freq"
    arcpy.AddField_management("in_memory\\sumTable", perFreq, "DOUBLE")
    arcpy.AddField_management("in_memory\\sumTable", perArea, "DOUBLE")
    
    # 2. calculate sum of frequency and area
    fieldFreq = "FREQUENCY"
    fieldSumArea = "SUM_" + fieldArea

    with arcpy.da.SearchCursor("in_memory\\sumTable",fieldFreq) as cursor:
        listFreq = {row[0] for row in cursor}
    with arcpy.da.SearchCursor("in_memory\\sumTable",fieldSumArea) as cursor:
        listArea = {row[0] for row in cursor}
        
    sumFreq = float(sum(listFreq))
    sumArea = float(sum(listArea)) 
    
    # 3. calculate proportions of frequency and area - add to table
    with arcpy.da.UpdateCursor("in_memory\\sumTable", (fieldHL, fieldFreq, fieldSumArea, perArea, perFreq)) as cursor:
        for row in cursor:
            row[4] = ((row[1] / sumFreq) * 100)
            row[3] = ((row[2] / sumArea) * 100)
            cursor.updateRow(row)
        
    arcpy.TableToExcel_conversion("in_memory\\sumTable", outSumTable)
    

    ## ---------------------------- CREATE GRAPHS --------------------------------
    
    if outGraphAbs != "" or outGraphRel != "":
        import numpy as np
        import matplotlib.pyplot as plt
    
        listHL = [] 
        listAbs = [] 
        listRel = []
        with arcpy.da.UpdateCursor("in_memory\\sumTable", (fieldHL, fieldSumArea, perArea)) as cursor: 
            for row in cursor:
                listHL.append(row[0])
                listAbs.append(row[1])
                listRel.append(row[2])

    # create graph with relative proportions
        if outGraphRel != "":
            fig, ax = plt.subplots()
            distance = 0.3
            bar_width = 0.8
            number = len(listHL) + distance
            position_x = np.arange(distance, number)
    
            ax.yaxis.grid()
            ax.set_axisbelow(True)
            graf = plt.bar(left = position_x, height = listRel)
    
            plt.xlabel('Hierarchy level')
            plt.ylabel('Area (%)')
            plt.title('Proportions of hierarchy levels')
            plt.xticks(position_x + bar_width/2 , (listHL))
    
            plt.tight_layout()
            fig.savefig(outGraphRel) 
            plt.close(fig)

    # create graph with absolute proportions
        if outGraphAbs != "":
    
            dictionary = {"Ares":"a", "Hectares":"ha", "Square meters":"m2", "Square kilometers":"km2"}
            unit = dictionary[areaUnit]
    
            fig, ax = plt.subplots()
            distance = 0.3
            bar_width = 0.8
            number = len(listHL) + distance 
            position_x = np.arange(distance, number)
    
            ax.yaxis.grid()
            ax.set_axisbelow(True)
            graf = plt.bar(left = position_x, height = listAbs)
    
            plt.xlabel('Hierarchy level')
            plt.ylabel('Area ' + '(' + unit + ')')
            plt.title('Proportions of hierarchy levels')
            plt.xticks(position_x + bar_width/2 , (listHL))
    
            plt.tight_layout()
            fig.savefig(outGraphAbs) 
            plt.close(fig)

if __name__ == '__main__':
    inFC = arcpy.GetParameterAsText(0)              # input feature class of LC changes
    fieldChange = arcpy.GetParameterAsText(1)       # field with change codes
    fieldArea = arcpy.GetParameterAsText(2)         # area field
    areaUnit = arcpy.GetParameterAsText(3)          # area unit
    fieldHL = arcpy.GetParameterAsText(4)           # new field with hierarchy levels
    noChange = arcpy.GetParameterAsText(5)          # include areas without change in output statistics
    outSumTable = arcpy.GetParameterAsText(6)       # output summary table
    outGraphAbs = arcpy.GetParameterAsText(7)       # output graph of absolute area proportions of hierarchy levels (optional)
    outGraphRel = arcpy.GetParameterAsText(8)       # output graph of relative area proportions of hierarchy levels (optional)
    
    detectHierarchy(inFC, fieldChange, fieldArea, areaUnit,
               fieldHL, noChange, outSumTable,
               outGraphAbs, outGraphRel)
