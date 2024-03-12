import datetime
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import os
from os.path import isfile, join
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import xlwings as xw
import batch_processor
import glob
import shutil
import holly_webscraper
from natsort import natsorted
import time
from threading import Thread
import numpy as np
from tkinter import messagebox
import easygui
import platform
import multiprocessing
import pickle
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import HTTPError, Request


'''
Author: Jack C. Gee


'''
#########################################################
'''
PARAMETERS
'''

'''finds current working dir and goes up 2 to cover the bayes op'''

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
data_pro_dir = pro_soft_dir + "/Formulation Engine Data Processing/Data Processor/"
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
molar_vol_gas = (pressure)/(ideal_gas_cons*temperature) # ~24.36 mol/L


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

event = threading.Event()

#os.add_dll_directory("C://Users/jackh/OneDrive - The University of Liverpool/PhD/Project Results Storage/Project Software/Formulation Engine Data Processing/Data Processor/venv2/Lib")

#########################################################

class listen_thread(Thread):
    global event
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

        self.running = True

        #app.show_frame(AutoPopUp)


    def run(self):
        # for i in glob.glob(optimiser_dir + "runqueue/*"):
        #     print(i)
        #exit()

        print("Automation start")




        while self.running:
            label_update()
            if not event.is_set():
                print("Automation ended")
                break
            runninglen = len(glob.glob(optimiser_dir + "running/*"))
            if runninglen > 1:
                #check output for processing
                print("Checking for completed experiments in /Unprocessed/")
                dirlist = list(glob.glob(unprocessed_batch_dir + "/*"))
                run_opt_flag = False
                #print(dirlist)
                try:
                    for i in dirlist:
                        #print(i)
                        holder = i.split("\\")[-1]
                        #print(holder)
                        batch_id = holder.split(" - ")[0]
                        #print(batch_id)
                        #exp_nam = holder.split(" - ")[1]
                        #print(exp_nam)
                        try:
                            if holly_webscraper.holly_complete_check(batch_id):
                                #no need to check again so skip that
                                exp_name = batch_processing(i, check_flag = False)

                                #once processed and dumped, move old exp to archive
                                archive_exp(exp_name)
                                run_opt_flag = True
                                #threading.main_thread(update_graph())
                                #time.sleep(5)
                                #run_bayes_op()
                            else:
                                continue
                        except Exception as e:
                            print(e)
                except:  # catches no files in dir
                    #print("issue")
                    pass
                if run_opt_flag == False:
                    print("No valid files found - Waiting 30 mins from " + datetime.datetime.now().strftime('%H:%M:%S'))
                    time.sleep(1800)

            elif len(glob.glob(optimiser_dir + "runqueue/*")) > 0:
                pre_f = ""
                for f in glob.glob(optimiser_dir + "runqueue/*"):
                    if pre_f == "" or pre_f  != f:
                        pre_f = f
                        holly_webscraper.upload_exp(f)
                        holder = f.split("\\")[-1]

                        time.sleep(10)
                        #shutil.
                        print("Moving file: " + holder + " to /running/")
                        shutil.move(f, (optimiser_dir + "running/" + holder))
                        try:
                            pass
                            #email_update(holder)
                        except:
                            print("email sign-in")


            else:
                print("Not enough files running and none in queue -> running optimiser")
                run_bayes_op()





    # def run(self):
    #     global unprocessed_batch_dir
    #     print("Starting listening thread")
    #     while self.running:









class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        master.title("FE Processing")
        #master.geometry("1920x1080")
        master.protocol("WM_DELETE_WINDOW", on_closing)

        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry("%dx%d" % (width, height))



        self.pack()
        container = tk.Frame(master)
        '''
        Builds a TK frame from master, container is the contents of the window (frame), master is the whole application.
        '''
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Make frames to display pages
        self.frames = {}
        #for F in (StartMenu, ExcelView, Output):
        '''blanks 1 and 2 will allow for additional windows if desired in future'''
        for F in (StartMenu, blank1, blank2):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartMenu)

    # Raises desired frame to top
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    # def update_frame(self, cont, data_type, data=None):
    #     frame = self.frames[cont]
    #     if data_type == "listbox_option_update":
    #         frame.excelview_listbox_options_update(data)
    #     if data_type == "listbox_selected_update":
    #         frame.excelview_listbox_selected_update(data)
    #     if data_type == "return_parameters":
    #         r_list = frame.excelview_return_parameters()
    #         return r_list
    #     if data_type == "data_processing":
    #         frame.output_update(data)
    #     if data_type == "update_graph":
    #         frame.output_update_graphs()
    #     if data_type == "update_dropboxes":
    #         frame.output_update_dropboxes(data)
    #     if data_type == "label_update":
    #         frame.label_update(data)

    def update_frame(self, cont, data=None, arg=None):
        '''Call this if you want to update a frame within the app
        app.updateframe(cont=example_frame, arg = 1) would run label_update() '''

        frame = self.frames[cont]
        # frame_switcher = {
        #     1: frame.label_update,
        #     2: frame.mat_list_update,
        #     3: frame.mat_list_reset
        # }
        if arg == 1:
            frame.label_update()
        if arg == 2:
            frame.mat_list_update()
        if arg == 3:
            frame.mat_list_reset()
        if arg == 4:
            frame.graph_update()
        #frame_switcher.get(arg, lambda: "invalid request")




class AutoPopup:
    def __init__(self):
        #self.tl = tk.Toplevel()
        self.root = tk.Toplevel()
        self.root.title("Running Auto")
        self.lock()

        tk.Label(self.root, text="Automation Running").pack(padx=12, pady=12)
        #tk.Button(self.root, text="Popup!", width=20, command=self.popup).pack(padx=12, pady=12)
        tk.Button(self.root, text="Stop", width=20, command=self.exit_popup).pack(padx=12, pady=12)


        t1 = listen_thread()
        t1.start()

        self.root.mainloop()





    def exit_popup(self):
        listening_thread(False)
        self.unlock()
        print("Automation Stopped")
        self.root.destroy()
    # def popup(self):
    #     if self.tl is None:
    #
    #         tk.Button(self.tl, text="Grab set", width=20, command=self.lock).pack(padx=12, pady=12)
    #         tk.Button(self.tl, text="Grab release", width=20, command=self.unlock).pack(padx=12, pady=12)

    def lock(self):
        (self.root.grab_set())
        print("Locked")

    def unlock(self):
        self.root.grab_release()
        print("Unlocked")

