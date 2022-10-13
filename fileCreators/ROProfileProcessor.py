#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import xarray as xr
from scipy.interpolate import interp1d
from netCDF4 import Dataset
dr_versions = ['cdr', 'icdr']
cdr_satellites = ['champ', 'cosmic', 'grace', 'metop']
icdr_satellites = ['metop']
ROM_SAF_path_generic = '/home/bdc2/aodhan/ROM_SAF/www.romsaf.org/pub/{cdr_version}/profs/{satellite}/atm/'
heights = np.linspace(5,35,301)*1000
month_strings = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

ROM_SAF_temp_profiles = []
for dr in dr_versions:
    if dr == 'cdr':
        dr_string = 'cdr/v1.0'
        satellites = cdr_satellites
    elif dr == 'icdr':
        dr_string = 'icdr/v1-series'
        satellites = icdr_satellites
    for sat in satellites:
        print('Satellite: ', sat)
        ROM_SAF_path_satellite = ROM_SAF_path_generic.format(cdr_version=dr_string, satellite=sat)
        for year in range(2001, 2023):
            print('Year: ', str(year))
            for month in month_strings:
                RO_daily_data_paths = glob.glob(ROM_SAF_path_satellite + str(year) 
                                                + '/' + str(year) + '-' + month + '*')
                if len(RO_daily_data_paths) == 0:
                    print('No data for {month} of {year}'.format(month=month, year=str(year)))
                    continue
                month_of_RO_data = []
                for day in RO_daily_data_paths:
                    datafiles_of_day = glob.glob(day + '/*')
                    
                    for datafile in datafiles_of_day:
                        if datafile[-11:] == 'non-nominal':
                            continue
                        else:
                            # extract temp and alt info from RO
                            RO = Dataset(datafile)
                            dry_temp = RO.variables['dry_temp'][0]
                            alt = RO.variables['alt_refrac'][0]
                            # above is the height according to page 51/51 at url below
                            # https://www.romsaf.org/product_documents/romsaf_pum.pdf 
                            
                            # find RO location
                            lat = np.array(RO.variables['lat_tp'])
                            lon = np.array(RO.variables['lon_tp'])
                            altm17 = np.abs(alt-17000)
                            idx_17km = np.nanargmin(altm17) # 17 Km tangent point
                            lat_17km = lat[0][idx_17km]
                            lon_17km = lon[0][idx_17km]
                            
                            # interpolate temperature profile
                            temp_interp = interp1d(alt, dry_temp, kind='cubic', bounds_error=False)
                            temp_100m_spacing = temp_interp(heights)

                            # append data
                            month_of_RO_data.append([lat_17km, lon_17km, temp_100m_spacing])
                # save month of data
                file_name = 'DryTempProf_{satellite}_{month}_{year}_5_35km'.format(satellite=sat, month=month, year=str(year))
                file_path = ROM_SAF_path_satellite + str(year) + '/' + file_name
                np.save(file_path, month_of_RO_data)
