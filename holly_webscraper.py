import threading

import requests, csv
from bs4 import BeautifulSoup
import s3cookiejar, mechanize
import pandas as pd
import time
import os
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.edge.options import Options
# from selenium.webdriver.support.select import Select
# from selenium.webdriver.common.keys import Keys



'''
Author: Jack C. Gee
'''
#########################################################

holly_ip = "http://138.253.226.153"
#
# for i in range(2):
#     path_parent = os.path.dirname(os.getcwd())
#     os.chdir(path_parent)

# pro_soft_dir = os.getcwd()
# optimiser_dir = pro_soft_dir + "/Bayesian Optimiser/fe_optimizer-master/Optimizer/"

ss_tar = False # set to true if subsample target amounts need to be used
validation_on = False
material_check_on = False
material_name_switch= True
convert_solid_g2mg = True




def holly_login():
    cj = s3cookiejar.S3CookieJar()
    br = mechanize.Browser()
    br.set_handle_robots(False)  # no robots
    br.set_handle_refresh(False)
    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    # [('User-agent', 'Firefox')]
    br.set_cookiejar(cj)  # allow everything to be written to
    br.open(holly_ip +"/RobotRun")
    br.select_form(nr=0)
    br.form['UserName'] = 'livad\mif015'
    br.form['Password'] = 'emsfl0w1'
    br.form['CompanyId'] = ["1", ]  # 1 labman, 2 UoL, 3 Unilever
    br.submit()

    return br

def holly_complete_check(expNum):
    '''
    should check the passed exp num to see if complete_formulations == total_formulations before proceeding if =/= sleep for 5 mins?
    if sleeping print time of sleep start and duration to show its not crashed
    '''
    print("Checking Exp: " + expNum)
    # cj = s3cookiejar.S3CookieJar()
    # br = mechanize.Browser()
    # br.set_cookiejar(cj)
    # br.open("http://138.253.226.89/RobotRun")
    # br.select_form(nr=0)
    # br.form['UserName'] = 'livad\mif015'
    # br.form['Password'] = 'emsfl0w1'
    # br.form['CompanyId'] = ["1",] #1 labman, 2 UoL, 3 Unilever
    # br.submit()
    br = holly_login()

    print("Logging into HOLLY")

    br.open(holly_ip + "/Experiment/ViewExperiment/" + expNum)
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')

    divs = soup.find_all("div", class_= "col-md-8 divborder")
    '''strips webpage to classes
    divs[0] is exp details
    divs[1] is exp stats ---- this is the important one
    etc.
    '''
    exp_stats = str(divs[1]) # needs str else is nonetype
    exp_stats = exp_stats.splitlines()
    total_forms = exp_stats[2]
    total_forms = (total_forms.split("</b>"))[1]
    total_forms = (total_forms.split("<br/>"))[0]
    total_forms = total_forms.strip()

    comp_forms = exp_stats[3]
    comp_forms = (comp_forms.split("</b>"))[1]
    comp_forms = (comp_forms.split("<br/>"))[0]
    comp_forms = comp_forms.strip()

    if comp_forms == total_forms:
        print("Exp: " + expNum + " ready for processing")
        return True
    else:
        print("Exp: " + expNum + " not ready")
        return False