class blank1(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

class blank2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)





class StartMenu(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.startmenu_label_vars()
        self.startmenu_create_widgets()
        self.graph_init()
        self.mat_list_init()
        self.pack()
    def startmenu_label_vars(self):
        self.queue_var = tk.StringVar()
        self.running_var = tk.StringVar()
        self.unprocessed_var = tk.StringVar()
        self.completed_var = tk.StringVar()

        self.label_update()
        self.material_list_update()


    def label_update(self):
        self.queue_var.set(str(len(glob.glob(optimiser_dir + "runqueue/*"))) + " batches in queue")
        self.running_var.set(str(len(glob.glob(optimiser_dir + "running/*")))+ " batches running")
        self.unprocessed_var.set(str(len(glob.glob(unprocessed_batch_dir + "/*")))+ " batches for processing")
        self.completed_var.set(str(len(glob.glob(optimiser_dir_comp + "*")))+ " batches completed")

    def material_list_update(self):
        pass



    def startmenu_create_widgets(self):
        #self.button_frame = tk.Frame(self)
        self.start_menu_frame = tk.LabelFrame(self, text="Select an option", height=500, width=500)
        self.material_list_frame = tk.LabelFrame(self, text="Material amounts", height=500, width=300)
        self.plot_frame = tk.LabelFrame(self, text="Graphics", height=800, width=600)

        #self.button_frame.grid()
        self.start_menu_frame.grid(padx=20, pady=20, row=0, column=0)
        self.material_list_frame.grid(padx=20, pady=20, row=0, column=1)
        self.plot_frame.grid(padx=20, pady=20, row=0, column=2)

        self.start_menu_frame.grid_propagate(0)
        self.material_list_frame.grid_propagate(0)
        #self.plot_frame.grid_propagate(0)
        # labels
        batch_gen_label = tk.Label(self.start_menu_frame, text="Batch Generator")
        batch_upload_label = tk.Label(self.start_menu_frame, text="Batch Uploading")
        batch_process_label = tk.Label(self.start_menu_frame, text="Batch Processing")
        result_view = tk.Label(self.start_menu_frame, text="Result Viewer")

        # pad labels

        col0_pad = tk.Label(self.start_menu_frame, text="")
        col1_pad = tk.Label(self.start_menu_frame, text="")
        col2_pad = tk.Label(self.start_menu_frame, text="")
        col3_pad = tk.Label(self.start_menu_frame, text="")
        col4_pad = tk.Label(self.start_menu_frame, text="")

        row0_pad = tk.Label(self.start_menu_frame, text="")
        row1_pad = tk.Label(self.start_menu_frame, text="")
        row2_pad = tk.Label(self.start_menu_frame, text="")

        # var labels
        queue_label_var = tk.Label(self.start_menu_frame, textvariable=self.queue_var)
        running_label_var = tk.Label(self.start_menu_frame, textvariable=self.running_var)
        unprocessed_label_var = tk.Label(self.start_menu_frame, textvariable=self.unprocessed_var)
        complete_label_var = tk.Label(self.start_menu_frame, textvariable=self.completed_var)

        #buttons
        #resultview_button = ttk.Button(self.button_frame, text="Results", command=button_temp)
        #matview_button = ttk.Button(self.button_frame, text="Material list", command=button_temp)

        #new_batch_button = ttk.Button(self.start_menu_frame, text="New batch(es)", command=lambda: run_bayes_op(new_batch_tbox.get()))
        new_batch_button = ttk.Button(self.start_menu_frame,text="New batch", command=run_bayes_op)
        register_button = ttk.Button(self.start_menu_frame, text="Hiden process only", command=hiden_process_only)
        ###
        process_select_button = ttk.Button(self.start_menu_frame, text="Process select", command=select_batch_processing)
        process_all_button = ttk.Button(self.start_menu_frame, text="Process all", command=all_batch_processing)
        process_select_forced_button = ttk.Button(self.start_menu_frame, text="Process forced select", command=select_batch_processing_forced)
        dispense_only_button = ttk.Button(self.start_menu_frame, text="Dispense only", command=just_dispenses)
        #view_select_button = ttk.Button(self.start_menu_frame, text="View select", command=button_temp)
        ####
        upload_exp_btn = ttk.Button(self.start_menu_frame, text="Upload Exp", command=upload_exp)
        upload_exp_pickexp_btn  = ttk.Button(self.start_menu_frame, text="PickExp", command=upload_exp_pickexp)
        upload_exp_pickexp_run_btn = ttk.Button(self.start_menu_frame, text="PickRun", command=upload_exp_pickexp_pickrun)
        ####
        email_button = ttk.Button(self.start_menu_frame, text="View all", command=view_all_csv)

        open_hiden_button = ttk.Button(self.start_menu_frame, text="Open Hiden File",
                                         command=button_temp)
        open_process_button = ttk.Button(self.start_menu_frame, text="Open Process File", command=open_b_processing_file)
        open_comp_button = ttk.Button(self.start_menu_frame, text="Open Comp File", command=open_comp_file)
        start_auto_button = ttk.Button(self.start_menu_frame, text="Auto", command=listening_thread)





        update_graph_button = ttk.Button(self.start_menu_frame, text="Update graph", command=update_graph)
        reset_graph_button = ttk.Button(self.start_menu_frame, text="Update graph", command=update_graph)
        component_graph_button = ttk.Button(self.start_menu_frame, text="Show component graph", command=graph_of_components)


        '''ddown config'''
        options = ["index",
                   "calc_%_H2_umol",
                   "10_Pt/TiO2",
                   "11_PCN",
                   "12_Pt/CdS",
                   "13_Pt/WO3",
         "20_Xylose-0.25M", "21_Proline","22_Cysteine","23_Glucose","24_Cellobiose",
         "30_NaOH-0.5M", "31_CitricAcid-0.5M", "32_AcidYellow73","33_AcidViolet43",
         "34_AcidGreen1",
         "calc_%_O2_umol", "calc_%_CO2_umol"]

        self.x_var_ddown = tk.StringVar(self.start_menu_frame)
        self.x_var_ddown.set(options[0])
        self.y_var_ddown = tk.StringVar(self.start_menu_frame)
        self.y_var_ddown.set(options[1])


        x_axis_ddown = tk.OptionMenu(self.start_menu_frame, self.x_var_ddown, *options)
        y_axis_ddown = tk.OptionMenu(self.start_menu_frame, self.y_var_ddown, *options)

        #text box
        #new_batch_tbox = tk.Entry(self.start_menu_frame, width=2)

        #packing
        col0_pad.grid(row=1,column=0,padx=20)
        col1_pad.grid(row=1,column=1,padx=20)
        col2_pad.grid(row=1,column=2,padx=20)
        col3_pad.grid(row=1,column=3,padx=20)
        col4_pad.grid(row=1,column=4,padx=20)

        row0_pad.grid(row=6,column=0,pady=5)
        row1_pad.grid(row=10,column=0,pady=5)

        batch_gen_label.grid(row=1, column=0, columnspan=2, sticky="")
        #resultview_button.grid(row=1, column=4, rowspan=1,  sticky="")
        #matview_button.grid(row=1, column=4, rowspan=1, sticky="")
        #new_batch_tbox.grid(row=2, column=1, rowspan=1, sticky="w", padx=20)
        new_batch_button.grid(row=2, column=0, columnspan=2, sticky="")
        start_auto_button.grid(row=2, column=4, columnspan=2, sticky="")
        register_button.grid(row=3, column=0, columnspan=2, sticky="")
        queue_label_var.grid(row=4, column=1, rowspan=1, sticky="w")
        running_label_var.grid(row=5, column=1, rowspan=1,  sticky="w")

        batch_upload_label.grid(row=6, column =0, columnspan=2, sticky="")
        upload_exp_btn.grid(row=7, column=1, rowspan=1,  sticky="w")
        upload_exp_pickexp_btn.grid(row=7, column=2, rowspan=1,  sticky="w")
        upload_exp_pickexp_run_btn.grid(row=7, column=3, rowspan=1,  sticky="w")

        batch_process_label.grid(row=8, column=0, columnspan=2, sticky="")

        process_select_button.grid(row=9, column=1, rowspan=1,  sticky="w")
        process_all_button.grid(row=9, column=2, rowspan=1,  sticky="w")
        dispense_only_button.grid(row=9, column=3, rowspan=1,  sticky="w")
        open_process_button.grid(row=9, column=4, rowspan=1,  sticky="w")

        process_select_forced_button.grid(row=9, column=1, rowspan=1, sticky="w")

        unprocessed_label_var.grid(row=10, column=0, columnspan=2,  sticky="")
        result_view.grid(row=11, column=1, rowspan=1,  sticky="w")
        #view_select_button.grid(row=12, column=1, rowspan=1,  sticky="w")
        email_button.grid(row=12, column=1, rowspan=1,  sticky="w")
        open_comp_button.grid(row=12, column=2, rowspan=1,  sticky="w")
        complete_label_var.grid(row=15, column=1, rowspan=1, sticky="w")

        x_axis_ddown.grid(row=13, column=1, rowspan=1, sticky="w")
        y_axis_ddown.grid(row=13, column=2, rowspan=1, sticky="w")
        update_graph_button.grid(row=14, column=1, rowspan=1, sticky="w")
        component_graph_button.grid(row=14, column=2, rowspan=1, sticky="w")

        ## read and set label vars

    def graph_init(self):
        #sns.set()
        try:
            init_fig = (self.graph_create_default())
            if init_fig == None:
                return
            self.canvas = FigureCanvasTkAgg(init_fig, master=self.plot_frame)
            self.canvas.draw()
            #canvas.get_tk_widget().pack(tk.TOP, fill=tk.BOTH, expand=1)
            self.canvas.get_tk_widget().grid()
            return self.canvas
        except:
            print("no data for graph")

    def graph_create_test(self):

        sns.set_theme(style="whitegrid")
        df = graph_data()
        figure, ax = plt.subplots(figsize=(6.5, 6.5))
        sns.despine(figure, left=True, bottom=True)
        x = df["form_name"]

        y = df["calc_%_H2_umol"]
        sns.scatterplot(x=x,y=y, ax=ax)

        # df1 = df.drop(df[df["Type"] == "Control"].index)  # samples only
        # df2 = df.drop(df[df["Type"] == "Sample"].index)  # controls only

        # ax = sns.scatterplot(data=df, x="index", y="calc_%_H2_umol", hue="calc_%_H2_umol", palette="ch:r=-0.5,l=0.8",
        #                      edgecolor="none")  # id by h2 umol
        # sns.scatterplot(data=df2, x="index", y="calc_%_H2_umol",palette="ch:r=-0.5,l=0.8", facecolor="black", edgecolor="none", marker="X")  # Controls
        # ax.legend([], [], frameon=False)
        # ax.set_ylabel("Dispense (mg / mL)")
        # ax.set_xlabel("ID")
        # # plt.show()
        # sns.scatterplot( data = data["calc_%_H2_umol"],ax=ax)

        return figure




    def graph_create_default(self):
        # # generate some data
        # matrix = np.random.randint(20, size=(10, 10))
        sns.set_theme(style="whitegrid")
        data = []
        df = graph_data()
        # if data == None:
        #     return None

        figure, ax = plt.subplots(figsize=(6.5,6.5))
        #ax = figure.subplots()

        sns.despine(figure, left=True, bottom=True)
        # # plot the data
        #figure = Figure(figsize=(6, 6))


        '''
        may have to do x=1-30 or this might get messy (expnum + plate num?)
        structure the scatter plot for x = pos 1-15, y = h2 umol, legend/hue = expNum
        
        
        When HOLLY is back up, seperate sample_name to plate#, vial#
        x = vial#
        y = h2 umol
        hue = expnum + "P:" plate#
        '''

        # x = data["form_name"]
        # y = data["calc_%_H2_umol"]
        # sns.scatterplot(x=x,y=y, ax=ax)
        #df1.drop(df[df["form_name"] == i].index, inplace=True)
        #samples = df[df["form_name"] == i].index, inplace=True)
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()

        for i in df["form_name"]:
            full = int(i.split("-")[-1])
            #print(full)
            if full == 14 or full == 15 or full == 29 or full == 30:
                #print(i)
                #print(df["form_name"])
                #df2 = df.drop(df[df["form_name"] == i].index)  # Controls only
                controls = df.loc[df["form_name"] == i]
                df2 = pd.concat([df2,controls])

            else:
                samples = df.loc[df["form_name"] == i]
                df1 = pd.concat([df1,samples])


        #print(df2)
        #print(df2["calc_%_H2_umol"])
        #print(df2["form_name"])
        #print(df1)

        #df1 = df.drop(df[df["Type"] == "Control"].index)  # samples only
        #df2 = df.drop(df[df["Type"] == "Sample"].index)  # controls only
        x = self.x_var_ddown.get()
        y= self.y_var_ddown.get()
        #print(x,y)

        ax = sns.scatterplot(data=df1, x=x, y=y, hue="calc_%_H2_umol", palette="ch:r=-0.5,l=0.8",
                             edgecolor="none")  # id by h2 umol
        sns.scatterplot(data=df2, x=x, y=y, facecolor="black", edgecolor="none", marker="X")  # Controls
        ax.legend([], [], frameon=False)

        #print(df1)

        ax.set_ylabel(y)
        ax.set_xlabel(x)
        #plt.show()
        #sns.scatterplot( data = data["calc_%_H2_umol"],ax=ax)


        return figure





    def graph_update(self):
        # figure = None
        # figure = self.graph_create_test()
        # self.canvas.figure = figure
        # self.canvas.draw()
        self.canvas.get_tk_widget().destroy()
        #print("graph destroyed")
        self.graph_init()

    def mat_list_init(self):
        '''
        needs to read through the material list and iterate through names to build this section to as large as required.
        Give name, type and amount "Name - Type: 50mL"
        '''
        mat_list_df = pd.read_csv(optimiser_dir + "Material tracking/material_list.csv", delimiter=",")
        mat_list_df = mat_list_df.set_index("Material")
        #print(mat_list_df)
        label_list = []
        count = 0
        for i in mat_list_df.index.values:
            type = ""
            total = 0
            unit = ""
            waste = ""
            #print(mat_list_df.loc[i])
            for j in mat_list_df.loc[i]:
                if str(j) == "nan":
                    continue
                if type == "":
                    type = j
                    if j == "solid":
                        unit = " g"
                    else: unit = " mL"
                    continue
                if "-" in str(j):
                    continue
                if "In Wash" in str(j):
                    continue
                if not unit == "":
                    total = total + float(j)
            f = (i + " - " + type + " : " + str(total) + unit)
            label_list.append(tk.Label(self.material_list_frame, text=f))
            label_list[count].grid(row=count, column=1, sticky="w")
            count += 1

        waste_file = open(optimiser_dir+ "Material tracking\waste.txt", "r")
        waste_list = waste_file.read()
        waste_list = waste_list.splitlines()
        waste_file.close()
        final_list = ""
        for w in waste_list:
            if final_list == "":
                final_list = w
            else: final_list = final_list +" ," + w




        label_list.append(tk.Label(self.material_list_frame, text="Waste: " + final_list))
        label_list[count].grid(row=count, column=1, sticky="w")
        count += 1

        reset_mat_list_btn = ttk.Button(self.material_list_frame, text="Reset Materials", command=reset_mat_list)
        reset_mat_list_btn.grid(row=count, column=1, sticky="se")
            #print("Mat: " +i, "Type: " + type, "Total: " +str(total))


            #print(mat_list_df.transpose()[i])

            #print(mat_list_df.iloc[1:2, [1,2]])



        #label_{}.format(i) = tk.Label(self.start_menu_frame, textvariable=self.queue_var)


        # for i in other_df.values.tolist():
        #     print(mat_list_df._get_value(i, "type"))
        #     if mat_list_df._get_value(i, "type") == "solid":
        #         pass


        pass

    def mat_list_update(self):
        "destroy all children in frame then rebuild"

        for i in self.material_list_frame.winfo_children():
            i.destroy()
        self.mat_list_init()


    def mat_list_reset(self):
        os.remove(optimiser_dir + "Material tracking\material_list.csv")

        dst_file = optimiser_dir + ("Material tracking\material_list.csv")


        shutil.copy(optimiser_dir+'Material tracking\material_list_blank.csv', dst_file)
        waste_file = open(optimiser_dir+ "Material tracking\waste.txt", "w")
        waste_file.write("")
        waste_file.close()

        self.mat_list_update()







        # view_all_label = tk.Label(self.start_menu_frame, text="View all by:")
        #
        # view_all_label.grid(row=3, column=1, rowspan=1, padx=0, sticky="ew")
        #
        # # buttons
        # process_new_batch_button = ttk.Button(self.start_menu_frame, text="Process new batch", command=data_processing)
        # view_by_access_button = ttk.Button(self.start_menu_frame, text="Access", command=view_by_access)
        # view_by_excel_button = ttk.Button(self.start_menu_frame, text="Excel", command=view_by_excel)
        #
        # process_new_batch_button.grid(row=2, column=3, rowspan=1, padx=0, sticky="ew")
        # view_by_access_button.grid(row=3, column=2, rowspan=1, padx=0, sticky="ew")
        # view_by_excel_button.grid(row=3, column=3, rowspan=1, padx=0, sticky="ew")


class ExcelView(tk.Frame):
    # self is own self, parent is container and controller is master
    '''For use with view_select
    To pick and choose which exps you want to view at one time'''

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.excelview_create_widgets()
        # self.update_label()

    def excelview_create_widgets(self):

        # Submit needs to start processing

        self.LHframe = tk.LabelFrame(self)
        self.RHframe = tk.LabelFrame(self)
        self.LHframe.grid(row=0, column=0, sticky="w", padx=10, rowspan=2)
        self.RHframe.grid(row=1, column=1, sticky="wn", padx=50)

        # Listbox - Options
        self.listbox_options = tk.Listbox(self.LHframe, width=60, height=40, borderwidth=2)
        self.listbox_options.grid(row=2, rowspan=2, column=0, padx=10)
        scrollbar_options = tk.Scrollbar(self.LHframe, orient="vertical")
        scrollbar_options.config(command=self.listbox_options.yview)
        self.listbox_options.config(yscrollcommand=scrollbar_options.set)
        scrollbar_options.grid(row=2, rowspan=2, column=0, sticky="ens")

        # Listbox - Selected
        self.listbox_selected = tk.Listbox(self.LHframe, width=60, height=40, borderwidth=2)
        self.listbox_selected.grid(row=2, rowspan=2, column=4, padx=10)
        scrollbar_selected = tk.Scrollbar(self.LHframe, orient="vertical")
        scrollbar_selected.config(command=self.listbox_selected.yview)
        self.listbox_selected.config(yscrollcommand=scrollbar_selected.set)
        scrollbar_selected.grid(row=2, rowspan=2, column=4, sticky="ens")

        # Labels
        select_directory_label = tk.Label(self.LHframe, text="Processed Batches")
        select_directory_label.grid(row=0, column=0, rowspan=2, padx=30, sticky="w")
        selected_label = tk.Label(self.LHframe, text="Selected Batches:")
        selected_label.grid(row=0, column=4, sticky="w", ipadx=10)

        # Buttons
        remove_choice_button = tk.Button(self.LHframe, text="<", command=listbox_remove_choice)
        remove_choice_button.grid(row=2, column=2, sticky="wes", ipadx=10)
        select_choice_button = tk.Button(self.LHframe, text=">", command=listbox_select_choice)
        select_choice_button.grid(row=2, column=3, sticky="wes", ipadx=10)
        remove_all_button = tk.Button(self.LHframe, text="<<", command=listbox_remove_all)
        remove_all_button.grid(row=3, column=2, sticky="wen", ipadx=10, pady=5)
        select_all_button = tk.Button(self.LHframe, text=">>", command=listbox_select_all)
        select_all_button.grid(row=3, column=3, sticky="wen", ipadx=10, pady=5)

        submit_nav_output = tk.Button(self.RHframe, text="View Selected",
                                      command=view_selected_batches)
        submit_nav_output.grid(sticky="es", row=6,
                               column=1,
                               ipadx=10)  # get(0, END) to get whole list, get(ACTIVE) for highlighted, delete(Active)

    def excelview_listbox_options_update(self, data):
        self.listbox_options.delete(0, "end")
        for i in data:
            self.listbox_options.insert("end", i)

    def excelview_listbox_selected_update(self, data):
        if data == 0:  # remove
            self.listbox_options.insert("end", self.listbox_selected.get("active"))
            self.listbox_selected.delete("active")
        if data == 1:  # add
            self.listbox_selected.insert("end", self.listbox_options.get(
                "active"))  # adds active to selected and removes from options
            self.listbox_options.delete("active")
        if data == 2:  # remove all
            list = self.listbox_selected.get(0, "end")
            self.listbox_selected.delete(0, "end")
            for i in list:
                self.listbox_options.insert("end", i)
            self.listbox_selected.delete(0, "end")
        if data == 3:  # add all
            list = self.listbox_options.get(0, "end")
            self.listbox_options.delete(0, "end")
            for i in list:
                self.listbox_selected.insert("end", i)

    def excelview_return_parameters(self):
        if self.listbox_selected.get(0) == "":
            return "Error - Please select files to process"
        '''
        .get() returns int value for state, 0 = unselected, if total = 0 then nothing selected, throw error
        '''
        s_list = self.listbox_selected.get(0, "end")  # selected list
        return s_list


class Output(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

    def output_update(self, data):
        '''
        Checks saving directory,
        Generates output filename,
        reads in CSV,
        process data to get avg, 2sd and gas mol,
        adds this data to dataframe,
        moves to next csv; iterates through all in batch,
        output to single CSV
        '''

        # Generates output file using template
        global template_filename, template_dir, output_dir, filetype
        print(data[2])
        self.output_filename = (data[2]) + "_" + str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        # batch_id + yyyy-mm-dd_HH-MM-SS

        global headspace_volume, molar_vol_gas, every_nth_file
        nth_counter = 1
        processed_output_dict = {}
        for i in data[0]:
            i2 = (i.split("_"))[2]  # takes file name, splits for FormulationIdxxxxxx
            if nth_counter != every_nth_file:  # skips through scans until desired is reached
                nth_counter += 1
                continue
            nth_counter = 1  # resets counter as desired has been reached
            form_datetime = i.split("_")[3]  # takes the datetime from formulation filename
            form_datetime = form_datetime.split(".")[0:2]  # cuts off .csv extension
            form_datetime = "20" + form_datetime[0] + form_datetime[1]
            # adds 20 to start of date to give date format e.g 20200314
            if processed_output_dict == {}:  # If nothing in dict, first should be an n2_sample
                pass
                # processed_output_dict.setdefault("N2_samp", []).append((True))

            elif i2.split("Id")[1] not in processed_output_dict["form_id"]:
                # processed_output_dict.setdefault("N2_samp", []).append((True))
                '''If nothing in dict, add this first formID as add. sampling
                If this formID not in dict, mark this as the add. sampling (As this occurs first, 
                if the list is ordered then this should be the first entering the dict)'''

            else:
                pass
                # processed_output_dict.setdefault("N2_samp", []).append((False))

            processed_output_dict.setdefault("form_id", []).append((i2.split("Id"))[1])  # takes the xxxxxxx from formID
            processed_output_dict.setdefault("form_datetime", []).append(form_datetime)
            to_skip = list(range(0, 32)) + [33, 34]  # reads to line 33 in csv (headers), then skips first 2 scans
            current_file_df = pd.read_csv((data[1] + "/" + i), skiprows=to_skip)
            # Reads the formatted output sheet into a dataframe
            current_file_df = current_file_df.dropna(1)
            # removes empty space / NaNs to the right
            current_file_df.rename_axis()

            for col in current_file_df.columns:
                if "%" in col or "Baratron" in col:
                    processed_output_dict.setdefault(("{} Avg").format(col), []).append(
                        current_file_df[("{}").format(col)].mean())

                    processed_output_dict.setdefault(("{} 2STD").format(col), []).append(
                        current_file_df[("{}").format(col)].std() * 2)
                if col == "% H2" or col == "% O2":
                    # if "H2" in col or "O2" in col:
                    avg_gas_per = current_file_df[("{}").format(col)].mean()  # per = %
                    avg_gas_vol_mL = avg_gas_per * headspace_volume
                    if avg_gas_vol_mL == 0:  # incase no desired gas in vial
                        avg_gas_umol = 0
                    else:
                        avg_gas_umol = ((avg_gas_vol_mL / 1000) / molar_vol_gas) * 10 ** 6
                    # Finds gas mol, flips and divides for umol

                    processed_output_dict.setdefault("{} umol".format(col), []).append(avg_gas_umol)

        processed_output_df = pd.DataFrame.from_dict(data=processed_output_dict)
        # Converts the dictionary to a Pandas Dataframe

        processed_output_df["form_id"] = pd.to_numeric(processed_output_df["form_id"])
        processed_output_df["form_datetime"] = pd.to_datetime(processed_output_df["form_datetime"],
                                                              format="%Y%m%d%H%M%S")

        processed_output_df.set_index("form_id", inplace=True)
        self.processed_output_df = processed_output_df

        Output.output_csv_processing(self)

        #self.output_create_widgets()
        #app.show_frame(Output)
        print("Processing Complete")

    def output_csv_processing(self):
        global template_filename, template_dir, output_dir, filetype

        self.processed_output_df.to_csv(output_dir + self.output_filename + ".csv")
        print(str(len(self.processed_output_df.index)) + " files processed")
        print(self.output_filename + " complete")


def label_update():
    app.update_frame(cont=StartMenu, arg=1)
    #arg is the frame switch

def archive_exp(exp_nam):
    print("moving running file to archive")
    shutil.move(src=optimiser_dir +"running/" + exp_nam + ".xlsx", dst=optimiser_dir +"archive/" + exp_nam + ".xlsx")

def select_batch_processing():

    dirname = filedialog.askdirectory(initialdir=unprocessed_batch_dir, title="Select batch to process")

    batch_processing(dirname)

def select_batch_processing_forced():
    dirname = filedialog.askdirectory(initialdir=unprocessed_batch_dir, title="Select batch to process")

    batch_processing(dirname, False)

    #app.update_frame(cont=Output, data_type="data_processing", data=r_list)
def all_batch_processing():
    global unprocessed_batch_dir
    #dirlist = [f for f in os.listdir(default_batch_loc) if isfile(join(default_batch_loc, f))]
    #dirlist = os.walk(default_batch_loc)
    dirlist = glob.glob(unprocessed_batch_dir + "/*")
    # for i in dirlist:
    #     i = i.split("/")[-1]
    #     i = i.split("\\")[-1]
    #     print(i)
    for i in dirlist:
        dirname = i
        batch_processing(dirname)
    '''
    Hopefully this doesn't get stuck looping too long, should help to do one exp at a time to reduce impact of errors
    '''


def view_all_csv():
    dirlist = glob.glob(optimiser_dir_comp + "/*")
    df_all = pd.DataFrame()
    for f in dirlist:
        #print(f)
        df_curr = pd.read_excel(f)
        df_all = pd.concat([df_all, df_curr])
    df_all.to_csv(view_dump + "view_all-{}.csv".format(str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))))
    print("view dumped")






