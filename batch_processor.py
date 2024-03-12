import pandas as pd
import datetime

'''
Author: Jack C. Gee
'''
#########################################################

def batch_processor(params, data):
    template_dir, output_dir, default_batch_loc, template_filename, filetype, every_nth_file, illu_time, molar_vol_gas, headspace_volume, rs_dict = params
    #print(data)



    #print(data[2])
    output_filename = (data[2]) + "_" + str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    '''batch_id + yyyy-mm-dd_HH-MM-SS'''
    nth_counter = 1
    processed_output_dict = {}
    remove_h2_std = True
    stdev_limit = 1

    '''NOTE csv name format
    0-PlateName
    1-VialNum
    2-ViewNum
    3-FormID
    4-TimeDate'''

    for i in data[0]:
        i2 = (i.split("_"))[3]  # takes file name, splits for FormulationIdxxxxxx
        if nth_counter != every_nth_file:  # skips through scans until desired is reached
            nth_counter += 1
            continue
        nth_counter = 1  # resets counter as desired has been reached
        form_datetime = i.split("_")[4]  # takes the datetime from formulation filename
        form_datetime = form_datetime.split(".")[0:2]  # cuts off .csv extension
        form_datetime = "20" + form_datetime[0] + form_datetime[1]

        sample_name = i.split("_")[0]+"_"+i.split("_")[1] # just incase view isn't present for a cleaner split
        ''' adds 20 to start of date to give date format e.g 20200314'''
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
        processed_output_dict.setdefault("sample_name", []).append(sample_name)
        to_skip = list(range(0, 32)) + [33, 36]  # reads to line 33 in csv (headers), then skips first 4 scans
        current_file_df = pd.read_csv((data[1] + "/" + i), skiprows=to_skip)
        # Reads the formatted output sheet into a dataframe
        #current_file_df = current_file_df.dropna()
        #current_file_df = current_file_df.dropna(1)
        # removes empty space / NaNs to the right
        current_file_df.rename_axis()

        '''
        Note 2 df's being worked on at once
        1) current_file_df - the csv being read from
        2) processed_output_df - where the processed data is being dumped
         '''
        # adding in-script calc of gas % to df
        real_list = []
        # calcs all the real gas values

        for col in current_file_df.columns:
            if "Scan" in col:
                mass_x = col.split(":")[1]
                rs_req = mass_x.strip()
                rs_vals = rs_dict.get(rs_req, lambda: "Hiden scan not valid - check rs_dict")
                current_file_df["real_{}".format(rs_vals[0])] = current_file_df[col] / float(rs_vals[1])
                real_list.append("real_{}".format(rs_vals[0]))
        # sum the real gas vals

        current_file_df["sum"] = current_file_df[real_list].sum(axis=1)

        for i in real_list:
            col_name = i.split("_")[1]
            #print(col_name)
            current_file_df["calc_%_{}".format(col_name)] = (current_file_df[i] *100)/current_file_df["sum"]
            #print(current_file_df["calc % {}".format(col_name)])


        '''to run using the hiden calc'd percentages, remove "calc" from the % string checks'''
        for col in current_file_df.columns:
            #if "%" in col or "Baratron" in col:
            if "calc_%" in col or "Baratron" in col:
                processed_output_dict.setdefault(("{}_Avg").format(col), []).append(
                    current_file_df[("{}").format(col)].mean())

            #if col == "% H2" or col == "% O2":
            if col == "calc_%_H2" or col == "calc_%_O2" or col == "calc_%_CO2":
                # if "H2" in col or "O2" in col:
                avg_gas_per = current_file_df[("{}").format(col)].mean()  # per = %
                avg_gas_vol_mL = (avg_gas_per/100) * headspace_volume
                if avg_gas_vol_mL == 0:  # incase no desired gas in vial
                    avg_gas_umol = 0
                else:
                    #needs to be in L so (ml/1000) would give mol - we want umol so x10^6 (or just do x1000)
                    avg_gas_umol = (avg_gas_vol_mL * molar_vol_gas)*1000
                # Finds gas mol, flips and divides for umol
                place_hol = col.strip("%").strip()
                processed_output_dict.setdefault(("{}_2STD").format(col), []).append(current_file_df[("{}").format(col)].std() * 2)
                processed_output_dict.setdefault("{}_umol".format(place_hol), []).append(avg_gas_umol)
                processed_output_dict.setdefault("{}_umol/h".format(place_hol), []).append(avg_gas_umol/illu_time)

    processed_output_df = pd.DataFrame.from_dict(data=processed_output_dict)
    # Converts the dictionary to a Pandas Dataframe
    frames_to_drop = processed_output_df[processed_output_df["calc_%_H2_2STD"] > stdev_limit]
    frames = []
    for f in frames_to_drop["form_id"]:
        frames.append(f)
    frames_s = str(frames)
    frames_s = frames_s.strip("[")
    frames_s = frames_s.strip("]")

    #print("High H2 std, dropping ID: " + frames_to_drop["form_id"])
    if not len(frames) == 0:
        print(("High H2 std, dropping {} IDs: ").format(len(frames)) + frames_s)

    processed_output_df = processed_output_df.drop(frames_to_drop.index)

    # Should drop all h2 stds over 1

    #processed_output_df["form_id"] = pd.to_numeric(processed_output_df["form_id"])
    processed_output_df["form_datetime"] = pd.to_datetime(processed_output_df["form_datetime"],
                                                          format="%Y%m%d%H%M%S")


    processed_output_df.set_index("form_id", inplace=True)

    #processed_output_df["form_id"].apply(int)
    processed_output_df = processed_output_df.sort_values(by=["form_id"])


    #processed_output_df.to_csv(output_dir + output_filename + ".csv")

    print(str(len(processed_output_df.index)) + " files processed")
    print(output_filename + " complete")
    return processed_output_df




