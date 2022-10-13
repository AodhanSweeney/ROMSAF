#!/usr/bin/env python3
"""
This code puts the STAR TLS Temperature Climate Data Record (TCDR) into a np file
that can be used to compare to the RO data more easily.
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

lats = np.arange(-90, 90, 2.5)
weights = np.cos(np.deg2rad(lats+1.25))

TLS_TCDR = xr.open_dataset('/usb/BM_amsu_atms/TLS/NESDIS-STAR_TCDR_RTLS_S200209_E202110_C20211116.nc')
nan_month = np.empty(np.shape(TLS_TCDR.tcdr_MSU_AMSUA_anomaly_channel_09.values[0]))
nan_month[:] = np.NaN
eight_nan_months = np.broadcast_to(nan_month, (8,72,144))
two_nan_months = np.broadcast_to(nan_month, (2,72,144))
TLS_anoms = TLS_TCDR.tcdr_MSU_AMSUA_anomaly_channel_09.values
TLS_anoms_nov_2003 = np.nanmean([TLS_anoms[13], TLS_anoms[14]], axis=0)
TLS_anoms = np.insert(TLS_anoms, 14, TLS_anoms_nov_2003, axis=0)
TLS_anoms_wnans = np.concatenate([eight_nan_months, TLS_anoms], axis=0)
TLS_anoms_wnans = np.concatenate([TLS_anoms_wnans, two_nan_months], axis=0)
TLS_anoms_calendar = np.reshape(TLS_anoms_wnans, (20,12,72,144))
np.save('/home/bdc2/aodhan/ROM_SAF/TLS_MonthlyMeanMaps/STARTLSMonthlyMeanAnomalyMaps_2002_2022', TLS_anoms_calendar)
