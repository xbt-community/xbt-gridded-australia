# import a parquet file and write it to a netcdf file
from datetime import datetime
import itertools
import os
from time import strftime, gmtime

import numpy as np
import pandas as pd
from netCDF4 import Dataset, date2num
from utils import read_variables_config, read_globals_config

def create_filename_output(df, source_url=None):

    # name format : IMOS_SOOP-XBT_T_20091223T140300Z_PX02_FV02_2025-02-01.nc
    # alternatively for CSIRO files:
    # PX02-202502-1.nc
    # where IMOS_SOOP-XBT_T is fixed
    # 20091223T140300Z is the time of first profile in the transect
    # PX02 is the SOOP line label
    # FV02 is the file version
    # 2025-02 is the transect ID

    # fv = 'FV02'
    #
    # filename = 'IMOS_SOOP-XBT_T_%s_%s_%s_ID-%s' % (
    #     min(df['TIME']).strftime('%Y%m%dT%H%M%SZ'), df['SOOP_line'][0], fv,
    #     df['transect_id'][0])
    # for CSIRO format, uncomment the following line and comment the previous one
    filename = '%s' % df['transect_id'][0]

    mode_suffix = ''
    if isinstance(source_url, str):
        source_url_upper = source_url.upper()
        if 'DELAYED' in source_url_upper:
            mode_suffix = '_D'
        elif 'REALTIME' in source_url_upper:
            mode_suffix = '_R'

    filename = f"{filename}{mode_suffix}"

    return filename


