#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob

def to_bin_lat(y):
    lat_step = 5.
    binned_lat = np.floor(y / lat_step) * lat_step
    return(binned_lat)

def to_bin_lon(x):
    lon_step = 10.
    binned_lon = np.floor(x / lon_step) * lon_step
    return(binned_lon)

def RO_calendar_creator(start_year, end_year, cdr_version_string, ROM_SAF_path_generic):
    latbins = np.arange(-90,90,5)
    nan_temp_prof = np.empty(301)
    nan_temp_prof[:] = np.NaN
    month_strings = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    RO_df_calendar= []
    for year in range(start_year, end_year):
        print(year)
        year_of_monthly_RO_composites = []
        for month in month_strings:
            print(month)
            RO_paths = (ROM_SAF_path_generic.format(cdr_version=cdr_version_string, satellite='*')
                        + str(year) + '/' + 'DryTempProf_'
                        + '{satellite}_{month}_{year}'.format(satellite='*', month=month, year=str(year)) 
                        + '_5_35km.npy')
            RO_monthly_data_paths = glob.glob(RO_paths)

            if len(RO_monthly_data_paths) == 0:
                empty_map = np.empty((36,301))
                empty_map[:] = np.NaN
                year_of_monthly_RO_composites.append(empty_map)
            else:
                monthly_data_array_all_sats = []
                for monthly_data_path in RO_monthly_data_paths:
                    try:
                        RO_monthly_data = np.load(monthly_data_path, allow_pickle=True)
                        monthly_data_array_all_sats.append(RO_monthly_data)
                    except:
                        continue
                RO_monthly_data_combined = np.concatenate(monthly_data_array_all_sats, axis=0)
                RO_df_one_month = pd.DataFrame(RO_monthly_data_combined, columns=['Lat', 'Lon', 'Temp'])
                RO_df_one_month['Latbin'] = RO_df_one_month.Lat.apply(to_bin_lat)
                RO_df_map = []
                for lat_idx in latbins:
                    ROs_lat = RO_df_one_month[RO_df_one_month['Latbin'] == lat_idx]
                    #ROs_boxes_along_lat = []
                    #for lon_idx in lonbins:
                    #ROs_box = ROs_lat[ROs_lat['Lonbin'] == lon_idx]
                    if ROs_lat.size == 0:
                        RO_df_map.append(nan_temp_prof)
                    else:
                        mean_temp_prof = np.nanmean(ROs_lat.Temp.to_list(), axis=0)
                        RO_df_map.append(mean_temp_prof)
                    #RO_df_map.append(ROs_boxes_along_lat) 
                year_of_monthly_RO_composites.append(RO_df_map)
        RO_df_calendar.append(year_of_monthly_RO_composites)
    print(np.shape(RO_df_calendar))
    return(RO_df_calendar)

ROM_SAF_path_generic = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/{cdr_version}/profs/{satellite}/atm/'
ROM_SAF_RO_CDR = RO_calendar_creator(2001, 2017, 'cdr/v1.0', ROM_SAF_path_generic)
ROM_SAF_RO_ICDR = RO_calendar_creator(2017, 2023, 'icdr/v1-series', ROM_SAF_path_generic)
ROM_SAF_RO = np.concatenate([ROM_SAF_RO_CDR, ROM_SAF_RO_ICDR], axis=0)
np.save('/home/bdc2/aodhan/ROM_SAF/ROM_SAF_zm_monthlymean_092002_062022', ROM_SAF_RO)