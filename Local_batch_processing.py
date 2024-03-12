import holly_webscraper
import batch_processor
import os
from os.path import isfile, join
import shutil
import pandas as pd
from tkinter import filedialog




'''TODO: 
Get this working
'''













for i in range(2):
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)

pro_soft_dir = os.getcwd()

template_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Excel Results (Processed)/Template/" \
               "files/"

output_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Excel Results (Processed)/"
#default_batch_loc = pro_soft_dir + "/Hiden Output/Processed"
unprocessed_batch_dir = pro_soft_dir + "/Hiden Output/Unprocessed"
processed_batch_dir = pro_soft_dir + "/Hiden Output/Processed"
optimiser_dir = pro_soft_dir + "/Bayesian Optimiser/fe_optimizer-master/Optimizer/"
optimiser_dir_comp = optimiser_dir + "completed/" # should help simplify changing comp folders when debugging

view_dump = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/View Dump/"

template_filename = "RESULTS TEMPLATE"
filetype = ".csv"


'''inherent to current catalyst, infrequent changes '''
illu_time = 4 # Illumination time in hours

'''inherent to all sampling, no changes expected'''
every_nth_file = 6  # Which nth file is the one to process
# 4th is default from 2 cup 2 from sample samples

'''hiden relative sensitivity values'''
if every_nth_file == 6:
    rs_dict = {
        "mass 2.00": ["H2", 1.75],
        "mass 28.00": ["N2", 1.00],
        "mass 32.00": ["O2", 0.71475],
        "mass 40.00": ["Ar", 1.21],
        "mass 44.00": ["CO2", 1.4]
    }
if every_nth_file == 7:
    rs_dict = {
        "mass 2.00": ["H2", 1.853],
        "mass 28.00": ["N2", 1.00],
        "mass 32.00": ["O2", 0.7275],
        "mass 40.00": ["Ar", 1.21],
        "mass 44.00": ["CO2", 1.4]
    }

'''values for calc from hiden values'''
headspace_volume = 6.64  # (mL) Correct with more accurate value when possible
pressure = 1  # (bar)
ideal_gas_cons = 0.083145  # (L*bar / K*mol)
temperature = 293  # (K)
molar_vol_gas = (pressure)/(ideal_gas_cons*temperature) # ~24.36


'''
material amount params
should match params in fe_parser
'''
liquid_limit = 1000
wash_limit = 3000
liquid_ds = 0.05
subsample_ds= 0.1

'''param lists for modules
bp: batch processor
hws: holly webscraper'''
bp_params = [template_dir, output_dir, unprocessed_batch_dir, template_filename, filetype, every_nth_file, illu_time, molar_vol_gas, headspace_volume, rs_dict]



def batch_processing(dirname):
    # app.update_frame(cont=StartMenu, data_type="label_update", data=dirname)
    #''' Cont = desired page, inputType= will be label, listbox, etc; input= filename/dir'''

    try:
        dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]
        dirname = os.path.normpath(dirname)
        batch_id = (dirname.split("\\"))[-1]
        print("Processing: {}".format(batch_id))

        r_list = dir_contents, dirname, batch_id
        # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
        check = holly_webscraper.holly_complete_check(batch_id)
        processed_output_df = batch_processor.batch_processor(bp_params, r_list)
        processed_output_df.sort_index(axis=0, inplace=True)

       # starts catch loop as web scraping most likely to give errors
        while check:
            try:
                #batch_id -> expNum
                dispense_df, exp_name = holly_webscraper.holly_webscaper(batch_id, optimiser_dir)
                collated_df = pd.concat([dispense_df, processed_output_df], axis=1)
                collated_df.reindex()
                collated_df.fillna(0, inplace=True)
                #post batch file handling - moves unprocessed hiden csv to processed folder
                collated_df.to_excel(optimiser_dir_comp+"{}.xlsx".format(batch_id + (" - {}".format(exp_name))), sheet_name="Output")
                print("File collated and dumped")
                #shutil.move(dirname, processed_batch_dir + "\\" + str(batch_id))

                break
            except Exception as e:
                print(e)
                while True:
                    print("Scraping Error - try again? Y/N")
                    x = input().upper().strip()
                    if x =="Y" or x == "N":
                        break
                    else:
                        print("Invalid response")
                if x == "Y":
                    continue
                if x =="N":
                    print("Process stopped")
                    break
    except:
        print("Closing process")

def select_batch_processing():

    dirname = filedialog.askdirectory(initialdir=unprocessed_batch_dir, title="Select batch to process")

    batch_processing(dirname)

select_batch_processing()
