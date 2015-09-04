
import os, sys, argparse
import datetime
from git import Repo
from netCDF4 import Dataset


"""
Taken from the Software Carpentry oceanography lesson by Damien Irving
Full lesson: http://damienirving.github.io/capstone-oceanography/index.html
Script is from "Putting It All Together":
http://damienirving.github.io/capstone-oceanography/03-data-provenance.html
"""


def calc_speed(u, v):
    """Calculate the speed"""

    speed = (u**2 + v**2)**0.5

    return speed


def copy_dimensions(infile, outfile):
    """Copy the dimensions of the infile to the outfile"""

    for dimName, dimData in infile.dimensions.iteritems():
        outfile.createDimension(dimName, len(dimData))


def copy_variables(infile, outfile):
    """Create variables corresponding to the file dimensions
    by copying from infile"""

    for var_name in ['TIME', 'LATITUDE', 'LONGITUDE']:
        varin = infile.variables[var_name]
        outVar = outfile.createVariable(var_name, varin.datatype,
                                        varin.dimensions,
                                        fill_value=varin._FillValue)
        outVar[:] = varin[:]

        var_atts = {}
        for att in varin.ncattrs():
            if not att == '_FillValue':
                var_atts[att] = eval('varin.'+att)
        outVar.setncatts(var_atts)


def create_history():
    """Create the new entry for the global history file attribute"""

    time_stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    exe = sys.executable
    args = " ".join(sys.argv)
    git_hash = Repo(os.getcwd()).heads[0].commit

    return """%s: %s %s (Git hash: %s)""" %(time_stamp, exe, args, str(git_hash)[0:7])


def read_data(ifile, uVar, vVar):
    """Read data from ifile corresponding to the U and V variable"""

    input_DATA = Dataset(ifile)
    uData = input_DATA.variables[uVar][:]
    vData = input_DATA.variables[vVar][:]

    return uData, vData, input_DATA


def set_global_atts(infile, outfile):
    """Set the global attributes for outfile.

    Note that the global attributes are simply copied from
    infile and the history attribute updated accordingly.

    """

    global_atts = {}
    for att in infile.ncattrs():
        global_atts[att] = eval('infile.'+att)

    new_history = create_history()
    global_atts['history'] = """%s\n%s""" %(new_history,  global_atts['history'])
    outfile.setncatts(global_atts)


def write_speed(infile, outfile, spData):
    """Write the current speed data to outfile"""

    u = infile.variables['UCUR']
    spcur = outfile.createVariable('SPCUR', u.datatype, u.dimensions, fill_value=u._FillValue)
    spcur[:,:,:] = spData

    spcur.standard_name = 'sea_water_speed'
    spcur.long_name = 'sea water speed'
    spcur.units = u.units
    spcur.coordinates = u.coordinates


def main(inargs):
    """Run the program"""

    inFile = inargs.infile
    uVar = inargs.uvar
    vVar = inargs.vvar
    outfile_name = inargs.outfile

    # Read input data
    uData, vData, input_DATA = read_data(inFile, uVar, vVar)

    # Calculate the current speed
    spData = calc_speed(uData, vData)

    # Write the output file
    outfile = Dataset(outfile_name, 'w', format='NETCDF4')
    set_global_atts(input_DATA, outfile)
    copy_dimensions(input_DATA, outfile)
    copy_variables(input_DATA, outfile)
    write_speed(input_DATA, outfile, spData)

    outfile.close()


if __name__ == '__main__':

    extra_info ="""example:
  python calc_current_speed.py http://thredds.aodn.org.au/thredds/dodsC/IMOS/eMII/demos/ACORN/monthly_gridded_1h-avg-current-map_non-QC/TURQ/2012/IMOS_ACORN_V_20121001T000000Z_TURQ_FV00_monthly-1-hour-avg_END-20121029T180000Z_C-20121030T160000Z.nc.gz UCUR VCUR IMOS_ACORN_SPCUR_20121001T000000Z_TURQ_monthly-1-hour-avg_END-20121029T180000Z.nc

author:
  Damien Irving, irving.damien@gmail.com

"""

    description='Calculate the current speed'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("infile", type=str, help="Input file name")
    parser.add_argument("uvar", type=str, help="Name of the zonal flow variable")
    parser.add_argument("vvar", type=str, help="Name of the meridional flow variable")
    parser.add_argument("outfile", type=str, help="Output file name")

    args = parser.parse_args()

    print 'Input file: ', args.infile
    print 'Output file: ', args.outfile

    main(args)