def holly_webscaper(expNum, path):
    print("Attempting scrape")

    # initialise the mat list stuff

    if material_name_switch:
        materials = pd.read_csv(path + "Material tracking/material_list.csv", delimiter=",")
        materials = materials.set_index("Material")




    # cj = s3cookiejar.S3CookieJar()
    # br = mechanize.Browser()
    #
    # br.set_handle_robots(False)  # no robots
    # br.set_handle_refresh(False)
    # br.addheaders = [('User-agent',
    #                   'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    # # [('User-agent', 'Firefox')]
    # br.set_cookiejar(cj)  # allow everything to be written to

    # #logs in to holly
    # br.open("http://138.253.226.89/RobotRun")
    # br.select_form(nr=0)
    # br.form['UserName'] = 'livad\mif015'
    # br.form['Password'] = 'emsfl0w1'
    # br.form['CompanyId'] = ["1",] #1 labman, 2 UoL, 3 Unilever
    # br.submit()
    br = holly_login()

    #print("Logging into HOLLY")

    #expNum = "665"
    #expNum = data
    #print("exp num:" + expNum)
    #br.follow_link("http://138.253.226.89/RobotRun/ViewRobotRun/"+robotRun)
    br.open(holly_ip + "/Experiment/ViewExperiment/"+expNum)
    #br._factory.is_html = True
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')
    #print(soup.prettify())
    # br.open("http://138.253.226.89/RobotRun")
    # br.select_form(nr=0)
    # print(br.form)


    #page = requests.get("http://138.253.226.89/RobotRun")


    #print(soup.find_all('tr'))
    # for tr in soup.find_all('tr'):
    #     tds = tr.find_all('td')
    # print(tds)

    divs = soup.find_all("div", class_="col-md-8 divborder")
    '''strips webpage to classes
    divs[0] is exp details - need for name for visual exp checking 
    divs[1] is exp stats 
    etc.
    '''

    exp_det = str(divs[0])  # needs str else is nonetype
    exp_det = exp_det.splitlines()
    exp_name = exp_det[3]
    exp_name = exp_name.split("</b>")[1]
    exp_name = exp_name.split("<br/>")[0]
    exp_name = exp_name.strip()




    table = soup.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="formulationsTable")
    rows = table.findAll(lambda tag: tag.name=='tr')


    formulationsDict = {}
    dispenseDict = {}
    print("Scraping Exp: {}".format(expNum))
    #finds all formulationIDs in exp and their status
    for row in rows[1:]:
        row = str(row)
        row = row.splitlines(True)

        form_id = row[2]
        form_id = form_id.split("<label>")
        form_id = form_id[1].split("</label>")
        form_id = form_id[0]

        form_name = row[5]
        form_name = form_name.split("<label>")
        form_name = form_name[1].split("</label>")
        form_name = form_name[0]

        form_status = row[14]
        if "Complete" in form_status:
            form_status = "Complete"
        if "Error" in form_status:
            form_status = "Error"
        if "Processing" in form_status:
            form_status = "Processing"

        formulationsDict.setdefault("form_id", []).append(form_id)
        formulationsDict.setdefault("form_name", []).append(form_name)
        formulationsDict.setdefault("form_status", []).append(form_status)

    formulation_df = pd.DataFrame.from_dict(data=formulationsDict)
    formulation_df.set_index('form_id', inplace=True)

    #goes through each formulation for dispense amounts

    #print("got form_ids, getting dispenses")
    form_list = []
    form_dict_list = []
    dispense_dict_list = []
    dictionary = {}
    end_dict_list=[]
    length = len(formulationsDict["form_id"])
    counter = 1
    mat1 = []
    mat2 = []
    ss_list = []

    '''
    Should give a list for normal materials and the subsample materials for use with collecting target amounts
    Stripped flow id from subsample list'''
    # if material_check_on:
    #     for i in range(8):
    #         i += 1
    #         for n in materials[('id{}').format(i)].dropna():
    #             #print(n)
    #             mat1.append(n)
    #         for index, row in materials.iterrows():
    #             if row["type"] == "subsampling":
    #                 # print(row[("id{}".format(i))])
    #                 ss1 = row[("id{}".format(i))].split(" - ")[0]
    #                 ss_list.append(ss1)
    #         # if not row["type"] == "Wash solution":
    #         #     if i == 1:
    #         #         mat1.append(row[("id{}".format(i))])


    if material_name_switch:
        for i in range(8):
            i += 1
            for n in materials[('id{}').format(i)].dropna():
                #print(n)
                mat1.append(n)
            # for index, row in materials.iterrows():
            #     if row["type"] == "subsampling":
            #         # print(row[("id{}".format(i))])
            #         ss1 = row[("id{}".format(i))].split(" - ")[0]
            #         ss_list.append(ss1)
            # # if not row["type"] == "Wash solution":
            # #     if i == 1:
            # #         mat1.append(row[("id{}".format(i))])



    # print(mat1, ss_list)
    for i in formulationsDict["form_id"]:
        while True:
            try:
                print("Processing: "+str(counter)+"/"+str(length))
                #bar.update(counter)
                #time.sleep(0.25)
                #bar.finish()
                br.open(holly_ip + "/Experiment/ViewFormulation/"+i)
                html = br.response().read()
                soup = BeautifulSoup(html, 'html.parser')
                #simplistic workaround as both tables on this page have the same ID
                table = soup.find_all('table')[1]
                #print(table)
                rows = table.findAll(lambda tag: tag.name == 'tr')
                material_list = []
                act_amount_list = []
                form_list.append(i)
                #dictionary.setdefault("form_id", []).append(i)
                #dispenseDict.setdefault("form_id", []).append(i)
                end_dict=[]
                for row in rows[1:]:
                    row = str(row)
                    row = row.splitlines(True)
                    instruc = row[2]
                    #print(row)
                    #print(instruc)
                    material = ""
                    act_amount = 0
                    take_act_amount = True
                    if "IngredientAddition" in instruc:
                        #print("correct")
                        material = row[16]
                        #print(material)
                        material = material.split("</td>")
                        material = material[0].strip()
                        #print(material)
                        act_amount_r = row[19] #before ss check
                        if ss_tar:
                            if material in ss_list:

                                # should be tar amount for ss samples and prevent ss tar amount becoming 0 from actual
                                #setting to row[17] gives the targetamount from before this was patched
                                #act_amount_r = row[17]
                                act_amount = act_amount_r.split("<td>")
                                act_amount = act_amount[1].split("</td>")
                                act_amount = act_amount[0]
                                material_list.append(material)
                                act_amount_list.append(float(act_amount))
                                take_act_amount = True


                        #if "good" in act_amount_r and take_act_amount: for handling ss?
                        if "good" in act_amount_r and take_act_amount:
                           # print(act_amount_r)
                            act_amount = act_amount_r.split('<td class="good">')
                            act_amount = act_amount[1].split("</td>")
                            act_amount = act_amount[0]
                            material_list.append(material)
                            act_amount_list.append(float(act_amount))
                            #print(material, act_amount)
                        if "bad" in act_amount_r and take_act_amount: #includes red OoT dispenses as optimiser can work with that
                           # print(act_amount_r)
                            act_amount = act_amount_r.split('<td class="bad">')
                            act_amount = act_amount[1].split("</td>")
                            act_amount = act_amount[0]
                            material_list.append(material)
                            act_amount_list.append(float(act_amount))
                            #print(material, act_amount)

                        # if "warning" in act_amount_r and take_act_amount:
                        #     act_amount = act_amount_r.split('<td class="warning">')
                        #     act_amount = act_amount[1].split("</td>")
                        #     act_amount = act_amount[0]
                        #     material_list.append(material)
                        #     act_amount_list.append(float(act_amount))


                counter += 1
                break
            except Exception as e:
                print(e)
                print("Retrying in 5s")
                time.sleep(5)
                continue


        '''
        need to convert material list to optimiser materials
        materials,df of ids for opt -> exp
        mat1, list of ids to re-add formid to mat name before exp -> opt
        material_list, webscraped mat names from holly, needs formid adding
        mat2, completed list of material + formid
        mat3, uses mat2 to find index name from materials for final exp -> opt step
        '''

        mat2=[]
        for j in material_list:
            for x in mat1:
                if j in x:
                    for b in range(8):
                        b += 1

                        # print(materials[materials[("id{}").format(b)]==x].index.values)
                        # mat = materials[materials[("id{}").format(b)]==x].index.
                        mat2.extend(materials.index[materials[("id{}").format(b)]==x])
                        #print(materials.index[materials[("id{}").format(b)]==x].tolist())

                        break
                    break
        # print(mat1)
        # print(mat2)
        # print(material_list)
        #
        #
        # print(material_list)
        # print(mat2)



        dispense_dict = dict(zip(mat2, act_amount_list))
        #print(act_amount_list)
        #print(dispense_dict)
        '''packs the dispense data for easier unloading into dataframe'''

        #dispense_dict = [dispense_dict]

                #amountList.append(act_amount)
                #dispenseDict.setdefault("form_id", []).append(i)
                #materialList =
                #dispenseDict = {i: {material: act_amount}}
                #dispenseDict.setdefault(i, []).append(material)
                #dispenseDict.setdefault(i, []).append(act_amount)


        #dispenseDict.setdefault("dispenses", []).append(dispense_dict)
        #dispenseDict.setdefault("form_id", i).setdefault("dispenses", []).append(dispense_dict)

    # for id in form_list:
    #     form_dict = {"form_id" : id}
    #     form_dict_list.append(form_dict)



        end_dict = {i:dispense_dict}
        end_dict_list.append(end_dict)
        #print(end_dict_list)
        #bar.finish()

    #print(end_dict)

        #https: // www.geeksforgeeks.org / python - convert - list - of - nested - dictionary - into - pandas - dataframe /

        #dict = [{"form_id":1, "dispsenses":[{"cat":0.005, "water": 5}, {"cat":0.005, "water":5}]}]

        #dispenseList.append(dispenseDict)





    #dispenses_df = pd.concat({k: pd.DataFrame(v) for k, v in dispenseDict.items()}, axis=0)

    #pd.DataFrame(dispenseDict)

    # rows list initialization
    rows = []
    # appending rows
    #print(dispenseList)

    '''takes the end dictionary list of mat names and dispense amounts and puts into df with form id as index'''
    for data in end_dict_list:
        for i in data:
            id = i
        #time = data["form_id"]
        data_row = data.values()
        #print(data_row)

        for row in data_row:
            row["form_id"] = id
            rows.append(row)

        # using data frame
    dispenses_df = pd.DataFrame(rows)
    dispenses_df.set_index("form_id", inplace=True)


    '''
    Check headers against ss_list and materials
    reformat headers from flow to bayes names
    total subsample rows and delete dupes
    
    
    gets flow names from dispense_df
    check to see if string in mat1, if yes, replaces with flow name + id
    checks flow name + id with materials df to get index (bayes name) for id1, replaces if exists
    if doesn't not exist checks against id1-8 for subsample
    
    
    TODO: 
    convert col1 from list to string, 
    reformat headers, add together the ss
    '''

    # print(materials)
    #print(mat1)
    # print(ss_list)
    #print(materials["id1"])
    if material_check_on:
        for col in dispenses_df.columns:
            for x in mat1:
                if col in x:
                    col2 = x
            col1 = (materials.index[materials["id1"] == col2].tolist())
            if col1:
                dispenses_df.rename(columns={col: col1.pop()}, inplace=True)
            if not col1:
                for n in range(7):
                    col_ss = (materials.index[materials[("id{}").format(n+2)] == col2].tolist())
                    if col_ss:
                        s_col_ss = col_ss.pop()
                        # print(s_col_ss)
                        # print(col)

                        dispenses_df[s_col_ss] = dispenses_df[s_col_ss].fillna(0)+dispenses_df[col].fillna(0)
                        dispenses_df.drop(columns=col, inplace=True)
                        #print(dispenses_df[col])
                        break
    #print(dispenses_df)



    '''
    find all solid dispensed materials
    x1000 to give in mg
    code below works but opt works in g not mg
    '''

    #print(dispenses_df.columns.values.tolist())
    #print(materials)
    if convert_solid_g2mg:
        for i in dispenses_df.columns.values.tolist():
            #print(materials._get_value(i, "type"))
            if materials._get_value(i, "type") == "solid":
                dispenses_df[i] = dispenses_df[i]*1000


        '''
        Validation of dispense amounts
        Tally up the ss and liquid dispenses, delete entry if =! 5
        Check solid dispense, remove if not between 0-15mg range - should probably pull this from opt config to not hardcode limit
        '''
        index_to_remove = []

        for index, row in dispenses_df.fillna(0).iterrows():
            total = 0
            for i in row.index:
                if materials._get_value(i, "type") == "subsampling" or materials._get_value(i, "type") == "liquid":
                    #print(row[i])
                    total = total + row[i]

                if materials._get_value(i, "type") == "solid":
                    if row[i] < 0 or row[i] > 15:
                        index_to_remove.append(index)

            if not total == 5:
                index_to_remove.append(index)


    if validation_on:
            #print(index)
        if not len(index_to_remove) == 0:
            print(("Trimming {} sample/s that do not meet validation rules: {}").format(len(index_to_remove), index_to_remove))
            dispenses_df = dispenses_df.drop(index_to_remove)

    #print(dispenses_df)







    #print(dispenses_df)
    # print(df)

     # dispenses_df = pd.DataFrame.from_dict({(i): dispenseDict[i]
     #                            for i in dispenseDict.keys()
     #                            for j in dispenseDict[i]},
     #                        orient='index')

    #dispenses_df = pd.DataFrame.from_dict(data=dispenseDict)
    #dispenses_df = dispenses_df.transpose()



    #print(dispenses_df)

    #formulation_dispenses_df= formulation_df.merge(dispenses_df, left_on="form_id")
    #print("here")
    formulation_dispenses_df = pd.concat([formulation_df, dispenses_df], axis=1, sort=True, join="inner")
    #formulation_dispenses_df.set_index("form_id", inplace=True)
    #print(formulation_dispenses_df)
    print("Scraping complete")


    return formulation_dispenses_df, exp_name

