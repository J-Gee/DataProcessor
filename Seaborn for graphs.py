import datetime
import tkinter.filedialog

import matplotlib
import pandas
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tkinter as tk
import glob
#
# rng = np.random.RandomState(0)
# x = np.linspace(0, 10, 500)
# y = np.cumsum(rng.randn(500, 6), 0)

matplotlib.rcParams.update({"figure.autolayout": True})


#dir = r"C:\Users\jackh\OneDrive - The University of Liverpool\PhD\Project Results Storage\Project Software\Formulation Engine Data Processing\Output and templates\View Dump\ExcelView_2022-05-30_14-32-07.xlsx"
dir = r"C:\Users\jackh\OneDrive - The University of Liverpool\Thesis\Chapter-3\Data\Biomass\Large screen data"
dir1 = r"C:\Users\jackh\OneDrive - The University of Liverpool\PhD\Project Results Storage\Project Software\Bayesian Optimiser\fe_optimizer-master\Optimizer\archive\Biomass Screening\bv screening\Data dump for seaborn heatmap - alt biomass.xlsx"
dir2 = r"C:\Users\jackh\OneDrive - The University of Liverpool\PhD\Project Results Storage\Project Software\Bayesian Optimiser\fe_optimizer-master\Optimizer\archive\Biomass Screening\bv screening\Data dump for seaborn heatmap - low ph.xlsx"

#dirname = tk.filedialog.askopenfilename(initialdir=dir, title="Pick data to process")

# x=df["ID"]
# y=df["calc_%_H2_umol"]
#print(df)
# sns.set()
# plt.plot(x,y)
# plt.show()




#sns.relplot(data=df, x="Exp#", y="calc_%_H2_umol", hue="Vial", palette="ch:r=-.4", style="Control")

#sns.scatterplot(data=df, x="Exp#", y="calc_%_H2_umol", hue="PCN", palette="ch:r=-.4", style="Control")



def scatter_overall():

    # sns.scatterplot(data=df, x="index", y="calc_%_H2_umol", style="Type", hue="calc_%_H2_umol",
    #                 palette="ch:r=-0.5,l=0.8", edgecolor="none")  # id by h2 umol

    df1 = df.drop(df[df["Type"] == "Control"].index) # samples only
    df2 = df.drop(df[df["Type"] == "Sample"].index) # controls only

    ax = sns.scatterplot(data=df1, x="index", y="calc_%_H2_umol", hue="calc_%_H2_umol", palette="ch:r=-0.5,l=0.8", edgecolor="none")  # id by h2 umol
    sns.scatterplot(data=df2, x="index", y="calc_%_H2_umol",
                    palette="ch:r=-0.5,l=0.8", facecolor="black", edgecolor="none", marker="X")  # Controls
    ax.legend([], [], frameon=False)
    ax.set_ylabel("H2 evolution (mg / mL)")
    ax.set_xlabel("ID")
def kdeplot():
    f, axes = plt.subplots(3,3, figsize=(9,9), sharey=True)
    i=0
    for ax, s in zip(axes.flat, np.linspace(0,3,10)):
        x=["10_Pt/TiO2","20_Xylose-0.25M","21_NaOH-0.5M","22_CitricAcid-0.5M","23_AcidYellow73","24_AcidViolet43","25_AcidGreen1"]

        cmap = sns.cubehelix_palette(start=5, light=2, as_cmap=True)
        sns.kdeplot(data=df, cmap=cmap, x=x[i], y="calc_%_H2_umol", fill=True, clip=((0,80)), thresh=0, levels=100, ax=ax)
        ax.set(xlim=(0,5))

        i +=1
        #ax.set_axis_off()



