#!/usr/bin/env python3
import numpy as np
import pandas as pd
from scipy import stats
import glob

def to_bin_lat(y):
    lat_step = 2.5
    binned_lat = np.floor(y / lat_step) * lat_step
    return(binned_lat)

def to_bin_lon(x):
    lon_step = 2.5
    binned_lon = np.floor(x / lon_step) * lon_step
    return(binned_lon)

def lon_rewrapper(lon):
    if lon > 180:
        new_lon = -360 + lon
        return(new_lon)
    else:
        return(lon)

path_to_data = glob.glob('/home/bdc2/aodhan/ROM_SAF/collocations/*_ERA_5_colocated_occultations.npy')
collocation_arrays = [np.load(path_to_data[i], allow_pickle=True) for i in range(0, len(path_to_data))]
collocation_concatenation = np.concatenate(collocation_arrays, axis=0)
collocation_df = pd.DataFrame(collocation_concatenation, 
                              columns=['Day', 'Hour', 'Month', 'Year', 'Lat', 'Lon', 'TLS', 'Tprof'])
collocation_df['Lon'] = collocation_df.Lon.apply(lon_rewrapper)
collocation_df['latbin'] = collocation_df.Lat.apply(to_bin_lat)
collocation_df['lonbin'] = collocation_df.Lon.apply(to_bin_lon)
collocation_df.Year = collocation_df.Year.astype(int)

lats = np.arange(-90, 90, 2.5)
lons = np.arange(-180, 180, 2.5)

TLS_calendar = []
Prof_calendar = []
for year in range(2001, 2023):
    print('Year: ', year)
    one_year_df = collocation_df[collocation_df['Year'] == year]
    year_of_TLS_maps = []
    year_of_profile_maps = []
    for month in range(1, 13):
        print('Month: ', month)
        one_month_df = one_year_df[one_year_df['Month'] == month]
        mean_TLS_map = []
        mean_prof_map = []
        for lat_idx in lats:
            one_month_df_at_lat = one_month_df[one_month_df['latbin'] == lat_idx]
            mean_TLS_at_lat = []
            mean_prof_at_lat = []
            for lon_idx in lons:
                one_month_df_box = one_month_df_at_lat[one_month_df_at_lat['lonbin'] == lon_idx]
                if one_month_df_box.size > 0:
                    mean_TLS = one_month_df_box.TLS.mean()
                    mean_prof = one_month_df_box.Tprof.mean()
                elif one_month_df_box.size == 0:
                    mean_TLS = np.NaN
                    mean_prof = np.empty(19)
                    mean_prof[:] = np.NaN
                else:
                    print('Size of df is invalid.')
                mean_TLS_at_lat.append(mean_TLS)
                mean_prof_at_lat.append(mean_prof)
            mean_TLS_map.append(mean_TLS_at_lat)
            mean_prof_map.append(mean_prof_at_lat)
        year_of_TLS_maps.append(mean_TLS_map)
        year_of_profile_maps.append(mean_prof_map)
    TLS_calendar.append(year_of_TLS_maps)
    Prof_calendar.append(year_of_profile_maps)

np.save('/home/bdc2/aodhan/ROM_SAF/TLS_MonthlyMeanMaps/TLSERA5collocationsGPS_2001_2022', TLS_calendar)
np.save('/home/bdc2/aodhan/ROM_SAF/Profiles_MonthlyMeanMaps/ProfERA5collocationsGPS_2001_2022', Prof_calendar)