import pandas as pd
import fasttrips
NETWORK_DIR = r"R:\FastTrips\FT Repo\network_draft1.8"

# bridge from CHTS travel_mode => operator_type
CHTS_MODE_TO_OPERATOR_TYPE = {
    15 : "Local_bus/Rapid_bus",
    16 : "GoldenGate/AC_transit",
    19 : None,
    20 : "AirBART",
    24 : "BART",
    23 : "Local_bus/Rapid_bus",
    25 : "ACE/Caltrain",
    26 : "MuniMetro/VTA",
    27 : "Street_car/Cable_car",
    29 : "Ferry"
}

# bridge from network service_id => operator_type
NETWORK_AGENCY_TO_OPERATOR_TYPE = {
    "bart"                  :"BART",
    "airbart"               :"AirBART",
    "ac_transit"            :"GoldenGate/AC_transit",
    "caltrain"              :"ACE/Caltrain",
    "samtrans"              :"Local_bus/Rapid_bus",
    "golden_gate_transit"   :"GoldenGate/AC_transit",
    "santa_rosa"            :"Local_bus/Rapid_bus",
    "ace"                   :"ACE/Caltrain",
    "lavta"                 :"Local_bus/Rapid_bus",
    "scvta"                 :"Local_bus/Rapid_bus",
    "sonoma_county_transit" :"Local_bus/Rapid_bus",
    "union_city_transit"    :"Local_bus/Rapid_bus",
    "petaluma"              :"Local_bus/Rapid_bus",
    "tri_delta_transit"     :"Local_bus/Rapid_bus",
    "cccta"                 :"Local_bus/Rapid_bus",
    "vine"                  :"Local_bus/Rapid_bus",
    "soltrans"              :"Local_bus/Rapid_bus",
    "ferry"                 :"Ferry",
    "sf_muni"               :"sf_muni"
}

'''
# bridge from stop_id to taz_id
taz_dict = pd.read_excel('stops.xlsx','Sheet1')
taz_dict.index = taz_dict.stop_id
taz_dict = taz_dict.drop('stop_id',axis=1)
STOPS_TO_SFTAZ = taz_dict.to_dict()['zone_id']
'''

def get_closest_stop(person_trips_df, vehicle_stops_df, location_prefix):
    # join the person trips with the stops
    person_trips_by_stops_df = pd.merge(left=person_trips_df,
                                        right=vehicle_stops_df,
                                        how="inner")

    # calculate the distance from [location_prefix]_lat, [location_prefix]_lon, and the stop
    fasttrips.Util.calculate_distance_miles(person_trips_by_stops_df,
                                            origin_lat="%s_lat" % location_prefix, origin_lon="%s_lon" % person_prefix,
                                            destination_lat="stop_lat",          destination_lon="stop_lon",
                                            distance_colname="%s_stop_dist" % location_prefix)

    # get the closest stop
    person_trips_df = person_trips_by_stops_df.loc[ person_trips_by_stops_df.groupby("Unique_ID")["%s_stop_dist" % location_prefix].idxmin() ]

    # rename the new columns
    person_trips_df.rename(columns={"stop_id"  :"%s_stop_id"   % location_prefix,
                                    "stop_name":"%s_stop_name" % location_prefix,
                                    "stop_lat" :"%s_stop_lat"  % location_prefix,
                                    "stop_lon" :"%s_stop_lon"  % location_prefix
                                    "route_id" :"%s_route_id"  % location_prefix}, inplace=True)
    return person_trips_df

if __name__ == "__main__":
    ft = fasttrips.FastTrips(input_network_dir= NETWORK_DIR,
                             input_demand_dir = None,
                             output_dir       = ".")
 
    ft.read_input_files()
    # Get the full (joined) transit vehicle trip table and add lat/lon for the stops
    full_trips_df = ft.trips.get_full_trips()
    full_trips_df = ft.stops.add_stop_lat_lon(full_trips_df, id_colname="stop_id", new_lat_colname="stop_lat", new_lon_colname="stop_lon", new_stop_name_colname="stop_name")
    # Add operator_type to match with CHTS file
    full_trips_df["operator_type"] = full_trips_df["agency_id"].replace(NETWORK_AGENCY_TO_OPERATOR_TYPE)

    # Read CHTS observed person trips file
    df = pd.read_csv('CHTS_FToutput.csv')
    # Add operator_type to CHTS
    df["operator_type"] = df["transit_mode_no"].replace(CHTS_MODE_TO_OPERATOR_TYPE)
    # Add Unique_ID to be used for merging later on
    df['Unique_ID'] = df.index
    
    Locations = ['A','B']
    A_stops = pd.DataFrame()
    B_stops = pd.DataFrame()
    
    df_operator_type_series = df["operator_type"].value_counts()
    for OPtype in df_operator_type_series.keys():
        service_vehicle_trips = full_trips_df.loc[ full_trips_df["operator_type"] == OPtype ]
        service_person_trips  = df.loc[df["operator_type"] == OPtype]
    
        print OPtype
        service_unique_vehicle_stops = service_vehicle_trips[["operator_type","route_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
        for i in Locations:
            stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
            stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon', i+'_route_id']]
            if   i=='A'  : A_stops  = A_stops.append(stops, ignore_index=True)
            else         : B_stops  = B_stops.append(stops, ignore_index=True)

    # sf_muni has 3 different operation types: local bus, light rail and streetcar. So we have to process it separately
    print 'sf_muni'
    service_vehicle_trips = full_trips_df.loc[ full_trips_df["operator_type"] == 'sf_muni' ]
    # Choose service_person_trips with operator_types "Local_bus/Rapid_bus" or "MuniMetro/VTA", 
    # and rename them to 'sf_muni' to match with service_vehicle_trips
    service_person_trips = df.loc[ (df["operator_type"] == "Local_bus/Rapid_bus") & (df["operator_type"] == "MuniMetro/VTA") & (df["operator_type"] == "Street_car/Cable_car")]
    service_person_trips[ service_person_trips["operator_type"]=="Local_bus/Rapid_bus", "operator_type" ] = 'sf_muni'
    service_person_trips[ service_person_trips["operator_type"]=="MuniMetro/VTA", "operator_type" ] = 'sf_muni'
    service_person_trips[ service_person_trips["operator_type"]=="Street_car/Cable_car", "operator_type" ] = 'sf_muni'
    service_unique_vehicle_stops = service_vehicle_trips[["operator_type","route_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
    for i in Locations:
        stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
        stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon', i+'_route_id']]
        if   i=='A'  : A_stops  = A_stops.append(stops, ignore_index=True)
        else         : B_stops  = B_stops.append(stops, ignore_index=True)


    # Put all stop_id and route_id info into the original CHTS dataframe
    new_df = df
    new_df = pd.merge (new_df, A_stops, how='left', on='Unique_ID')
    new_df = pd.merge (new_df, B_stops, how='left', on='Unique_ID')
    '''
    #A_id in access links and B_id in egress links should be taz_id and not stop_id
    new_df['A_id'] = None
    new_df['A_id'] = new_df['A_stop_id'].replace(STOPS_TO_SFTAZ)
    new_df.loc [ df['linkmode']!='access', 'A_id' ] = new_df['A_stop_id']
    new_df['B_id'] = None
    new_df['B_id'] = new_df['B_stop_id'].replace(STOPS_TO_SFTAZ)
    new_df.loc [ df['linkmode']!='egress', 'B_id' ] = new_df['B_stop_id']
    '''
    
    new_df.to_csv("CHTS_FToutput_wStops_wRoutes.csv", index=False)
    print 'Done'