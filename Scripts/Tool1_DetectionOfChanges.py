# ChangeDection toolbox
# Tool 1: Detection of land cover changes
# Lukas Zubrietovsky, Hana Bobalova


def detectChanges(inFC1, fieldCode1, inFC2, fieldCode2,
                    fieldChange, fieldArea, areaUnit,
                   noChange, minArea, 
                   outFC, outConTable, outSumTable):

    '''The tool detects land cover (LC) changes by overlay of two vector polygon 
        feature classes and generates a new feature class of LC changes as well 
        as contingency table. Unchanged areas and/or areas of minor changes can 
        be excluded from results. A summary table can be created as needed. '''

    # import system moduls
    import arcpy, os
    from arcpy import env

    # environment settings 
    folder = outFC.rsplit("\\", 1)
    env.workspace = folder[0]
    env.overwriteOutput = True

    # intersection - new layer of changes is created
    arcpy.Intersect_analysis([inFC1, inFC2], "memory\\changeFC", "ALL", "", "")

    # add fields for change code and area
    arcpy.AddField_management("memory\\changeFC", fieldChange, "TEXT")
    arcpy.AddField_management("memory\\changeFC", fieldArea, "DOUBLE")
    
    # join code1 and code2
    if fieldCode1 == fieldCode2:
        fieldCode2 = fieldCode2 + "_1"
    with arcpy.da.UpdateCursor("memory\\changeFC", [fieldChange, fieldCode1, fieldCode2]) as cursor:
        for row in cursor:
            row[0] = str(row[1]) + "_" + str(row[2])
            cursor.updateRow(row)


    # calculate area 
    dictionary = {"Ares":"ARES", "Hectares":"HECTARES", "Square meters":"SQUAREMETERS","Square kilometers":"SQUAREKILOMETERS"}
    areaUnit = dictionary[areaUnit]
    expression = "!SHAPE.AREA@" + areaUnit + "!"
    arcpy.CalculateField_management("memory\\changeFC", fieldArea, expression, "PYTHON")

    # select regions without change
    if noChange == "NO":
       whereClause = '"' + fieldCode1 + '" <> ' + '"' + fieldCode2 + '"'    
       arcpy.Select_analysis("memory\\changeFC", "memory\\noChangeFC", whereClause)
          
    # select minimal area of change
    if minArea != "" and noChange == "YES":
       whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters(outFC, fieldArea), minArea)
       arcpy.Select_analysis("memory\\changeFC", "memory\\minAreaFC", whereClause)                
    if minArea != "" and noChange == "NO":
       whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters("memory\\noChangeFC", fieldArea), minArea)
       arcpy.Select_analysis("memory\\noChangeFC", "memory\\noChangeMinAreaFC", whereClause)
    
    # create final output feature class
    if minArea == "" and noChange == "YES":
       arcpy.CopyFeatures_management("memory\\changeFC", outFC)
    elif minArea == "" and noChange == "NO": 
       arcpy.CopyFeatures_management("memory\\noChangeFC", outFC)
    elif minArea != "" and noChange == "NO":
       arcpy.CopyFeatures_management("memory\\noChangeMinAreaFC", outFC)
    else:
       arcpy.CopyFeatures_management("memory\\minAreaFC", outFC)
                                                                             

    ## ------------------------ CREATE CONTINGENCY TABLE --------------------
    # calculate values of contingency table
    if outConTable != "":
        # summary statistics 
        arcpy.Statistics_analysis(outFC, "memory\\tableChange", [[fieldArea, "SUM"]], fieldChange)
                
        with arcpy.da.SearchCursor(outFC,fieldCode1) as cursor:
                listLC1 = sorted({row[0] for row in cursor})
        with arcpy.da.SearchCursor(inFC2,fieldCode2) as cursor:
                listLC2 = sorted({row[0] for row in cursor})

        # add categories from listLC2 to listLC1
        for value in listLC2:
            if value not in listLC1:
                listLC1.append(value)

        listLC1.sort() # sorted list of unique land cover categories of both periods

        sumArea = "SUM_" + fieldArea
        dictionary = {}
        with arcpy.da.SearchCursor("memory\\tableChange", [fieldChange, sumArea]) as cursor:
            for row in cursor:
                valChange = str(row[0]) 
                valArea = str(row[1]) 
                dictionary[valChange] = valArea
 

        # create contingency statistical table
        import xlwt

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Sheet_1')

        counter = 1
        for i in listLC1:
            sheet.write(0, counter, i)
            counter += 1

        counter2 = 1
        for j in range(len(listLC1)):
            counter = 1
            for k in range(len(listLC1)):
                if counter == 1:
                    sheet.write(counter2, 0, listLC1[j])
                value = str(listLC1[counter2 - 1]) + "_" + str(listLC1[counter - 1])
                sheet.write(counter2, counter, dictionary.get(value,0))
                counter += 1
            counter2 +=1

        workbook.save(outConTable)
        
        # create summary table                              
    if outSumTable != "": 
        
        tablePath = outSumTable.rsplit("\\", 1)  
        tableNameExt = tablePath[1].rsplit(".",1)
        tableName = tableNameExt[0]

        arcpy.analysis.Statistics(outFC, "memory\\tableName", [[fieldArea, "SUM"]], fieldChange)
 
        arcpy.TableToExcel_conversion("memory\\tableName", outSumTable)

if __name__ == '__main__':
    inFC1 = arcpy.GetParameterAsText(0)           # input LC feature class from the first period
    fieldCode1 = arcpy.GetParameterAsText(1)      # input field with LC codes from the first period
    inFC2 = arcpy.GetParameterAsText(2)           # input LC feature class from the second period
    fieldCode2 = arcpy.GetParameterAsText(3)      # input field with LC codes from the second period
    fieldChange = arcpy.GetParameterAsText(4)     # new change code field
    fieldArea = arcpy.GetParameterAsText(5)       # new area field
    areaUnit = arcpy.GetParameterAsText(6)        # output area unit
    noChange = arcpy.GetParameterAsText(7)        # include areas without change in output feature class
    minArea = arcpy.GetParameterAsText(8)         # minimal area to exclude minor changes from the output feature class
    outFC = arcpy.GetParameterAsText(9)           # output LC change feature class
    outConTable = arcpy.GetParameterAsText(10)    # output contingency table (xls)
    outSumTable = arcpy.GetParameterAsText(11)    # output summary table (xls)
  
    detectChanges(inFC1, fieldCode1, inFC2, fieldCode2,
                    fieldChange, fieldArea, areaUnit,
                   noChange, minArea, 
                   outFC, outConTable, outSumTable)    
    
