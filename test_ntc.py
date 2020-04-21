import tropycal.tracks as tracks
tc_id = "AL031981"
print("get hurdat_atl")
hurdat_atl = tracks.TrackDataset(basin='north_atlantic',include_btk=True)
print("get storm_raw")
storm_raw = hurdat_atl.get_storm(tc_id)
print("get op_storm")
op_storm = storm_raw.get_operational_forecasts()

print(f"\n{storm_raw['name']} - {storm_raw['year']}")

test_array = [0,1,2,3,4,5]
print(test_array[0:1])


keys = [k for k in op_storm.keys()]
print(keys)

OFCL = op_storm['CARQ']
forecasts = [value for key,value in OFCL.items()]
for i,forecast in enumerate(forecasts):
    print(f"\n{forecast['init']}")
    print(f"{forecast['fhr']}")
    print(f"{forecast['vmax']}")
    print(f"{forecast['mslp']}")
    if 3 not in forecast['fhr']: print(f"{forecast}")
