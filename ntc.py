###################################################################################
#                                                                                 #
# Calculates the Net Tropical Cyclone (NTC) activity from each year.              #
#   ACE - Calculates the accumulated cyclone energy using revised data.           #
#   OFCL_ACE - Calculates ACE using operational cone information.                 #
#   NTC - Calculates net tropical cyclone activity normalized by 1950-2000 years. #
#   OFCL_NTC - Calculates NTC using operational cone information.                 #
#                                                                                 #
# Code includes calculations of 1950-1990 averages that could be used for NTC.    #
#   It might be weird to calculate NTCs in the 1990s using data through 2000.     #
#   Or, you might want all years to be on equal footing knowing what we know now. #
#   It's up to you. But you'll have to adjust the code to make that work.         #
#                                                                                 #
# Code by Stephen Mullens. April 2020.                                            #
###################################################################################
 

import tropycal.tracks as tracks
from tropycal.tracks.tools import *
import numpy as np
import pandas
from datetime import datetime as dt,timedelta

#################################
# STEP 1:                       #
# Adjust some initial settings. #
#################################
# What year do you start outputing data?
start_printing = 1980

# What storms do you explicitly exclude?
bad_names = ['UNNAMED']

# When do you start looking up NHC cone forecasts?
if start_printing>1954: no_OFCL = start_printing
else: no_OFCL = 1954

# Create a couple of empty lists.
tc_storms=[]
OFCL_tc_storms=[]

######################
# STEP 1:            #
# Download the data. #
######################
hurdat_atl = tracks.TrackDataset(basin='north_atlantic',include_btk=True)

######################################################
# STEP 2:                                            #
# Loop through annual data to calculate ACE and NTC. #
######################################################
# Notes:
#
# Basin
# AL=Atlantic; EP=Eastern Pacific; WP=Western Pacific;
# IO=Indian Ocean; SH=Southern Hemisphere; CP=Central Pacific
#
# Type   (from: https://www.aoml.noaa.gov/hrd/hurdat/hurdat2-format.pdf)
# SS - named subtropical storm, TS - named tropical storm
# HU - hurricane, MH - HU & wind speed>96kt
# TD - tropical depression, SD - subtropical depression
# LO - "other" low, EX - extratropical, DB - disturbance, WV - wave

# Let's calculate how long it takes step 2 to run.
start_time = dt.now()

