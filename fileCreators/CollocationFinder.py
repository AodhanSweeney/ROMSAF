#!/usr/bin/env python3
from netCDF4 import Dataset
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.interpolate import CubicSpline
from datetime import datetime
from datetime import date, timedelta
import glob as glob
import cdsapi
import sys
import matplotlib.pyplot as plt
import time as time

months_as_strings = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 
                     'august', 'september', 'october', 'november', 'december']

def TLS(temp, weight, levels):
    TpWp = np.multiply(temp, weight)
    integral_top = np.trapz(TpWp, levels)
    integral_bottom = np.trapz(weight, levels)
    return(integral_top/integral_bottom)
    
def find_idx_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def day_finder(row):
    date = str(row.Date)
    day_of_month = int(date[8:10])
    hour_of_day = int(date[11:13])
    return([day_of_month, hour_of_day])

def colocations(path_to_ERA5_data, year_string_idx, month):
    path_to_monthly_ERA5_mean = Path(path_to_ERA5_data)
    month_of_data_ds = Dataset(path_to_monthly_ERA5_mean)
    hours_since_1900 = int(month_of_data_ds['time'][0]) 
    days_since_1900 = int(hours_since_1900/24)
    start = date(1900,1,1) #ERA-5 data counts from 1900  
    delta = timedelta(days_since_1900)  # delta is the time since 1900
    offset = str(start + delta)  # combine the two to get actual time you want
    date_thing = datetime.strptime(offset, '%Y-%m-%d')
    day_of_year = date.timetuple(date_thing).tm_yday
    year = offset[:4]
    print('Year: ', year)
    latitudes = month_of_data_ds['latitude'][:]
    longitudes = month_of_data_ds['longitude'][:]
    times = month_of_data_ds['time'][:]
    days_in_month = int(len(times)/24)
    utc_times = times%24
    p_level = month_of_data_ds['level'][:]
    p_level_positive_z = np.flip(p_level)
    hour_array = np.arange(0,24)
    
    #Import the weighting function and its respective pressure levels
    amsu_channel9_df = pd.read_csv('/home/disk/p/aodhan/ROM_SAF/AMSU_channel9_2022_pressure.csv')
    total = amsu_channel9_df.Weight.sum()
    amsu_channel9_df = amsu_channel9_df[amsu_channel9_df['Pressure'] > 2]
    amsu_channel9_df = amsu_channel9_df[amsu_channel9_df['Pressure'] < 400]
    pressure_levels_correct_range_logrithmic = np.geomspace(amsu_channel9_df.Pressure.to_list()[-1], amsu_channel9_df.Pressure.to_list()[0], num=100)

    #weighting function needs to be interpolated to this new set of pressure levels
    weighting_func_interpolater = CubicSpline(amsu_channel9_df.Pressure.to_list(), amsu_channel9_df.Weight.to_list())
    pressure_levels_correct_range_logrithmic_inverse_z = np.flip(pressure_levels_correct_range_logrithmic)
    weighting_func_logrithmic_inverse_z = weighting_func_interpolater(pressure_levels_correct_range_logrithmic_inverse_z)
    weighting_func_logrithmic_positive_z = np.flip(weighting_func_logrithmic_inverse_z)    
    
    #Now we need to load TLS data
    #base_path = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/cdr/v1.0/profs/*/atm/'
    base_path = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/icdr/v1-series/profs/*/atm/'
    year_of_TLS_path = base_path + year_string_idx + '/*TLS*'
    TLS_yearly_files = glob.glob(year_of_TLS_path)
    one_year_TLS_files = []
    for sat_file in TLS_yearly_files:
        one_sat_one_year_TLS = np.load(sat_file, allow_pickle=True)
        one_year_TLS_files.append(one_sat_one_year_TLS)
    one_year_TLS_files = np.concatenate(one_year_TLS_files, axis=0)
    one_year_df = pd.DataFrame(one_year_TLS_files, columns=['Month', 'Lat', 'Lon', 'Date', 'TLS'])
    one_year_one_month_df = one_year_df[one_year_df['Month'] == month]
    print('Month: ', month)
    one_year_one_month_df[['Day', 'Hour']] = one_year_one_month_df.apply(day_finder, axis=1, result_type='expand')
    ERA_5_monthly_mean_synthetic_TLS_map = []
    for t in range(0, days_in_month):
        day_start = t*24
        day_end = day_start+24
        day_of_month = t + 1
        print('Day: ', day_of_month)
        day_of_data = month_of_data_ds['t'][day_start:day_end]
        day_of_gpsro = one_year_one_month_df[one_year_one_month_df['Day'] == day_of_month]
        for h_idx in range(0, 24):
            hour = hour_array[h_idx]
            hour_of_occultations = day_of_gpsro[day_of_gpsro['Hour'] == hour]
            hour_of_occultations = hour_of_occultations.reset_index(drop=True)
            hour_of_ERA5 = day_of_data[h_idx]

            for occultation in hour_of_occultations.iterrows():
                occultation_instance = occultation[1]
                occult_lat = occultation_instance.Lat
                occult_lon = occultation_instance.Lon
                closest_lat_idx = find_idx_nearest(latitudes, occult_lat)
                if occult_lon >= 0:
                    closest_lon_idx = find_idx_nearest(longitudes, occult_lon)
                elif occult_lon < 0:
                    closest_lon_idx = find_idx_nearest(longitudes, 360 + occult_lon)
                
                #get closest profile in ERA-5 that corresponds to the occultation
                ERA5_colocated_temp_prof = hour_of_ERA5[:,closest_lat_idx,closest_lon_idx] - 273.15

                #interpolate using a cubic spline
                temperature_interpolater = CubicSpline(p_level, ERA5_colocated_temp_prof)
                era5_temp_prof_interp = temperature_interpolater(pressure_levels_correct_range_logrithmic_inverse_z)
                
                #flip the interpolated profile from 2.9hPa-->351hPa to 351hPa-->2.9hPa
                temp_prof_interp_positive_z = np.flip(era5_temp_prof_interp)
                
                #Find TLS temp
                ERA5_TLS_temp = TLS(temp_prof_interp_positive_z, 
                                             weighting_func_logrithmic_positive_z, 
                                             pressure_levels_correct_range_logrithmic)
                ERA5_LT_TLS_temp = [day_of_month, hour, month, year, latitudes[closest_lat_idx], 
                                    longitudes[closest_lon_idx], ERA5_TLS_temp, ERA5_colocated_temp_prof]
                ERA_5_monthly_mean_synthetic_TLS_map.append(ERA5_LT_TLS_temp)

    monthly_synthetic_TLS_map = pd.DataFrame(ERA_5_monthly_mean_synthetic_TLS_map, columns=['Day', 'Hour','Month', 'Year', 'Lat', 'Lon', 'TLS', 'Tprof'])
    np.save('/home/bdc2/aodhan/ROM_SAF/collocations/{monthString}_{year_idx}_ERA_5_colocated_occultations'.format(monthString=str(month),
        year_idx=year_string_idx), monthly_synthetic_TLS_map)

for year in range(2017, 2023):
    for month in range(1, 13):
        try:
            year_string_idx = str(year)
            path_to_colocations = '/home/disk/pna2/aodhan/ERA5_hourly_data/{monthString}_{year_idx}_ERA5.nc'.format(
                monthString=months_as_strings[month-1], year_idx=year_string_idx)
            colocations(path_to_colocations, year_string_idx, month)
        except:
            continue
