# Functions to import matlab files containing the spatially gridded XBT data. Then
# output the data to netcdf using the write2netcdf.py functions
# Bec Cowley, 12 October, 2026

def write_vert_grid_nc(output_folder, transect_df, data_df, data_df_uncorrected=None, globals_file_path='netcdfGlobalAtts.csv', vars_file_path='netcdfVars.csv', source_url=None):
    from write2netcdf import write_vert_grid_nc as write_func
    write_func(output_folder, transect_df, data_df, data_df_uncorrected=data_df_uncorrected, globals_file_path=globals_file_path, vars_file_path=vars_file_path, source_url=source_url)

def import_matlab_and_write_to_netcdf(matlab_file_path, output_folder, globals_file_path='netcdfGlobalAtts.csv', vars_file_path='netcdfVars.csv', source_url=None):
    """Import a MATLAB file containing spatially gridded XBT data and write it to a NetCDF file.
    :param matlab_file_path: path to the MATLAB file to import
    :param output_folder: the folder to write the NetCDF file to
    :param globals_file_path: path to the global attributes config file
    :param vars_file_path: path to the variable attributes config file
    :param globals_file_path: path to the CSV file containing global attributes for the NetCDF file
    :param vars_file_path: path to the CSV file containing variable attributes for the NetCDF file
    :param source_url: optional source URL for the data
    :return: None
    """
    import scipy.io
    import pandas as pd
    # Ensure globals_file_path and vars_file_path are passed to the function
    if globals_file_path is None:
        globals_file_path = 'netcdfGlobalAtts_transect.csv'
    if vars_file_path is None:
        vars_file_path = 'netcdfVars_transect.csv'

    # look in the matlab_file_path and subdirectories to find *_all.mat files and keep a record of them
    found_files = []
    import os
    if os.path.isdir(matlab_file_path):
        for root, dirs, files in os.walk(matlab_file_path):
            for file in files:
                if file.endswith('_all.mat'):
                    matlab_file_path = os.path.join(root, file)
                    found_files.append(matlab_file_path)
                    continue
            else:
                continue

    for file in found_files:
        matlab_file_path = file
        # Load the MATLAB file
        mat_data = scipy.io.loadmat(matlab_file_path)

        # Call the function to write the data to NetCDF
        from write2netcdf import write_spatial_grid_nc as write_func
        write_func(output_folder, mat_data, globals_file_path=globals_file_path, vars_file_path=vars_file_path, source_url=source_url)

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: matgrid2netcdf.py <matlab_file_path> <output_folder> [globals_file_path] [vars_file_path] [source_url]")
        sys.exit(1)
    matlab_file_path = sys.argv[1]
    output_folder = sys.argv[2]
    globals_file_path = sys.argv[3] if len(sys.argv) > 3 else 'netcdfGlobalAtts_transect.csv'
    vars_file_path = sys.argv[4] if len(sys.argv) > 4 else 'netcdfVars_transect.csv'
    source_url = sys.argv[5] if len(sys.argv) > 5 else None
    import_matlab_and_write_to_netcdf(matlab_file_path, output_folder, globals_file_path, vars_file_path, source_url)

if __name__ == "__main__":
    main()