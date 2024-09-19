# ChangeDetection toolbox
# Tool 4 - Statistical evaluation of land cover changes
# Lukas Zubrietovsky, Hana Bobalova


def computeStatistics(inFC, fieldChange, fieldArea, areaUnit, 
                    codeLC, outStatTable, outGraphNet, outGraphGL, outGraphCon):

    ''' The tool creates three types of statistical tables. First - net change by 
    land cover (LC) category, second - gains and losses by LC category, third - 
    contributors to net change by selected LC category. Optionally, graphs based 
    on these values can be created. '''
    
    # system moduls
    import arcpy, os
    from arcpy import env

    #environment properties 
    folder = inFC.rsplit("\\", 1)
    env.workspace = folder[0]
    env.overwriteOutput = True

    # input values
    fieldSumArea = "SUM_" + fieldArea

    # create statistics table
    arcpy.Statistics_analysis(inFC, "memory\\statTable", [[fieldArea, "SUM"]], fieldChange)

    ## -----------  create lists and dictionaries for calculations -----------
    
    # values from table to lists and dictionaries
    listCode1 = []      # list of LC codes from the first period
    listCode2 = []      # list of LC codes from the second period
    listSumArea = []    # list of area sums for change combinations 

    with arcpy.da.SearchCursor("memory\\statTable", [fieldChange, fieldSumArea]) as cursor:
        for row in cursor:
            change = row[0]
            sumArea = row[1] 
            changeSplit = change.split("_")
            code1 = changeSplit[0] 
            code2 = changeSplit[1]
            listCode1.append(code1)
            listCode2.append(code2)
            listSumArea.append(sumArea)
   
    listLC1 = []          # list of unique values of LC codes from the first period 
    listLC2 = []          # list of unique values of LC codes from the second period
    listSumArea1 = []     # list of area sums for LC categories from the first period
    listSumArea2 = []     # list of area sums for LC categories from the second period
    i = 0
    for code in listCode1:
        if code not in listLC1:
            listLC1.append(code)
            listSumArea1.append(listSumArea[i])
        else:
            k = listLC1.index(code)
            listSumArea1[k] += listSumArea[i]        
        i += 1

    i = 0
    for code in listCode2:
        if code not in listLC2:
            listLC2.append(code)
            listSumArea2.append(listSumArea[i])
        else:
            k = listLC2.index(code)
            listSumArea2[k] += listSumArea[i]        
        i += 1
           
    listLC = []          # list of unique values of LC codes
    for code in listLC1:
        if code not in listLC:
            listLC.append(code)
    for code in listLC2:
        if code not in listLC:
            listLC.append(code)
            
    listLCs = sorted(listLC) # sorted list of unique values of LC codes
                
    # create dictionaries (LC code: area)
    dictLC1 = {} 
    dictLC2 = {} 
    i = 0
    for code in listLC1:
        dictLC1[code] = listSumArea1[i]
        i += 1
    i = 0
    for code in listLC2:
        dictLC2[code] = listSumArea2[i]
        i += 1

    listLC2s = sorted(listLC2)


    
    ## --------------------- calculate first table and graph  - net change ------------------

    listNet = []      # list of net changes for unique LC codes (listLC)
    for code in listLCs:
        if code in dictLC1 and code in dictLC2:
            sumArea1 = dictLC1.get(code)
            sumArea2 = dictLC2.get(code)
            netChange = sumArea2 - sumArea1
            listNet.append(netChange)
        if code in dictLC1 and code not in dictLC2:
            sumArea1 = dictLC1.get(code)
            netChange = 0 - sumArea1
            listNet.append(netChange)
        if code in dictLC2 and code not in listLC1:
            sumArea2 = dictLC2.get(code)
            listNet.append(sumArea2)

    ## -------------------- calculate second table and graph - gains and losses ---------------------

    listGain = []       # list of gains for unique unique LC codes (listLC) 
    listLoss = []       # list of losses for unique unique LC codes (listLC) 

    for code in listLCs:
        gain = 0
        loss = 0
        for i in range(len(listCode1)):
            if code == listCode1[i] and code != listCode2[i]:
                loss -= listSumArea[i]
            if code != listCode1[i] and code == listCode2[i]:
                gain += listSumArea[i]
        if loss != 0:
            listLoss.append(loss)
        else:
            listLoss.append(0)
        if gain != 0:
            listGain.append(gain)
        else:
            listGain.append(0)

    ## -------------------- calculate third table and graph  - contributors to net change -------------------

    if codeLC != "":
        listCon = []        # list of contributors (LC codes)
        listConArea = []    # list of area of contributions

        for i in range(len(listCode1)):
            if codeLC == listCode1[i] and codeLC != listCode2[i]:
                listCon.append(listCode2[i])
                area = 0 - listSumArea[i]
                listConArea.append(area)
            if codeLC != listCode1[i] and codeLC == listCode2[i]:
                listCon.append(listCode1[i])
                listConArea.append(listSumArea[i])
            if codeLC != listCode1[i] and codeLC != listCode2[i]:
                if listCode1[i] not in listCon:
                    listCon.append(listCode1[i])
                    listConArea.append(0)
                if listCode2[i] not in listCon:
                    listCon.append(listCode2[i])
                    listConArea.append(0)

        listUnCon = []          # unique list of contributors
        listUnConArea = []      # unique list of area of contributions
        i = 0
        for code in listCon:
            if code not in listUnCon:
                listUnCon.append(listCon[i])
                listUnConArea.append(listConArea[i])
            else:
                k = listUnCon.index(code)
                listUnConArea[k] += listConArea[i]        
            i += 1
        
        # create dictionary and sorted lists of contributors and areas
        dictCon = {}
        i = 0
        for code in listUnCon:
            dictCon[code] = listUnConArea[i]
            i += 1
    
        listUnCons = sorted(listUnCon)  # sorted list of contributors
        listUnConAreas = []             # sorted list of area of contributions
        for code in listUnCons:
            listUnConAreas.append(dictCon.get(code)) 
                   

    ## ---------------------------create xls table --------------------------------
    import xlwt

    # create woorkbook with three sheets
    workbook = xlwt.Workbook()
    sheet1 = workbook.add_sheet("Net change")
    sheet2 = workbook.add_sheet("Gains and Losses")
    if codeLC != "":
        sheet3 = workbook.add_sheet("Contributors")

    # first table - categories of the first and second period, net change             
    sheet1.write(0,0, "All categories")                                                 
    sheet1.write(0,1, "Area in first period")
    sheet1.write(0,2, "Area in second period")
    sheet1.write(0,3, "Net change")
    for i in range(len(listLCs)):
        sheet1.write(i+1,0, listLCs[i])
        sheet1.write(i+1,1, dictLC1.get(listLCs[i]))
        sheet1.write(i+1,2, dictLC2.get(listLCs[i]))
        sheet1.write(i+1,3, listNet[i])

    # second table - gains and losses by category
    sheet2.write(0,0, "Category")
    sheet2.write(0,1, "Gain")
    sheet2.write(0,2, "Loss")
    for i in range(len(listLCs)):
        sheet2.write(i+1, 0, listLCs[i])
        sheet2.write(i+1, 1, listGain[i])
        sheet2.write(i+1, 2, listLoss[i])
        
    # third table - contributos to net change of category
    if codeLC != "":
        sheet3.write(0,0, "Category " + codeLC)
        sheet3.write(0,1, "Area of change")
        for i in range(len(listUnCons)):
            sheet3.write(i+1, 0, listUnCons[i])
            sheet3.write(i+1, 1, listUnConAreas[i])
            
    workbook.save(outStatTable)

    ## ---------------------------- create graphs --------------------------------
    if outGraphNet != "" or outGraphGL != "" or outGraphCon != "":
        
        import matplotlib.pyplot as plt
        plt.rcdefaults()
        import numpy as np
        import matplotlib.pyplot as plt
        
        listLCs.reverse() # graph writes from the bottom

        dictUnits = {"Ares":"a", "Hectares":"ha", "Square meters":"m2", "Square kilometers":"km2"}
        unit = dictUnits[areaUnit]
        
    # create first graph - net change by category
    if outGraphNet != "":

        listNet.reverse()

        plt.rcParams.update({'axes.labelsize':'large'})
        plt.rcParams.update({'xtick.labelsize':'large'})
        plt.rcParams.update({'ytick.labelsize':'large'})

        space1 = 1
        quantity1 =  len(listLCs) + space1
        y_pos1 = np.arange(space1, quantity1)

        plt.grid(True)
        plt.barh(y_pos1, listNet, align='center', color = "blue")
        plt.yticks(y_pos1, listLCs)
        plt.xlabel('Area ' + '(' +  unit + ')')
        plt.title('Net change of area by category')
        plt.savefig(outGraphNet)
        plt.close()

    # create second graph - gains and losses
    if outGraphGL != "":

        listGain.reverse()
        listLoss.reverse()

        plt.rcParams.update({'axes.labelsize':'large'})
        plt.rcParams.update({'xtick.labelsize':'large'})
        plt.rcParams.update({'ytick.labelsize':'large'})

        space2 = 1
        quantity2 =  len(listLCs) + space2
        y_pos2 = np.arange(space2, quantity2)

        plt.grid(True)
        plt.barh(y_pos2, listGain, align='center', color = "red")
        plt.barh(y_pos2, listLoss, align='center', color = "blue")
        plt.yticks(y_pos2, listLCs)
        plt.xlabel('Area ' + '(' +  unit + ')')
        plt.title('Gains and losses of area by category')
        plt.savefig(outGraphGL)
        plt.close()

    # create third graph - contributors to net change of category
    if outGraphCon != "":
        
        listUnCons.reverse()
        listUnConAreas.reverse()

        plt.rcParams.update({'axes.labelsize':'large'})
        plt.rcParams.update({'xtick.labelsize':'large'})
        plt.rcParams.update({'ytick.labelsize':'large'})

        space3 = 1
        quantity3 = len(listUnCons) + space3
        y_pos3 = np.arange(space3, quantity3)

        plt.grid(True)
        plt.barh(y_pos3, listUnConAreas, align='center', color = "blue")
        plt.yticks(y_pos3, listUnCons)
        plt.xlabel('Area ' + '(' +  unit + ')') 
        plt.title('Contributors to net change of category ' + codeLC)
        plt.savefig(outGraphCon)
        plt.close()

if __name__ == '__main__':
    inFC = arcpy.GetParameterAsText(0)              # input feature class of LC changes
    fieldChange = arcpy.GetParameterAsText(1)       # field with change codes
    fieldArea = arcpy.GetParameterAsText(2)         # area field
    areaUnit = arcpy.GetParameterAsText(3)          # area unit
    codeLC = arcpy.GetParameterAsText(4)            # code of LC category
    outStatTable = arcpy.GetParameterAsText(5)      # output statistical table
    outGraphNet = arcpy.GetParameterAsText(6)       # output graph of net change
    outGraphGL = arcpy.GetParameterAsText(7)        # output graph of gains and losses
    outGraphCon = arcpy.GetParameterAsText(8)       # output graph of contributors to net change
    
    computeStatistics(inFC, fieldChange, fieldArea, areaUnit, 
                    codeLC, outStatTable, outGraphNet, outGraphGL, outGraphCon)
