### Python and Matlab code developed for gridding the Australian region XBT transect data and creating output files of the products


### Data sources and reference information
This repository is associated with the following data sources:
- Cowley, Rebecca; Krummel, Lisa; McMahon, Aidan; Hanstein, Craig; Parker, Ashley; Sloyan, Bernadette; Chapman, Chris; & Ridgway, Ken (2026): Australian XBT Ship of Opportunity gridded data collection. v1. CSIRO. Data Collection. https://data.csiro.au/collection/csiro:73479
- AODN (Australian Ocean Data Network) XBT Delayed Mode data collection. The IMOS XBT sub-Facility, including data access is described [here](https://imos.org.au/facility/ships-of-opportunity/expendable-bathythermographs). The code accesses the [THREDDS data service](https://thredds.aodn.org.au/thredds/catalog/IMOS/SOOP/SOOP-XBT/catalog.html).

The article describing the data collection and gridding methods is in preparation. For more information about the data collection, please see the CSIRO Data Collection page linked above.

## Quick start (recommended)

1. Create and activate a virtual environment (Python 3.11+ recommended):

```
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies (pip):

```
pip install -r requirements.txt
```

Note: For scientific packages (netCDF4, xarray, numpy) using conda can simplify installation of compiled dependencies:

```
conda create -n xbt_env python=3.11 -c conda-forge
conda activate xbt_env
conda install -c conda-forge netcdf4 xarray numpy pandas scipy beautifulsoup4 requests
```

3. Run the transect gridding script:

```
python transect_vertical_grid.py <input_directory_or_url> <output_directory> --v-grid-step 2 --max-depth 1000
```

- `input_directory_or_url` may be a local folder containing `.nc` files or any level of the [AODN SOOP XBT THREDDS catalog URL](https://thredds.aodn.org.au/thredds/catalog/IMOS/SOOP/SOOP-XBT/catalog.html).
- `output_directory` will receive the generated netCDF files.
- `--v-grid-step` is the depth interval for the vertical gridding in meters
- `--max-depth` is the maximum depth to grid the data to in meters

Note the code is set up to handle the AODN format of XBT data. It will need adjusting if a different input format is used.

## Notes for contributors and external users

- The repository includes a `requirements.txt` with conservative version bounds; for reproducible installs add a lockfile for your package manager.
- If you use PyCharm or another IDE and it cannot find local modules (e.g., `interp_gaussian.py`), mark the project folder as a Sources Root or ensure the interpreter's working directory includes the project root.
- The code includes defensive checks for empty inputs; if you see runtime errors when processing a dataset, please open an issue with a small reproducible example.

## MATLAB usage

The repository includes MATLAB utilities under `matlab/` for spatial gridding. To set system paths, the MATLAB scripts look for data and bathymetry files using the following strategy (in order):

- Environment variables: `XBT_DATA_DIR` (top-level data folder) and `XBT_OUT_DIR` (top-level output folder).
- Repo-relative candidate: `$(repo_root)/data/...` and `$(repo_root)/output/...`.
- For GEBCO bathymetry the `GEBCO_PATH` environment variable can point directly to the GEBCO netCDF file.

Examples (bash / zsh):

```bash
# set env vars to point to your local data locations
export XBT_DATA_DIR=/path/to/my/xbt_data
export XBT_OUT_DIR=/path/to/where/i/want/output
export GEBCO_PATH=/path/to/gebco_30sec.nc

# Run the main matlab control script from MATLAB command line or script
# Open MATLAB and set input variables:

data_dir = "/path/to/vertically/gridded/netcdf/files"
out_data_dir = "/path/to/output/folder"
bathy_fnm = "/path/to/gebco/bathymetry/file"
transects = {"IX01","PX30"} %example
remake = True % optional argument where True will remove all existing mat files made in previous gridding runs

# Run the spatial gridding code
create_matlab_grid(data_dir,out_data_dir, bathy_fnm, transects, remake)

```

If you prefer, place required files under `data/` in the repository root using the same structure expected by the scripts (e.g. `data/PX34/transect_files/` and `data/bath/gebco08_30sec.nc`).


## Optional output *.mat files from spatial gridding to netCDF:
In Python 3.11+

```
python matgrid2netcdf.py <matlab_file_path> <output_folder> [globals_file_path] [vars_file_path] [source_url]
```

- `matlab_file_path` may be a local folder containing `.mat` files from the spatial gridding step
- `output_folder` is a local folder for the output netCDF files
- `globals_file_path` is an optional argument containing the path to the netCDF globals attributes. Default is 'netcdfGlobalAtts_transect.csv' in the xbt-gridded-australia directory
- `vars_file_path`  is an optional argument containing the path to the netCDF variables and variable attributes. Default is 'netcdfVars_transect.csv' in the xbt-gridded-australia directory
- `source_url` optional, do not fill for this code