def listening_thread(start=True):



    if start == True:
        event.set()
        AutoPopup()



    if start == False:
        event.clear()




def upload_exp():
    myvar = easygui.ynbox("Upload all experiments in queue?")
    #print(myvar)


    if myvar:

        dirlist = glob.glob(optimiser_dir+"/runqueue" "/*")

        for i in dirlist:
            exp_dirname = i
            holly_webscraper.upload_exp(inputFile=exp_dirname)








def upload_exp_pickexp():
    exp_dirname = None

    try:
        exp_dirname = filedialog.askopenfilename(initialdir=optimiser_dir+"/runqueue/", title="Pick a file to upload")

        exp_dirname = os.path.normpath(exp_dirname)
    except:
        print("Dialog closed")

    if  exp_dirname  != None:
        holly_webscraper.upload_exp(inputFile=exp_dirname)

def upload_exp_pickexp_pickrun():
    exp_dirname = None
    run_id = None
    try:
        exp_dirname = filedialog.askopenfilename(initialdir=optimiser_dir+"/runqueue/", title="Pick a file to upload")

        exp_dirname = os.path.normpath(exp_dirname)
    except:
        print("Dialog closed")

    run_id = easygui.enterbox(("Run ID:"))

    if  exp_dirname  != None:
        holly_webscraper.upload_exp(inputFile=exp_dirname, run=run_id)