def write_vert_grid_nc(output_folder, transect_df, data_df, data_df_uncorrected=None, data_df_incl_surface=None, data_df_incl_surface_uncorrected=None, globals_file_path='netcdfGlobalAtts.csv', vars_file_path='netcdfVars.csv', source_url=None):
    """output the binned data to the IMOS format netcdf version
    :param output_folder: the folder to write the netcdf file to
    :param transect_df: data frame with transect location and cruise information
    :param data_df: data frame with binned CH14-corrected TEMP data and DEPTH
    :param data_df_uncorrected: data frame with binned uncorrected TEMP data, same shape as data_df
    :param data_df_incl_surface: data frame with binned CH14-corrected TEMP data including surface, same shape as data_df
    :param data_df_incl_surface_uncorrected: data frame with binned uncorrected TEMP data including surface, same shape as data_df
    :param globals_file_path: path to the global attributes config file
    :param vars_file_path: path to the variable attributes config file
    :return: None
    """
    # get the soop line label from the transect_df and if a folder does not exist with that name in the output_folder, create it
    soop_line_label = transect_df['SOOP_line'].iloc[0]
    # if the output folder name already includes the soop line folder, do not add it again
    if soop_line_label in output_folder:
        print('Output folder for SOOP line %s already exists, writing to that folder' % soop_line_label)
    else:
        output_folder = os.path.join(output_folder, soop_line_label)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    # now begin write out to new format
    netcdf_filepath = os.path.join(output_folder, "%s.nc" % create_filename_output(transect_df, source_url=source_url))
    print('Creating output %s' % netcdf_filepath)

    # read the variables config file
    vars = read_variables_config(vars_file_path)

    # get a list of the dimensions from the vars DataFrame
    dimensions = set()
    for dims in vars['Dimensions'].dropna():
        for dim in dims.split(','):
            dimensions.add(dim.strip())
    # keep the unique dimensions
    dimensions = list(dimensions)

    # read the global attributes config file
    globals_list = read_globals_config(globals_file_path)

    # Identify attribute columns starting with 'att_'
    att_cols = [col for col in vars.columns if col.startswith('att_')]
    # remove the 'att_' prefix from the attribute columns
    att_labels = [col.replace('att_', '') for col in att_cols]

    with Dataset(netcdf_filepath, "w", format="NETCDF4") as output_netcdf_obj:
        # Create the dimensions from the size of the data DataFrame
        depth_data = data_df.index.values

        # create the dimensions in the NetCDF file
        for dim in dimensions:
            if dim == 'DEPTH':
                output_netcdf_obj.createDimension('DEPTH', len(depth_data))
            elif dim == 'TIME':
                output_netcdf_obj.createDimension('TIME', None)
            elif dim.startswith('str'):
                output_netcdf_obj.createDimension(dim, int(dim.replace('str', '')))
            else:
                # use the dimension name as is
                output_netcdf_obj.createDimension(dim, len(transect_df[dim].values))


        # Create the variables from the vars Dataframe
        for var_name in vars['variable_name']:
            var_info = vars[vars['variable_name'] == var_name].iloc[0]
            if not pd.isna(var_info['Dimensions']) and var_info['Dimensions'] != '':
                # get dimensions from the Dimensions column in the vars DataFrame
                var_dims = var_info['Dimensions']
                var_dims = tuple(var_dims.split(',')) if len(var_dims) > 1 else (var_dims,)
                if not np.isnan(var_info['fillValue']):
                    output_netcdf_obj.createVariable(var_name, var_info['variable_type'], var_dims, fill_value=np.float32(var_info['fillValue']))
                else:
                    # no fill value specified, create variable without fill_value
                    output_netcdf_obj.createVariable(var_name, var_info['variable_type'], var_dims)  
            else:
                # if no Dimensions specified, create variable without dimensions
                if not np.isnan(var_info['fillValue']):
                    output_netcdf_obj.createVariable(var_name, var_info['variable_type'], fill_value=np.float32(var_info['fillValue']))
                else:
                    output_netcdf_obj.createVariable(var_name, var_info['variable_type'])

        # Build TEMP matrix once and fill NaNs without mutating the input dataframe.
        temp_data = data_df.to_numpy(dtype=np.float32, copy=True).T
        np.nan_to_num(temp_data, copy=False, nan=np.float32(vars[vars['variable_name'] == 'TEMP'].iloc[0]['fillValue']))

        # uncorrected TEMP is left empty if not supplied.
        temp_data_uncorrected = data_df_uncorrected.to_numpy(dtype=np.float32, copy=True).T
        np.nan_to_num(temp_data_uncorrected, copy=False, nan=np.float32(vars[vars['variable_name'] == 'TEMP_uncorrected'].iloc[0]['fillValue']))

        # TEMP including surface
        temp_data_incl_surface = data_df_incl_surface.to_numpy(dtype=np.float32, copy=True).T
        np.nan_to_num(temp_data_incl_surface, copy=False, nan=np.float32(vars[vars['variable_name'] == 'TEMP_including_surface'].iloc[0]['fillValue']))

        # TEMP including surface uncorrected
        temp_data_incl_surface_uncorrected = data_df_incl_surface_uncorrected.to_numpy(dtype=np.float32, copy=True).T
        np.nan_to_num(temp_data_incl_surface_uncorrected, copy=False, nan=np.float32(vars[vars['variable_name'] == 'TEMP_including_surface_uncorrected'].iloc[0]['fillValue']))

        # set variable attributes
        for var_name in vars['variable_name']:
            var_obj = output_netcdf_obj.variables[var_name]
            var_info = vars[vars['variable_name'] == var_name].iloc[0]
            # set attributes from the att_* columns
            for att_label, att_col in zip(att_labels, att_cols):
                att_value = var_info[att_col]
                if pd.isna(att_value):
                    continue
                var_obj.setncattr(att_label, att_value)

        # append the data to the file
        for var_name in vars['variable_name']:
            # if the var_name is in the transect_df, get the data from the transect_df. if not, use the depth_data and temp_data arrays as appropriate
            if var_name not in transect_df.columns:
                if var_name == 'DEPTH':
                    output_netcdf_obj.variables[var_name][:] = depth_data
                elif var_name == 'TEMP':
                    output_netcdf_obj.variables[var_name][:] = temp_data
                elif var_name == 'TEMP_uncorrected':
                    output_netcdf_obj.variables[var_name][:] = temp_data_uncorrected
                elif var_name == 'TEMP_including_surface':
                    output_netcdf_obj.variables[var_name][:] = temp_data_incl_surface
                elif var_name == 'TEMP_including_surface_uncorrected':
                    output_netcdf_obj.variables[var_name][:] = temp_data_incl_surface_uncorrected
                continue
            if pd.api.types.is_datetime64_any_dtype(transect_df[var_name]):
                output_netcdf_obj.variables[var_name][:] = date2num(pd.to_datetime(transect_df[var_name]).dt.to_pydatetime(),
                                                                   units=output_netcdf_obj.variables[var_name].units,
                                                                   calendar=output_netcdf_obj.variables[var_name].calendar)
            elif isinstance(transect_df[var_name].iloc[0], str):
                 #the df['filename'] as a string variable in the netcdf file
                # create a padded array of 100 characters
                padded_array = np.full((len(transect_df['filename']), 100), ' ', dtype='S1')
                for i, filename in enumerate(transect_df['filename']):
                    padded_array[i, :len(filename)] = list(filename)
                # assign the padded values to the variable
                output_netcdf_obj.variables[var_name][:] = padded_array 
            else:
                output_netcdf_obj.variables[var_name][:] = transect_df[var_name].values

        # add geospatial information to global attributes dictionary
        globals_list['geospatial_lat_max'] = transect_df['LATITUDE'].max()
        globals_list['geospatial_lat_min'] = transect_df['LATITUDE'].min()
        globals_list['geospatial_lon_max'] = transect_df['LONGITUDE'].max()
        globals_list['geospatial_lon_min'] = transect_df['LONGITUDE'].min()
        globals_list['geospatial_vertical_max'] = max(depth_data)
        globals_list['geospatial_vertical_min'] = min(depth_data)
        # add time coverage information to global attributes dictionary
        globals_list['time_coverage_start'] = min(transect_df['TIME']).strftime("%Y-%m-%dT%H:%M:%SZ")
        globals_list['time_coverage_end'] = max(transect_df['TIME']).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Add date created to the global attributes
        utctime = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        globals_list['date_created'] = utctime

        # set the SOOP_line_label, SOOP_line_description and transect_id global attributes
        globals_list['SOOP_line_label'] = transect_df['SOOP_line'].iloc[0]
        globals_list['SOOP_line_description'] = transect_df['SOOP_line_description'].iloc[0]
        globals_list['transect_id'] = transect_df['transect_id'].iloc[0]
        globals_list['Cruise_ID'] = transect_df['Cruise_ID'].iloc[0]

        # set the global attributes where the index is the attribute name
        for att_name, att_value in globals_list.items():
            # if the global_att[att_name] is None, replace with 'Unknown'
            if pd.isna(att_value):
                att_value = 'Unknown'
            output_netcdf_obj.setncattr(att_name, att_value)
