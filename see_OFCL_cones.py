##############################################################################
#                                                                            #
# Lets you view the operational cone data for a particular tropical cyclone. #
#   Or, you can view the CARQ data instead.                                  #
#                                                                            #
# Code by Stephen Mullens. April 2020.                                       #
##############################################################################
import tropycal.tracks as tracks

# Which storm do you want to see?
# ALXXYYYY
# AL = Atlantic, XX = storm number, YYYY = year
tc_id = "AL031981"

# Download the dataset for the North Atlantic basin.
# include_btk includes the current year.
print("get hurdat_atl")
hurdat_atl = tracks.TrackDataset(basin='north_atlantic',include_btk=True)

# Get the data for the tc_id.
print("get storm_raw")
storm_raw = hurdat_atl.get_storm(tc_id)

# Get the operational forecasts for the tc_id.
print("get op_storm")
op_storm = storm_raw.get_operational_forecasts()

# Output the storm's name and the year it occurred.
print(f"\n{storm_raw['name']} - {storm_raw['year']}")

# Output all the 4-character model codes for this storm. 
keys = [k for k in op_storm.keys()]
print(keys)

# Pick out the NHC cone (OFCL).
# Output parts of the cone data.
# Note: fhr=3 is typically the starting time for a new cone.
CARQ = op_storm['CARQ']
OFCL = op_storm['OFCL']
forecasts = [value for key,value in OFCL.items()]
for i,forecast in enumerate(forecasts):
    print(f"\n{forecast['init']}")
    print(f"{forecast['fhr']}")
    print(f"{forecast['vmax']}")
    print(f"{forecast['mslp']}")
    if 3 not in forecast['fhr']: print(f"{forecast}")