def just_dispenses():
    batch_id = input("Please enter Experiment number:")
    print(batch_id)
    dispense_df, exp_name = holly_webscraper.holly_webscaper(batch_id,optimiser_dir)

    dispense_df.to_csv(view_dump + "{}.csv".format(batch_id)) # drop in view dump to not get mixed with actual output
    print("Dispense-only complete")
    os.startfile(view_dump)

def update_graph():
    app.update_frame(cont=StartMenu, arg=4)



def batch_processing(dirname, check_flag = True):
    # app.update_frame(cont=StartMenu, data_type="label_update", data=dirname)
    #''' Cont = desired page, inputType= will be label, listbox, etc; input= filename/dir'''

    try:
        dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]
        dirname = os.path.normpath(dirname)
        batch_id = (dirname.split("\\"))[-1]
        print("Processing: {}".format(batch_id))

        r_list = dir_contents, dirname, batch_id
        # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
        if check_flag:
            check = holly_webscraper.holly_complete_check(batch_id)
        if not check_flag:
            check = True
        processed_output_df = batch_processor.batch_processor(bp_params, r_list)
        processed_output_df.sort_index(axis=0, inplace=True)

       # starts catch loop as web scraping most likely to give errors
        while check:
            try:
                #batch_id -> expNum
                dispense_df, exp_name = holly_webscraper.holly_webscaper(batch_id, optimiser_dir)
                # remove / or \from expname - try not to add these in the first place
                if "/" in exp_name:
                    exp_name = exp_name.replace("/", "")
                if "\ " in exp_name:
                    exp_name = exp_name.replace("\ ", "")

                collated_df = pd.concat([dispense_df, processed_output_df], axis=1)
                collated_df.reindex()
                collated_df.fillna(0, inplace=True)
                #post batch file handling - moves unprocessed hiden csv to processed folder
                collated_df.to_excel(optimiser_dir_comp+"{}.xlsx".format(batch_id + (" - {}".format(exp_name))), sheet_name="Output")
                print("File collated and dumped")
                shutil.move(dirname, processed_batch_dir + "\\" + str(batch_id))
                label_update()

                return exp_name
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
    except Exception as e:
        print(e)