def scatterplot():
    dirname = tk.filedialog.askdirectory(initialdir=dir, title="Pick data to process")

    dirlist = glob.glob(dirname + "/*")
    df_cur = pandas.DataFrame()
    df_all = pandas.DataFrame()


    for i in dirlist:
        df_cur = pd.read_excel(i)
        df_all = pd.concat([df_all, df_cur], ignore_index=True)
    df_all["10_Pt/TiO2"] = df_all["10_Pt/TiO2"]*1000
    print(df_all)

    df_all.index.names = ["index"]

    # x_list = []
    # for f in dir_contents:
    #     df = pd.read_excel(optimiser_dir_comp + f, index_col="form_id", header=0)
    #     df.insert(0, "Exp#", f.split(".")[0])
    #     x_list.append(df)
    # x_df = pd.concat(x_list, axis=0, ignore_index=True)
    #x_df.index.names = ["index"]



    f, axes = plt.subplots(3, 3, figsize=(24, 13.5), sharey=False, sharex=False)
    #f.tight_layout()
    i = 0
    x = ["10_Pt/TiO2", "20_Xylose-0.25M", "21_NaOH-0.5M", "22_CitricAcid-0.5M", "23_AcidYellow73", "24_AcidViolet43",
         "25_AcidGreen1", "calc_%_O2_umol", "calc_%_CO2_umol"]
    for ax, s in zip(axes.flat, np.linspace(0, 3, 10)):


        #cmap = sns.cubehelix_palette(start=1, light=0.2, as_cmap=True)
        #palette="ch:r=-0.4"
        #palette = "ch:r=-{}".format(i)
        sns.scatterplot(data=df_all, x="index", y=x[i],
                    ax=ax, hue="calc_%_H2_umol", palette="ch:r=-0.4", s=20, edgecolor="none")

        ax.set_xlabel(x[i])
        #ax.set_ylabel("Dispense (mg / mL)")
        #ax.set_xlabel("ID")

        ax.legend([],[], frameon=False)
        #ax.set(ylim=(0,5))
        if "umol" in x[i]:
            ax.set_ylabel("umol")
        else:
            ax.set_ylabel("Dispense (mg / mL)")
            ax.set(ylim=(0, 5))
        i += 1

        # ax.set_axis_off()
    handles, labels = ax.get_legend_handles_labels()

    f.legend(handles, labels, loc="upper right", title="H2 umol")

#scatterplot()
#kdeplot()
#plt.legend([],[],frameon=False)

def biomass_heatmap():
    df = pd.read_excel(dirname)

    #print(df["Test"])
    data = df.pivot("Test", "Catalyst", "H2 Evol")
    sns.set(font_scale=1.6)

    cat_list = []
    for i in df["Catalyst"]:
        if not i in cat_list:
            cat_list.append(i)

    test_list = []
    for i in df["Test"]:
        if not i in test_list:
            test_list.append(i)

    cat_list.sort()
    test_list.sort()


    #cmap = sns.diverging_palette(220, 8, as_cmap=True, center="dark")
    #cmap = sns.diverging_palette(220,8, as_cmap=True)
    #cmap = sns.cubehelix_palette(as_cmap=True, light=.9)

    #df["Catalyst"] = df.Catalyst.astype(str)
    #b = sns.heatmap(data, annot=False, fmt="f", linewidths=0.5, cmap= cmap, cbar_kws={"label": "H2 umol/hg"})


    mask = data.isnull()


    cmap = sns.color_palette(palette="mako", as_cmap=True).copy()
    cmap.set_bad("gray")
    b = sns.heatmap(data, annot=False, fmt="f", cmap = cmap, linewidths=0,  cbar_kws={"label": "H2 umol/hg"})
    b.set_facecolor("gray")
    b.set_xticklabels(cat_list,  rotation = 45)

    b.set_yticklabels(test_list)

    #b.tight_layout()
    #plt.xlabel(weight="bold")
    #b.set_xlabel(cat_list,fontsize=20)






#scatter_overall()
#biomass_heatmap()
scatterplot()
#plt.tight_layout()

manager = plt.get_current_fig_manager()
manager.resize(1920, 1080)
fig = plt.gcf()
#plt.savefig((dir+"\\"+"{}.svg").format(str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))), transparent=True, bbox_inches="tight" )
#plt.autoscale()

plt.show()
#fig.savefig((dir+"\\"+"{}.svg").format(str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))), transparent=True)