def get_current_robot_run():
    br = holly_login()
    br.open(holly_ip + "/RobotRun")
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    rows = table.find_all(lambda tag: tag.name == 'tr')
    #print(rows)

    for row in rows[1:]:
        #print(row)
        row = str(row)
        row = row.splitlines(True)
        try:
            # name=row[8]
            # name = name.split("<td>")[1]
            # name = name.split("</td>")[0]
            id=row[2]
            id = id.split("<label>")[1]
            id = id.split("</label>")[0]
            progress=row[6]
            progress = progress.split("<td>")[1]
            progress = progress.split("</td>")[0]
        except: print("Problem with: " + id + progress)

        if progress == "Running":
            #print(id+" " +progress)
            return id

    print("No robot runs started")
    exit()

def get_text_run(run_id=None):
    br = holly_login()
    br.open((holly_ip + "/RobotRun/AddExperimentToExistingRun/{}").format(run_id))

    br.select_form(nr=0)
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all("div", class_="col-md-8 divborder")
    '''strips webpage to classes
    divs[0] is exp details - need for name for visual exp checking 
    divs[1] is exp stats 
    etc.
    '''
    risk_txt = ""
    check_txt = ""

    raf_div = str(divs[3])
    raf_div = raf_div.splitlines()
    for i in raf_div:
        if "</textarea>" in i:
            if risk_txt == "":
                risk_txt = i.split("</textarea>")[0]
                continue
            if check_txt  == "":
                check_txt = i.split("</textarea>")[0]
                break

    print(risk_txt)
    print(check_txt)

    return risk_txt, check_txt