def batch_recovery():
    '''
    User needs to pick the hiden data exp (from unproccessed dir) and provide the HOLLY dispense exp
    Largely the same as batch processing but does not pass Exp# from HIDEN to HOLLY
    Not joined by primary key as =/=
    Joined by time/date sort of holly results and plate#vial# of hiden
    ONLY WORKS IF PLATES USED IN ACSENDING ORDER ie 1 to 4
    '''

    dirname = filedialog.askdirectory(initialdir=unprocessed_batch_dir, title="Hiden batch to recover")
    dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]
    dirname = os.path.normpath(dirname)
    holly_exp = input("Enter HOLLY Exp# (eg 685) \n")
    batch_id = (dirname.split("\\"))[-1]
    print("Processing: {}".format(batch_id))

    r_list = dir_contents, dirname, batch_id
    # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
    processed_output_df = batch_processor.batch_processor(bp_params, r_list)
    processed_output_df.reset_index(inplace=True)
    processed_output_df.drop(columns="form_id", axis=1, inplace=True)
    processed_output_df.set_index("sample_name", inplace=True)
    processed_output_df = processed_output_df.reindex(index=natsorted(processed_output_df.index)) # quick way to sort AN strings so A2 comes before A11
    processed_output_df.reset_index(inplace=True)

    dispense_df = holly_webscraper.holly_webscaper(holly_exp)
    dispense_df.reset_index(inplace=True)

    '''
    Both dispense and hiden dataframes made using semi-normal process
    Primary keys (form_id) removed, hiden data must be named as such that it gives correct order to form_id
    ie if plates are only ever used in ascending order then ag1 to ag4 will work
    hiden data sorted to plate name - vial num and bolted onto dispense data
    '''


    #collated_df = pd.concat([dispense_df, processed_output_df], axis=1)
    collated_df = pd.merge(dispense_df, processed_output_df, left_index=True, right_index=True, how="outer")
    collated_df.set_index("form_id", inplace=True)
    #print(collated_df)
    # post batch file handling - moves unprocessed hiden csv to processed folder
    collated_df.to_excel(optimiser_dir_comp + "{}.xlsx".format(batch_id))
    print("File collated and dumped")
    #shutil.move(dirname, processed_batch_dir + "\\" + str(batch_id))
    label_update()