### For each year...
for year in range(1950,2020):
    # Print every 5 years unless it's taking a long time.
    # I just want to see that my code is still making progress.
    if (dt.now() - start_time).total_seconds()>1 or year%5==0: print(f"*** {year} ***")

    # Most of the code will want the year to be a string.
    # This will require re-conversion to int in if-statements.
    year = str(year)

    # This is where the stats for one year will be stored.
    # It will then be appended onto tc_storms.
    year_storms = []
    OFCL_year_storms = []


    #
    # Step 2a:
    # Get the season ACE value from revised data.
    #

    # Gets each season and converts it to a pandas dataframe.
    season = hurdat_atl.get_season(year)
    season = season.to_dataframe()

    # One of the items in the list is ACE for each storm.
    # Sum the ACE for all storms in the season.
    season_ace = season['ace'].sum()
    #print(f"{year},{season_ace:.1f}")

    # While we're here, store num_storms for each year for the next loop.
    num_storms = len(season)


    #
    # Step 2b:
    # Get stats to calculate the NTC activity.
    #

    ## We're going to accumulate these values. Start them all at zero.
    # These are for revised data.
    NS=HU=MH = 0
    NS_days=HU_days=MH_days = 0
    accum_ace = 0

    # These are using operational cone data.
    OFCL_NS=OFCL_HU=OFCL_MH = 0
    OFCL_NS_days=OFCL_HU_days=OFCL_MH_days = 0
    OFCL_accum_ace = 0

    ### For each storm in that year... (storm is just a number here).
    for storm in range(1,num_storms+1):

        # If we're getting operational data, show progress.
        if int(year)>no_OFCL: print(f"    Storm #{storm}")

        # Create the storm ID string needed to get the data.
        if storm < 10: storm = "0"+str(storm)
        else: storm = str(storm)

        tc_id = 'AL'+storm+year



        #
        # Step 2b, revised track data
        # Accumulate revised track data from after post-season review.
        #

        # Get the data for this storm.
        # If storm is unnamed, go to the next storm.
        # If data doesn't exist, go to the next storm.
        try:
            storm_raw = hurdat_atl.get_storm(tc_id)
            storm = storm_raw.to_dict()
            if storm['name'] in bad_names:
                continue
        except:
            print(f"*** Data for {tc_id} does not exist. ***")
            continue

        # Accumulate annual statistics using data from this storm.
        #   "storm_report_x" strings are to report progress and verify things are working.

        storm_report_1 = f"{year},{storm['name']},"

        # Total ACE values are given for each storm.
        accum_ace += storm['ace']

        # Find max category. Add one storm type to the season totals as appropriate.
        if 'HU' in storm['type'] and np.nanmax(storm['vmax'])>=96:
            NS += 1
            HU += 1
            MH += 1
            #storm_report_2 = "1,1,1,"

        elif 'HU' in storm['type'] and 64<=np.nanmax(storm['vmax'])<=95:
            NS += 1
            HU += 1
            #storm_report_2 = "1,1,0,"

        elif ('TS' in storm['type'] or 'SS' in storm['type']) and 34<=np.nanmax(storm['vmax'])<=63:
            NS += 1
            #storm_report_2 = "1,0,0,"

        #else: storm_report_2 = "0,0,0,"

        # Calculate named storm days, hurricane days, major hurricane days.
        #   Each [0, 6, 12, 18] UTC instance == 0.25 days
        #   Use XX_this to accumulate for this storm, for reporting only.
        NS_this=HU_this=MH_this=ACE_this=0.0

        ### For each observation in storm's life...
        for i,extra in enumerate(storm['extra_obs']):
            if extra==0 and storm['type'][i] in ['TS','SS'] and 34<=storm['vmax'][i]<=63:
                NS_days += 0.25

                #NS_this += 0.25
                #ACE_this += (10**-4) * (storm['vmax'][i]**2)

            elif extra==0 and storm['type'][i]=='HU' and 64<=storm['vmax'][i]<=95:
                NS_days += 0.25
                HU_days += 0.25

                #NS_this += 0.25
                #HU_this += 0.25
                #ACE_this += (10**-4) * (storm['vmax'][i]**2)

            elif extra==0 and storm['type'][i]=='HU' and storm['vmax'][i]>=96:
                NS_days += 0.25
                HU_days += 0.25
                MH_days += 0.25

                #NS_this += 0.25
                #HU_this += 0.25
                #MH_this += 0.25
                #ACE_this += (10**-4) * (storm['vmax'][i]**2)

        #storm_report_3 = f"{NS_this},{HU_this},{MH_this},{ACE_this:.1f}"

        # In years that you desire, print report for this storm for verification.
        #if year=='2019':
            #storm_report = storm_report_1 + storm_report_2 + storm_report_3
            #print(storm_report)

        # Report how accumulatd values progress through the season.
        #print(year,storm['name'],np.nanmax(storm['vmax']),NS,HU,MH,NS_days,HU_days,MH_days)



        #
        # Step 2b, operational track data
        # Get the operational track data if values are missing.
        # Accumulate operational track data from while storm was ongoing.
        #
        OFCL_vmax = 0; OFCL_type = ''

        # Get this only for 'recent' years...
        if int(year)>no_OFCL:
            # Originally, cone data didn't include the starting location.
            # Sometimes we need to get that information from elsewhere.
            # We get it from CARQ. Let's set a flag for whether we used it.
            use_carq = False

            # We're gonna put vmax and type info in lists.
            # Then, we can accumulate season info like we did above.
            OFCL_vmax_list = []
            OFCL_type_list = []


            # Get the data for this storm.
            # We already passed by unnamed storms and IDs with no data above.
            op_storm = storm_raw.get_operational_forecasts()

            # op_storms has all the operational AND model data. Too much!
            # Store the OFCL cone data and CARQ position data we need.
            OFCL = op_storm['OFCL']
            CARQ = op_storm['CARQ']

            # Verify you got what you wanted.
            #print(f"\nOFCL: {OFCL}")
            #print(f"CARQ: {CARQ}")

            # Make sure the cone data has what we need. If not, get it from CARQ.
            ### For each forecast in OFCL...
            for key,ofcl in OFCL.items():

                # If there is no initial forecast hour...
                #    Either there is no info at all (len==0) or first info is 12hr forecast.
                if len(ofcl['fhr'])==0 or (len(ofcl['fhr'])>0 and ofcl['fhr'][0] == 12):
                    #... then lets get the info from CARQ.

                    # This is the initial observation time we are looking for within CARQ.
                    ofcl_init = key

                    # Here's a list of CARQ initial times available.
                    carq_forecast_init = [k for k in CARQ.keys()]

                    # At the initial time we're looking for, here are the hours in the CARQ data.
                    # The CARQ data typically has fhr of [-24,-12,0]
                    hrs_carq = CARQ[ofcl_init]['fhr'] if ofcl_init in carq_forecast_init else []

                    # If there is an initial time in CARQ, then we have the data we need!
                    if ofcl_init in carq_forecast_init and 0 in hrs_carq:
                        # We're using CARQ data.
                        use_carq = True

                        # Here's the index in CARQ where you find fhr=0 (what we need). 
                        hr_idx = hrs_carq.index(0)

                        # Get the data! Put it at the beginning of the cone where it's supposed to be!
                        ofcl['fhr'].insert(0,CARQ[ofcl_init]['fhr'][hr_idx])
                        ofcl['lat'].insert(0,CARQ[ofcl_init]['lat'][hr_idx])
                        ofcl['lon'].insert(0,CARQ[ofcl_init]['lon'][hr_idx])
                        ofcl['vmax'].insert(0,CARQ[ofcl_init]['vmax'][hr_idx])
                        ofcl['mslp'].insert(0,CARQ[ofcl_init]['mslp'][hr_idx])

                        # If no type code is given, determine it from vmax.
                        # tropycal makes this easy with tracks.tools.get_type(), imported above.
                        itype = CARQ[ofcl_init]['type'][hr_idx]
                        if itype == "":
                            if pd.isnull(CARQ[ofcl_init]['vmax'][hr_idx]) == False:
                                itype = get_type(CARQ[ofcl_init]['vmax'][0],False)
                            else:
                                itype = np.nan
                        ofcl['type'].insert(0,itype)

                    # Update the cone list.
                    OFCL[key] = ofcl

                # If there is an initial forecast hour, we'll just use that.
                #    use_carq remains False
                else:
                    continue


            #
            # Step 2b, still in operational track data
            #   DONE: Get the operational track data if values are missing.
            #   NOW: Use the data to zccumulate operational track data from while storm was ongoing.
            #
            #forecasts = [value for key,value in OFCL.items()]

            ### For each forecast the NHC made...
            for forecast in OFCL.values():
                # Report forecasts that have no data, just to make sure.
                if len(forecast['fhr'])==0: print(f"\n{forecast}")

                # We will want to append most data to the master tc_storms list to calculate NTC.
                append=True

                # Operationally, the initial position is fhr==3. If it's there, then it's easy.
                # First, let's deal with if fhr==3 is not there.
                if 3 not in forecast['fhr']:

                    ###
                    # If there is data and mslp is recorded in 2nd item,
                    #    NHC probably updated data within 3 hours.
                    #    Use wind speed and type from fhr==0 item.
                    ###
                    #if len(forecast['mslp'])>1 and forecast['fhr'][0]==0 and np.isnan(forecast['mslp'][1])==False:
                    if len(forecast['mslp'])>1 and forecast['fhr'][0]==0:

                        # For first several years, there's no VMAX information.
                        # Common for 1980 - 1989
                        if np.all(pd.isnull([forecast['vmax'][0],forecast['type'][0]]))==True:
                            print("   VMAX & TYPE are NAN")

                        # But if there is for fhr==0, use it!
                        # Common for 1990 - 2000
                        else:
                            #print(f"\n   {tc_id}: {forecast['fhr']}");
                            #print(f"   {tc_id}: {forecast['mslp']}");
                            #print(f"   {tc_id}: {forecast['vmax']}");
                            #print(f"   {tc_id}: {forecast['type']}");
                            OFCL_vmax = forecast['vmax'][0]
                            OFCL_type = forecast['type'][0]
                            print(f"   USED IF {OFCL_vmax}kt -> {OFCL_type}")

                            # But tell me if something's weird between [0] and [1]
                            if np.any(np.isnan(forecast['vmax'][0:2]))==False:
                                if forecast['vmax'][1]!=forecast['vmax'][0] and forecast['fhr'][1]<=6:
                                    print(f"   {tc_id}: {forecast['fhr']}");
                                    print(f"   {tc_id}: {forecast['mslp']}");
                                    print(f"   {tc_id}: {forecast['vmax']}");
                                    print(f"   {tc_id}: {forecast['type']}");
                                    print(f"   *** SOMETHING IS DIFFERENT ***\n")

                    # OR, if we DID use CARQ, use the fhr==0 time.
                    elif use_carq==True and len(forecast['vmax'])>0:
                        OFCL_vmax = forecast['vmax'][0]
                        OFCL_type = forecast['type'][0]
                        #print(f"   USED ELIF {OFCL_vmax}kt -> {OFCL_type}")

                    # OR, if we did NOT use CARQ and we're in the middle of the storm's life,
                    #    then reuse the previous value. (Should be rare). 
                    elif use_carq==False and OFCL_vmax!=0:
                        print(f"\n   {tc_id}: {forecast['fhr']}");
                        print(f"   {tc_id}: {forecast['mslp']}");
                        print(f"   {tc_id}: {forecast['vmax']}");
                        print(f"   {tc_id}: {forecast['type']}");
                        print(f"   REUSE {OFCL_vmax}kt -> {OFCL_type}")
                        OFCL_vmax=OFCL_vmax
                        OFCL_type=OFCL_type

                    # OR, if everything falls through, skip it all.
                    #    Forecast entry has no data. Otherwise, shouldn't happen.
                    else:
                        print(f"\n   {tc_id}: {forecast['fhr']}");
                        print(f"   {tc_id}: {forecast['mslp']}");
                        print(f"   {tc_id}: {forecast['vmax']}");
                        print(f"   {tc_id}: {forecast['type']}");
                        print("   NOTHING DONE")

                #
                # but if there IS fhr==3, then use that data.
                #
                elif forecast['fhr'][1]==3:
                    OFCL_vmax = forecast['vmax'][1]
                    OFCL_type = forecast['type'][1]
                elif forecast['fhr'][2]==3 and forecast['fhr'][0]==0:
                    OFCL_vmax = forecast['vmax'][2]
                    OFCL_type = forecast['type'][2]
                # or, if neither of those, then don't append the data.
                else:
                    append=False
                    print(f"\n   {tc_id}: {forecast['fhr']}\n   CONTINUE"); continue

                # Once we figure out the data we want to use, put the vmax and type in lists.
                if append:
                    OFCL_vmax_list.append(OFCL_vmax)
                    OFCL_type_list.append(OFCL_type)
                # or, if we didn't want to append, just reset the append flag and continue. 
                else:
                    append=True

            #
            # Now we can just accumulate the stats like we did with the revised data.
            #

            # Find max category. Add one storm type to the season totals as appropriate.
            if 'HU' in OFCL_type_list and np.nanmax(OFCL_vmax_list)>=96:
                OFCL_NS += 1
                OFCL_HU += 1
                OFCL_MH += 1
                storm_report_2 = "1,1,1,"

            elif 'HU' in OFCL_type_list and 64<=np.nanmax(OFCL_vmax_list)<=95:
                OFCL_NS += 1
                OFCL_HU += 1
                storm_report_2 = "1,1,0,"

            elif ('TS' in OFCL_type_list or 'SS' in OFCL_type_list) and 34<=np.nanmax(OFCL_vmax_list)<=63:
                OFCL_NS += 1
                storm_report_2 = "1,0,0,"

            else: storm_report_2 = "0,0,0,"

            # Calculate named storm days, hurricane days, major hurricane days.
            NS_this=HU_this=MH_this=ACE_this=0.0

            for i in range(len(OFCL_vmax_list)):

                if OFCL_type_list[i] in ['TS','SS'] and 34<=OFCL_vmax_list[i]<=63:
                    OFCL_NS_days += 0.25

                    NS_this += 0.25
                    ACE_this += (10**-4) * (OFCL_vmax_list[i]**2)

                elif OFCL_type_list[i]=='HU' and 64<=OFCL_vmax_list[i]<=95:
                    OFCL_NS_days += 0.25
                    OFCL_HU_days += 0.25

                    NS_this += 0.25
                    HU_this += 0.25
                    ACE_this += (10**-4) * (OFCL_vmax_list[i]**2)

                elif OFCL_type_list[i]=='HU' and OFCL_vmax_list[i]>=96:
                    OFCL_NS_days += 0.25
                    OFCL_HU_days += 0.25
                    OFCL_MH_days += 0.25

                    NS_this += 0.25
                    HU_this += 0.25
                    MH_this += 0.25
                    ACE_this += (10**-4) * (OFCL_vmax_list[i]**2)

                if np.isnan(OFCL_vmax_list[i])==False:
                    if OFCL_type_list[i] in ['SS','TS','HU']:
                        OFCL_ace = (10**-4) * (OFCL_vmax_list[i]**2)
                        OFCL_accum_ace += OFCL_ace

            storm_report_3 = f"{NS_this},{HU_this},{MH_this},{ACE_this:.1f}"

            # If ACE is zero, report it to verify it's fine.
            # True for every storm before 1990.
            if ACE_this<0.1:
                storm_report = storm_report_1 + storm_report_2 + storm_report_3
                print(storm_report)


    #
    # Step 2c:
    # Store annual stats in master list (tc_storms) for calculating the NTC activity.
    #

    # Put annual stats into a dictionary. Append to list of years.
    year_storms = {'year':year,
                    'ACE':accum_ace,
                    'OFCL_ACE':OFCL_accum_ace,
                    'NS':NS,
                    'HU':HU,
                    'MH':MH,
                    'NS_days':NS_days,
                    'HU_days':HU_days,
                    'MH_days':MH_days
                    }
    tc_storms.append(year_storms)

    if int(year)>no_OFCL:
        OFCL_year_storms = {'year':year,
                        'ACE':OFCL_accum_ace,
                        'NS':OFCL_NS,
                        'HU':OFCL_HU,
                        'MH':OFCL_MH,
                        'NS_days':OFCL_NS_days,
                        'HU_days':OFCL_HU_days,
                        'MH_days':OFCL_MH_days
                        }
        OFCL_tc_storms.append(OFCL_year_storms)