# def exp_to_run_sel(batch_id):
#     '''Add this to the end of upload when working, no need for this to be seperate'''
#
#     run_id = get_current_robot_run()
#
#
#
#     edge_options = Options()
#     edge_options.add_experimental_option("detach", True)
#     driver = webdriver.Edge(options = edge_options)
#     driver.get(("http://138.253.226.89/RobotRun/AddExperimentToExistingRun/{}").format(run_id))
#     un_field = driver.find_element(By.NAME, "UserName")
#     pw_field = driver.find_element(By.NAME, "Password")
#     silo_lb_e = driver.find_element(By.ID, "CompanyId")
#     silo_lb_o = Select(silo_lb_e)
#
#     un_field.send_keys("livad\mif015")
#     pw_field.send_keys("emsfl0w1")
#     silo_lb_o.select_by_index(1)
#
#     login_btn = driver.find_element(By.XPATH, "//input[@type='submit'][@value='Log In']")
#     login_btn.click()
#
#     # Select exp, fill fields and upload
#     driver.implicitly_wait(1000)
#
#
#     '''
#     pull text from fields for checking
#     done through mechanize as its better for this'''
#
#
#     risk_txt, check_txt = get_text_run(run_id)
#     risk_update = ''
#     check_update = ''
#
#     raf_ele = driver.find_element(By.NAME, "RiskAssessmentRef")
#     check_ele = driver.find_element(By.NAME, "CheckedBy")
#
#     if not "See COSHH on Bay B" in risk_txt:
#         risk_update = ("\n --------\n See COSHH on Bay B")
#
#     if not "JCG" in check_txt:
#         check_update = (" / JCG")
#
#     raf_ele.send_keys(risk_update)
#     check_ele.send_keys(check_update)
#
#
#
#     new_exp_lb_e = driver.find_element(By.ID, "NewExperimentId")
#     new_exp_lb_o = Select(new_exp_lb_e)
#     #Value seems to be exp num, need to record this when uploading
#     new_exp_lb_o.select_by_value(batch_id)
#
#
#
#
#
#
#
#
#
# def upload_exp_sel(expNam=None):
#
#     '''TODO: Add BATCH ID'''
#
#     pre_dir = os.getcwd()
#
#     for i in range(2):
#         path_parent = os.path.dirname(os.getcwd())
#         os.chdir(path_parent)
#
#     '''PULLED FROM MAIN for file-handling test
#     Need to pass directory through when calling in operation?
#     initialises dir then resets to the correct path for driver
#     '''
#     pro_soft_dir = os.getcwd()
#     optimiser_dir = pro_soft_dir + "/Bayesian Optimiser/fe_optimizer-master/Optimizer/runqueue/"
#     if expNam == None:
#         # for debugging
#         file = "carbonnitride-optimiser-fe-0088.xlsx"
#         current_file = optimiser_dir + file
#     else: current_file = expNam
#
#
#     os.chdir(pre_dir)
#
#
#
#
#     # intialise and log in
#     edge_options = Options()
#     edge_options.add_experimental_option("detach", True)
#     driver = webdriver.Edge(options = edge_options)
#     driver.get("http://138.253.226.89/Session/Login?returnUrl=%2FExperiment%2FUploadExperimentInputFile%2FTrue")
#     un_field = driver.find_element(By.NAME, "UserName")
#     pw_field = driver.find_element(By.NAME, "Password")
#     silo_lb_e = driver.find_element(By.ID, "CompanyId")
#     silo_lb_o = Select(silo_lb_e)
#
#     un_field.send_keys("livad\mif015")
#     pw_field.send_keys("emsfl0w1")
#     silo_lb_o.select_by_index(1)
#
#     login_btn = driver.find_element(By.XPATH, "//input[@type='submit'][@value='Log In']")
#     login_btn.click()
#
#     # Select exp, fill fields and upload
#     driver.implicitly_wait(1000)
#     file_btn = driver.find_element(By.NAME, "inputfile")
#     file_btn.send_keys(current_file)
#      # time seems to be ms, need next page to load before continuing
#     risk_tfield = driver.find_element(By.NAME, "RiskAssessmentRef")
#     checked_tfield = driver.find_element(By.NAME, "CheckedBy")
#
#     risk_tfield.clear()
#     risk_tfield.send_keys("See COSHH on Bay B")
#     checked_tfield.clear()
#     checked_tfield.send_keys("JCG-Auto")
#
#     driver.implicitly_wait(5000)
#     #upload_btn = driver.find_element(By.XPATH, "//input[@type='submit']")
#
#     upload_btn = driver.find_element(By.XPATH, "//*[@id='pagelayout_body']/form/div[3]/button")
#     #pload_btn = driver.find_element(By.CSS_SELECTOR, ".btn btn-primary btn-large").
#     # cant seem to click the upload button to get the error pop up?
#     print("?")
#     upload_btn.click()










    #upload_btn.submit()

