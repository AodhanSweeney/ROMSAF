#!/usr/bin/env python3
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import xarray as xr
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

def ERA5regridder(ERA5map):
    """
    Reanalysis is put initially on a 73x144 grid, we want 72x144.
    Whatever the dimmensions of the input array, latitude must be first axis.
    Output will have different dimensions so axes will likely need to be swapped.
    """
    map_regridded = []
    for i in range(1,73):
        regridlat = np.nanmean(ERA5map[i-1:i+1], axis=0)
        map_regridded.append(regridlat)
    return(np.array(map_regridded))

def ERA5TLScreator(ERA5MonthlyMeanTempProfs):
    latitudes = ERA5MonthlyMeanTempProfs.latitude
    longitudes = ERA5MonthlyMeanTempProfs.longitude
    times = ERA5MonthlyMeanTempProfs.time
    p_level = ERA5MonthlyMeanTempProfs.level
    p_level_positive_z = np.flip(p_level)
    ERA5MonthlyMeanTempProfs_np = ERA5MonthlyMeanTempProfs.to_array()[0]
    
    #Import the weighting function and its respective pressure levels
    amsu_channel9_df = pd.read_csv('/home/disk/p/aodhan/ROMSAF/AMSU_channel9_2022_pressure.csv')
    total = amsu_channel9_df.Weight.sum()
    amsu_channel9_df = amsu_channel9_df[amsu_channel9_df['Pressure'] > 2]
    amsu_channel9_df = amsu_channel9_df[amsu_channel9_df['Pressure'] < 400]
    pressure_levels_correct_range_logrithmic = np.geomspace(amsu_channel9_df.Pressure.to_list()[-1], amsu_channel9_df.Pressure.to_list()[0], num=100)

    #weighting function needs to be interpolated to this new set of pressure levels
    weighting_func_interpolater = CubicSpline(amsu_channel9_df.Pressure.to_list(), amsu_channel9_df.Weight.to_list())
    pressure_levels_correct_range_logrithmic_inverse_z = np.flip(pressure_levels_correct_range_logrithmic)
    weighting_func_logrithmic_inverse_z = weighting_func_interpolater(pressure_levels_correct_range_logrithmic_inverse_z)
    weighting_func_logrithmic_positive_z = np.flip(weighting_func_logrithmic_inverse_z)    
        
    ERA5TLScalendar = []
    for month in range(0, len(times)):
        ERA5_MonthlyMap = []
        for lat in range(0, len(latitudes)):
            ERA5_at_lat = []
            for lon in range(0, len(longitudes)):
                ERA5_inbox = ERA5MonthlyMeanTempProfs_np[month, :, lat, lon]
                ERA5TempProfile = ERA5_inbox - 273.15
                #interpolate using a cubic spline
                temperature_interpolater = CubicSpline(p_level, ERA5TempProfile)
                era5_temp_prof_interp = temperature_interpolater(pressure_levels_correct_range_logrithmic_inverse_z)
                
                #flip the interpolated profile from 2.9hPa-->351hPa to 351hPa-->2.9hPa
                temp_prof_interp_positive_z = np.flip(era5_temp_prof_interp)
                temp_prof_interp_positive_z
                #Find TLS
                ERA5_TLS = TLS(temp_prof_interp_positive_z, 
                               weighting_func_logrithmic_positive_z, 
                               pressure_levels_correct_range_logrithmic)
                ERA5_at_lat.append(ERA5_TLS)
            ERA5_MonthlyMap.append(ERA5_at_lat)
        ERA5_MonthlyMap_regrid = ERA5regridder(ERA5_MonthlyMap)
        ERA5TLScalendar.append(ERA5_MonthlyMap_regrid)
    return(np.array(ERA5TLScalendar))

# Get TLS data
ERA5MonthlyMeanTempProfs = xr.open_dataset('/home/disk/pna2/aodhan/ERA5_MonthlyMeanTempProf_2p5by2p5.nc')
ERA5TLSMapCreator = ERA5TLScreator(ERA5MonthlyMeanTempProfs)
ERA5TLSMapCreator_calendar = np.reshape(ERA5TLSMapCreator, (21,12,72,144))
np.save('/home/bdc2/aodhan/ROM_SAF/TLS_MonthlyMeanMaps/ERA5TLSMaps_Jan2001_Dec2021', ERA5TLSMapCreator_calendar)

# Get profile data
ERA5MonthlyMeanTempProfs = xr.open_dataset('/home/disk/pna2/aodhan/ERA5_MonthlyMeanTempProf_2p5by2p5.nc').to_array()[0] 
ERA5MonthlyMeanTempProfs_swapedaxes = np.swapaxes(ERA5MonthlyMeanTempProfs, 0,2)
ERA5MonthlyMeanTempProfs_regridded = ERA5regridder(ERA5MonthlyMeanTempProfs_swapedaxes)
ERA5MonthlyMeanTempProfs_regridded = np.swapaxes(ERA5MonthlyMeanTempProfs_regridded, 0,2)
ERA5ProfMapCreator_calendar = np.reshape(ERA5MonthlyMeanTempProfs_regridded, (21,12,19,72,144))
np.save('/home/bdc2/aodhan/ROM_SAF/TLS_MonthlyMeanMaps/ERA5ProfMaps_Jan2001_Dec2021', ERA5ProfMapCreator_calendar)

