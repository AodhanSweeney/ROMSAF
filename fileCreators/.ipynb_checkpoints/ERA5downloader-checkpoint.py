#!/usr/bin/env python3
"""
This script downloads monthly mean ERA5 data. Converting the hourly data
into something that could be uploaded was taking too long.

This script can be adapted to download ERA5 reanalysis for other needs 
besides what is currently listed.
"""

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-pressure-levels-monthly-means',
    {
        'format': 'netcdf',
        'product_type': 'monthly_averaged_reanalysis',
        'variable': 'temperature',
        'pressure_level': [
            '2', '3', '5',
            '7', '10', '20',
            '30', '50', '70',
            '100', '125', '150',
            '175', '200', '225',
            '250', '300', '350',
            '400',
        ],
        'year': [
            '2001', '2002', '2003',
            '2004', '2005', '2006',
            '2007', '2008', '2009',
            '2010', '2011', '2012',
            '2013', '2014', '2015',
            '2016', '2017', '2018',
            '2019', '2020', '2021',
        ],
        'time': '00:00',
        'month': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
        ],
        'grid':['2.5', '2.5'],
    },
    '/home/disk/pna2/aodhan/ERA5_MonthlyMeanTempProf_2p5by2p5.nc')