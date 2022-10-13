#!/usr/bin/env python3
"""
This code is designed to take synthetic TLS measurements that come from GPS-RO data 
in the ROM SAF record, and make monthly mean maps of those TLS measurements.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob

def to_bin_lat(y):
    lat_step = 2.5
    binned_lat = np.floor(y / lat_step) * lat_step
    return(binned_lat)

def to_bin_lon(x):
    lon_step = 2.5
    binned_lon = np.floor(x / lon_step) * lon_step
    return(binned_lon)

def TLS_maps_creator(base_path, start_year, end_year):
    cdr_TLS_maps = []
    for year in range(start_year, end_year):
        print(year)
        year_of_TLS_path = base_path + str(year) + '/*TLS*'
        TLS_yearly_files = glob.glob(year_of_TLS_path)
        one_year_TLS_files = []
        for sat_file in TLS_yearly_files:
            one_sat_one_year_TLS = np.load(sat_file, allow_pickle=True)
            one_year_TLS_files.append(one_sat_one_year_TLS)
        one_year_TLS_files = np.concatenate(one_year_TLS_files, axis=0)
        one_year_df = pd.DataFrame(one_year_TLS_files, columns=['Month', 'Lat', 'Lon', 'Date', 'TLS'])
        one_year_df['latbin'] = one_year_df.Lat.apply(to_bin_lat)
        one_year_df['lonbin'] = one_year_df.Lon.apply(to_bin_lon)
        year_of_TLS_maps = []
        for month in range(1, 13):
            one_month_df = one_year_df[one_year_df['Month']==month]
            mean_TLS_map = []
            for lat_idx in lats:
                one_month_df_at_lat = one_month_df[one_month_df['latbin'] == lat_idx]
                mean_TLS_at_lat = []
                for lon_idx in lons:
                    one_month_df_box = one_month_df_at_lat[one_month_df_at_lat['lonbin'] == lon_idx]
                    if one_month_df_box.size > 0:
                        mean_TLS = one_month_df_box.TLS.mean()
                    elif one_month_df_box.size == 0:
                        mean_TLS = np.NaN
                    else:
                        print('Size of df is invalid.')
                    mean_TLS_at_lat.append(mean_TLS)
                mean_TLS_map.append(mean_TLS_at_lat)
            year_of_TLS_maps.append(mean_TLS_map)
        cdr_TLS_maps.append(year_of_TLS_maps)
    return(np.array(cdr_TLS_maps))


cdr_base_path = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/cdr/v1.0/profs/*/atm/'
icdr_base_path = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/icdr/v1-series/profs/*/atm/'

lats = np.arange(-90, 90, 2.5)
lons = np.arange(-180, 180, 2.5)

cdr_TLS_maps = TLS_maps_creator(cdr_base_path, 2001, 2017)
icdr_TLS_maps = TLS_maps_creator(icdr_base_path, 2017, 2022)

calendar_TLS_maps = np.concatenate([cdr_TLS_maps, icdr_TLS_maps], axis=0)
np.save('/home/bdc2/aodhan/ROM_SAF/TLS_MonthlyMeanMaps/ROTLSMonthlyMeanMaps_2001_2022', calendar_TLS_maps)