def hiden_process_only():
    dirname = filedialog.askdirectory(initialdir=unprocessed_batch_dir, title="Hiden batch to process")


    dirname = os.path.normpath(dirname)

    dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]

    #dirname = os.path.normpath(dirname)
    batch_id = (dirname.split("\\"))[-1]
    print("Processing: {}".format(batch_id))

    r_list = dir_contents, dirname, batch_id
    # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
    #print(r_list)
    processed_output_df = batch_processor.batch_processor(bp_params, r_list)
    #processed_output_df.reset_index(inplace=True)
    #processed_output_df.drop(columns="form_id", axis=1, inplace=True)
    #processed_output_df.set_index("sample_name", inplace=True)
    #processed_output_df = processed_output_df.reindex(index=natsorted(processed_output_df.index)) # quick way to sort AN strings so A2 comes before A11
    #processed_output_df.reset_index(inplace=True)

    processed_output_df.to_csv((optimiser_dir_comp+"{}"+".csv").format(str(batch_id)))

#laptop is py 3.9
#hiden_process_only()

def button_temp():
    print("not implemented")

def listbox_remove_choice():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=0)


def listbox_select_choice():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=1)


def listbox_remove_all():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=2)


def listbox_select_all():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=3)


def view_by_excel():
    global output_dir
    dir_contents = [f for f in os.listdir(output_dir) if isfile(join(output_dir, f)) and f.split(".")[1] == "csv"]
    # checks if isfile and isCSV == true
    app.update_frame(cont=ExcelView, data_type="listbox_option_update", data=dir_contents)
    app.show_frame(ExcelView)