def upload_exp(inputFile=None, run=None):
    br = holly_login()

    br.open(holly_ip+ "/Experiment/UploadExperimentInputFile/True")
    #br._factory.is_html = True
    #html = br.response().read()
    #soup = BeautifulSoup(html, 'html.parser')
    count = 0
    i = 0
    # for form in br.forms():
    #
    #     print(form.name)
    #     print(i)

    # for control in br.form.style:
    #     print(control)
    #     print(control.type)
    #     print(control.name)
    #     print(i)
       # i += 1
    #     # if "FileControl" in br.form:
    #     #     f = br.form
    #     #     break
    # br.select_form()
    # print(f)
    # exit()
    #x = "sample 1p only.xlsx"
    #r = "C:/Users/jackh/OneDrive - The University of Liverpool/PhD/Project Results Storage/Project Software/Bayesian Optimiser/fe_optimizer-master/Optimizer/runqueue/"
     #f = read(r + x, encoding="utf-8")
    br.select_form(nr=0)

    filename = inputFile.split("\\")[-1]


    #print(br.form)
    #br.form["inputfile"]
    #print(br.form)
    # #br.add_file(f, name="inputfile", filename=x)
    #filename = "C:/Users/jackh/OneDrive - The University of Liverpool/PhD/Project Results Storage/Project Software/Bayesian Optimiser/fe_optimizer-master/Optimizer/runqueue/{}".format(x)
    #data = pd.read_excel(filename)
    #br.select_form(name = "inputfile")
    print("Adding exp: {}".format(filename))

    f = open(inputFile, "rb")

    br.form.add_file(f, content_type="file", filename=filename)

    # #mechanize.FileControl.add_file()
    #
    # #br.form.add_file(f, name="inputfile", filename=x)
    #
    # html = br.response().read()
    # soup = BeautifulSoup(html, 'html.parser')
    #
    br.form['RiskAssessmentRef'] = 'See COSHH on Bay B'
    br.form['CheckedBy'] = 'JCG'



    print("Submitting exp")
    br.submit()
    print("Submitted!")

    f.close()
    time.sleep(10)
    add_exp_to_run(br, run)

    br.close()



def add_exp_to_run(br, run_id):
    #br = holly_login()

    #br.open(holly_ip + "/Experiment/ViewExperiment/1430")

    url = str(br.geturl()).split("ViewExperiment/")
    #print(url)
    exp_id = url[1]
    if run_id == None:
        run_id = get_current_robot_run()

    br.open(holly_ip + "/RobotRun/AddExperimentToExistingRun/" + run_id)
    #
    # for form in br.forms():
    #     print(form)

    #control = br.form.find_control("SelectControl")
    br.select_form(nr=0)

    print("Adding: {a} to Run: {b}".format(a=exp_id, b=run_id))
    br.form['NewExperimentId'] = [exp_id, ]
    #br.form['UserName'] = 'livad\mif015'

    br.submit()

    #print(ExpId)

#def find_current_fun():

#add_exp_to_run()

