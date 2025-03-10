"""Utility module for preparing the original JSON earthquakes dataset.

This module was taken from the previous Cassandra report and provides functions
to prepare the `earthquakes_big.geojson.json` dataset in several ways.
"""

import pandas as pd
import timezonefinder

def find_tz_offset(tz_name, tz_df):
        """Get the offset from the given timezone name.
        
        This is useful for converting the timestamps in the dataset to the
        correct, timezone-invariant format."""

        row = tz_df[tz_df['utc'].apply(lambda x: tz_name in x)]
        if len(row) > 0:
            return row.iloc[0]['offset']
        else:
            return 0

def apply_types(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the correct types to the given `merged_df` DataFrame.
    
    This method can be called after `merged_json` was loaded into a DataFrame
    to apply the correct types to the columns.
    
    We leave 'ids', 'sources', 'types', 'coordinates' as objects as they are
    lists that sometimes contain more than one value.
    Timestamps are assumed to be in milliseconds.
    """

    # Strings
    df[['alert', 'code', 'detail', 'id', 'magtype', 'place', 'net', 'url', 'status', 'type']] = df[['alert', 'code', 'detail', 'id', 'magtype', 'place', 'net', 'url', 'status', 'type']].astype(pd.StringDtype())

    # Timestamps
    df['time'] = df['time'].astype(pd.Int64Dtype())
    df['updated'] = df['updated'].astype(pd.Int64Dtype())

    return df

def prepare_dataset(df_path) -> pd.DataFrame:
    """Prepare the original dataset file named 'merged_df'.
    
    This method performs several improvements on the original JSON earthquakes
    dataset, such as applying the correct types, removing unneeded (*i.e.*
    static) columns, fixing the timestamps incorrectly encoded, etc."""

    df = pd.read_json(df_path, lines=True)

    df.drop('type', axis=1, inplace=True) # Contains one unique value

    df_properties = pd.json_normalize(df['properties'])

    # Format types, sources and ids using correct array notation
    df_properties['types'] = df_properties['types'].apply(lambda x: x[1:-1].split(','))
    df_properties['sources'] = df_properties['sources'].apply(lambda x: x[1:-1].split(','))
    df_properties['ids'] = df_properties['ids'].apply(lambda x: x[1:-1].split(','))

    # If it caused a tsunami (convert to Boolean correct format)
    df_properties['tsunami'] = df_properties['tsunami'] == 1

    df_geometry = pd.json_normalize(df['geometry'])
    df_geometry.drop('type', axis=1, inplace=True) # Contains one unique value

    # Convert timezones to UTC as it should be
    df_offsets = df_geometry['coordinates'].apply(lambda x: find_tz_offset(TZ_FINDER.timezone_at(lng=x[0], lat=x[1]), TZ_DF))
    df_properties['time'] = (df_properties['time'] + df_offsets * 60 * 60)
    df_properties['updated'] = (df_properties['updated'] + df_offsets * 60 * 60)
    df_properties.drop('tz', axis=1, inplace=True)

    # Concatenate properties and geometry
    merged_df = pd.concat([df.drop(['properties', 'geometry'], axis=1), df_properties, df_geometry], axis=1)

    merged_df.rename(str.lower, axis='columns', inplace=True)

    merged_df = apply_types(merged_df)

    return merged_df

DATASET_PATH = 'earthquakes_big.geojson.json'

# This is a file we created to extract the UTC timezone from a timezone name
TIMEZONES_PATH = 'timezones.json'

TZ_DF = pd.read_json('timezones.json')
TZ_FINDER = timezonefinder.TimezoneFinder()
TZ_NAMES = {tz_name: find_tz_offset(tz_name, TZ_DF) for tz_name in TZ_FINDER.timezone_names}