import json

def transform_to_geojson(input_file, output_file):
    # Load the original earthquake data from the input JSON file
    with open(input_file, 'r') as file:
        earthquake_data = [json.loads(line) for line in file]  # Adjust for each line being a JSON object

    # Prepare the data with 'location' field in GeoJSON format
    for earthquake in earthquake_data:
        earthquake['location'] = {
            "type": "Point",
            "coordinates": earthquake['coordinates'][:2]  # Only use longitude, latitude for GeoJSON
        }
        del earthquake['coordinates']  # Remove the original coordinates field

    # Output the transformed data to the output JSON file
    with open(output_file, 'w') as outfile:
        json.dump(earthquake_data, outfile, indent=4)

    print(f"Data successfully transformed and saved to {output_file}.")

# Usage
input_file = '/content/merged_df.json'  # Replace with your input file path
output_file = 'output_earthquake_data_geojson.json'  # Desired output file path

transform_to_geojson(input_file, output_file)