def test_email():
    '''
    Reads all completed xlsx files in completed, collates and adds exp id, dumps file

    '''

    email_update("Test")

    #
    # dir_contents = [f for f in os.listdir(optimiser_dir_comp) if isfile(join(optimiser_dir_comp, f)) and f.split(".")[1] == "xlsx"]
    # csv_list = []
    # for f in dir_contents:
    #     df = pd.read_excel(optimiser_dir_comp+f,  header=0)
    #     exp_1 = f.split(".")[0] #id - name
    #     exp_1, exp_2 = exp_1.split(" - ")
    #     df.insert(1, "Exp#", exp_1)
    #     df.insert(2, "Exp:", exp_2)
    #     csv_list.append(df)
    # csv_df = pd.concat(csv_list, axis=0, ignore_index=False)
    # csv_df = csv_df.reset_index()
    # csv_df.to_excel(view_dump + "/{}.xlsx".format("ExcelView_" + str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))))
    # os.startfile(view_dump)

def graph_data():
    if len(os.listdir(optimiser_dir_comp)) ==0:
        print("No data for graph")
        return None

    dir_contents = [f for f in os.listdir(optimiser_dir_comp) if
                    isfile(join(optimiser_dir_comp, f)) and f.split(".")[1] == "xlsx"]

    x_list = []
    for f in dir_contents:
        df = pd.read_excel(optimiser_dir_comp + f, index_col="form_id", header=0)
        df.insert(0, "Exp#", f.split(".")[0])
        x_list.append(df)
    x_df = pd.concat(x_list, axis=0, ignore_index=True)
    x_df.index.names = ["index"]
    return x_df