# Report done and how long it took step 2 to run.
time_elapsed = dt.now() - start_time
tsec = round(time_elapsed.total_seconds(),2)
print(tsec)
if tsec>60:
    tmin = round(tsec/60,0)
    tsec = tsec - (tmin*60)
    print(f"--> Completed processing data ({tmin:.0f}:{tsec:.2f} minutes)")
else:
    print(f"--> Completed processing data ({tsec:.2f} seconds)")


#
# Step 3:
# Calculate Net Tropical Cyclone (NTC) activity.
#
#   Calculate NTC from revised data normalized by 1950-2000 averages (NTC_50).
#       or 1950-1990 averages (NTC_40).
#   Calculate NTC from OFCL data normalized by 1950-2000 averages (NTC_OFCL).
#

# Let's calculate how long it takes step 3 to run.
start_time = dt.now()

# Find averages for 1950-2000. For NTC_50.
NS_mean = np.array([yr['NS'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
HU_mean = np.array([yr['HU'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
MH_mean = np.array([yr['MH'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
NS_days_mean = np.array([yr['NS_days'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
HU_days_mean = np.array([yr['HU_days'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
MH_days_mean = np.array([yr['MH_days'] for yr in tc_storms if 1950<=int(yr['year'])<=2000]).mean()
print("\n*** NTC_50 averages ***")
print(f"{NS_mean:.1f},{HU_mean:.1f},{MH_mean:.1f},{NS_days_mean:.1f},{HU_days_mean:.1f},{MH_days_mean:.1f}\n")

# Find averages for 1950-1990. For NTC_40.
NS_mean_40 = np.array([yr['NS'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
HU_mean_40 = np.array([yr['HU'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
MH_mean_40 = np.array([yr['MH'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
NS_days_mean_40 = np.array([yr['NS_days'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
HU_days_mean_40 = np.array([yr['HU_days'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
MH_days_mean_40 = np.array([yr['MH_days'] for yr in tc_storms if 1950<=int(yr['year'])<=1990]).mean()
print("\n*** NTC_40 averages ***")
print(f"{NS_mean_40:.1f},{HU_mean_40:.1f},{MH_mean_40:.1f},{NS_days_mean_40:.1f},{HU_days_mean_40:.1f},{MH_days_mean_40:.1f}\n")

### For each year in the list of tropical years...
for i,yr in enumerate(tc_storms):

    # Normalize current year by 1950-2000 averages. For NTC_50.
    NTC_50_NS = yr['NS'] / NS_mean
    NTC_50_HU = yr['HU'] / HU_mean
    NTC_50_MH = yr['MH'] / MH_mean
    NTC_50_NS_days = yr['NS_days'] / NS_days_mean
    NTC_50_HU_days = yr['HU_days'] / HU_days_mean
    NTC_50_MH_days = yr['MH_days'] / MH_days_mean

    # Normalize current year by 1950-1990 averages. For NTC_40.
    NTC_40_NS = yr['NS'] / NS_mean_40
    NTC_40_HU = yr['HU'] / HU_mean_40
    NTC_40_MH = yr['MH'] / MH_mean_40
    NTC_40_NS_days = yr['NS_days'] / NS_days_mean_40
    NTC_40_HU_days = yr['HU_days'] / HU_days_mean_40
    NTC_40_MH_days = yr['MH_days'] / MH_days_mean_40

    # Normalize current year by 1950-2000 or 1950-1990 averages. For NTC_OFCL.
    if int(yr['year'])>no_OFCL:
        OFCL_yr = [oyr for oyr in OFCL_tc_storms if oyr['year']==yr['year']][0]
        if int(yr['year'])>2001:
            NTC_OFCL_NS = OFCL_yr['NS'] / NS_mean
            NTC_OFCL_HU = OFCL_yr['HU'] / HU_mean
            NTC_OFCL_MH = OFCL_yr['MH'] / MH_mean
            NTC_OFCL_NS_days = OFCL_yr['NS_days'] / NS_days_mean
            NTC_OFCL_HU_days = OFCL_yr['HU_days'] / HU_days_mean
            NTC_OFCL_MH_days = OFCL_yr['MH_days'] / MH_days_mean
        else:
            NTC_OFCL_NS = OFCL_yr['NS'] / NS_mean_40
            NTC_OFCL_HU = OFCL_yr['HU'] / HU_mean_40
            NTC_OFCL_MH = OFCL_yr['MH'] / MH_mean_40
            NTC_OFCL_NS_days = OFCL_yr['NS_days'] / NS_days_mean_40
            NTC_OFCL_HU_days = OFCL_yr['HU_days'] / HU_days_mean_40
            NTC_OFCL_MH_days = OFCL_yr['MH_days'] / MH_days_mean_40

    # Calculate final NTC_50 and NTC_OFCL values for this year.
    # Here, NTC is percent of normal. 100% = 1.0
    NTC_50 = (NTC_50_NS+NTC_50_HU+NTC_50_MH+
            NTC_50_NS_days+NTC_50_HU_days+NTC_50_MH_days) / 6
    NTC_40 = (NTC_40_NS+NTC_40_HU+NTC_40_MH+
            NTC_40_NS_days+NTC_40_HU_days+NTC_40_MH_days) / 6
    if int(yr['year'])>no_OFCL:
        NTC_OFCL = (NTC_OFCL_NS+NTC_OFCL_HU+NTC_OFCL_MH+
                NTC_OFCL_NS_days+NTC_OFCL_HU_days+NTC_OFCL_MH_days) / 6

    # Here, NTC * 100. So, 100% = 100.0
    NTC_50 = NTC_50 * 100
    NTC_40 = NTC_40 * 100
    if int(yr['year'])>no_OFCL: NTC_OFCL = NTC_OFCL * 100

    ### Add NTC to dictionary.                          
    # If you want all years normalized by 1950-2000, use this line.
    tc_storms[i].update( {'NTC_50':NTC_50} )
                          
    # If you want some years normalized by 1950-1990, others by 1950-2000, use these lines.
    #if int(yr['year'])>2001: tc_storms[i].update( {'NTC_50':NTC_50} )
    #else:               tc_storms[i].update( {'NTC_50':NTC_40} )
                          
    if int(yr['year'])>no_OFCL: tc_storms[i].update( {'NTC_OFCL':NTC_OFCL} )
    else: tc_storms[i].update( {'NTC_OFCL':0} )



#
# Step 4:
# Output results
#
                          
print("year,ACE,NTC_50")                          
#print("year,ACE,OFCL_ACE,NTC_50,NTC_OFCL")

for yr in tc_storms:
    if int(yr['year'])>=start_printing:
        print(f"{yr['year']},{yr['ACE']:.1f},{yr['NTC_50']:.1f}")
        """
        if yr['NTC_OFCL']>0:
            print(f"{yr['year']},{yr['ACE']:.1f},{yr['OFCL_ACE']:.1f},{yr['NTC_50']:.1f},{yr['NTC_OFCL']:.1f}")
        else:
            print(f"{yr['year']},{yr['ACE']:.1f},{yr['OFCL_ACE']:.1f},{yr['NTC_50']:.1f},--")
        """

time_elapsed = dt.now() - start_time
tsec = round(time_elapsed.total_seconds(),2)
if tsec>60:
    tmin = round(tsec/60,0)
    tsec = tsec - (tmin*60)
    print(f"--> Completed code ({tmin:.0f}:{tsec:.2f} minutes)")
else:
    print(f"--> Completed code ({tsec:2f} seconds)")