def graph_of_components():
    df = graph_data()
    #df["10_Pt/TiO2"] = df["10_Pt/TiO2"] * 1000
    f, axes = plt.subplots(4, 4, figsize=(12, 7), sharey=False, sharex=False)
    #figsize was 24, 13.5
    f.tight_layout()

    x = ["10_Pt/TiO2", "11_PCN", "12_Pt/CdS","13_Pt/WO3",
         "20_Xylose-0.25M", "21_Proline","22_Cysteine","23_Glucose","24_Cellobiose",
         "30_NaOH-0.5M", "31_CitricAcid-0.5M", "32_AcidYellow73","33_AcidViolet43",
         "34_AcidGreen1",
         "calc_%_O2_umol", "calc_%_CO2_umol"]
    # x = ["10_Pt/TiO2", "11_PCN", "12_Pt/CdS","13_Pt/WO3",
    #      "20_Xylose-0.25M", "21_Proline","23_Glucose","24_Cellobiose",
    #      "30_NaOH-0.5M", "31_CitricAcid-0.5M", "32_AcidYellow73","33_AcidViolet43",
    #      "34_AcidGreen1",
    #      "calc_%_O2_umol", "calc_%_CO2_umol"]

    #x = ["10_Pt/TiO2", "11_PCN", "12_Pt/CdS", "13_Pt/WO3"]

    df1 = pd.DataFrame()
    df2 = pd.DataFrame()


    for i in df["form_name"]:
        full = int(i.split("-")[-1])
        # print(full)
        if full == 14 or full == 15 or full == 29 or full == 30:
            # print(i)
            # print(df["form_name"])
            # df2 = df.drop(df[df["form_name"] == i].index)  # Controls only
            controls = df.loc[df["form_name"] == i]
            df2 = pd.concat([df2, controls])

        else:
            samples = df.loc[df["form_name"] == i]
            df1 = pd.concat([df1, samples])
    #print(df2)
##remove cysteine test
    #df1.drop(df1.loc[df1["22_Cysteine"]>0].index,inplace=True)
    #print(df1)



    #print(df2)

    h = 0
    for ax, s in zip(axes.flat, np.linspace(0, 3, 16)):

        # cmap = sns.cubehelix_palette(start=1, light=0.2, as_cmap=True)
        # palette="ch:r=-0.4" -- the nice one
        # palette = "ch:r=-{}".format(i)



        sns.scatterplot(data=df1, x="index", y=x[h],
                        ax=ax, hue="calc_%_H2_umol", alpha=1, palette="ch:r=-0.4", s=50, edgecolor="none")

        sns.scatterplot(data=df2, x="index", y=x[h], ax=ax, alpha=0.2, facecolor="black",
                        edgecolor="none", marker="X")  # Controls
        ax.legend([], [], frameon=False)

        ax.set_xlabel(x[h])
        #ax.xaxis.labelpad = 50
        # ax.set_ylabel("Dispense (mg / mL)")
        # ax.set_xlabel("ID")

        ax.legend([], [], frameon=False)
        # ax.set(ylim=(0,5))
        if "umol" in x[h]:
            ax.set_ylabel("umol")
        else:
            ax.set_ylabel("Dispense (mg / mL)")
            ax.set(ylim=(-0.5, 6))
        h += 1

        # ax.set_axis_off()
    handles, labels = ax.get_legend_handles_labels()

    f.legend(handles, labels, loc="upper right", title="H2 umol")

    plt.show()


def reset_mat_list():
    answer = messagebox.askyesno("Warning", "Reset materials?")
    if answer == True:
        app.update_frame(cont=StartMenu, arg=3)

def open_comp_file():
    os.startfile(optimiser_dir_comp)
def open_b_processing_file():
    os.startfile(processed_batch_dir)
def view_selected_batches():
    global output_dir
    return_batches = app.update_frame(cont=ExcelView, data_type="return_parameters")
    li = []
    for filename in return_batches:
        df = pd.read_csv(output_dir + filename, index_col=None, header=0)
        li.append(df)
    all_batches_df = pd.concat(li, axis=1, ignore_index=True)

    wb = xw.Book()
    sheet = wb.sheets["Sheet1"]
    sheet.range("A1").value = all_batches_df

def run_bayes_op():
    '''
    runs bayes op - didn't incorp to main as I didn't make it
    '''

    os.chdir(optimiser_dir)
    os.system("python experiment.py")
    app.update_frame(cont=StartMenu, arg=1) # label update
    app.update_frame(cont=StartMenu, arg=2) # mat list update


    #label_update()


    # if not xbatches == "":
    #     xbatches = int(xbatches)
    #     if xbatches > 0:
    #         os.chdir(optimiser_dir)
    #         os.system("py experiment.py {}".format(xbatches))
    #         label_update()
    #     else:
    #         print("Error: batch# invalid")
    # else:
    #     print("Error: batch# blank")

# Maintains tkinter interface

def email_update(filename):
    SCOPES = [
            "https://www.googleapis.com/auth/gmail.send"
        ]
    creds = ""
    if os.path.exists(data_pro_dir + "token.pickle"):
        with open(data_pro_dir + "token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            #creds.refresh()
            flow = InstalledAppFlow.from_client_secrets_file(
                data_pro_dir+'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                data_pro_dir+'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(data_pro_dir + "token.pickle", 'wb') as token:
            pickle.dump(creds, token)


    #flow = InstalledAppFlow.from_client_secrets_file(data_pro_dir+'credentials.json', SCOPES)
    #creds = flow.run_local_server(port=0)


    service = build('gmail', 'v1', credentials=creds)
    message = MIMEText(filename + " uploaded at: " + str(datetime.datetime.now()))
    message['to'] = 'jackgee43@gmail.com'
    message['subject'] = ('Uploaded experiment: ' + filename)
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(F'sent message to {message} Message Id: {message["id"]}')

    except HTTPError as error:
        print(F'An error occurred: {error}')
        message = None


def on_closing():
    quit()


app = Application(master=tk.Tk())
app.mainloop()
