# Report MongoDB

---
## Setup the database

### Setup docker

```
docker pull mongo
```

```bash
docker run --name mongodb -d -p 27017:27017 mongo
```
### Download the files

Clone the following repository
```
git clone git@github.com:Jlemlr/MongoDB.git
```

### MongoDB Compass

- open mongoDB Compass
- create connection (`mongodb://localhost:27017/`)
- create a new database and open the `output_earthquake_data_geojson.json` file from the github repository you downloaded

You can directly write your queries in the UI of `MongoDb` Compass.

---
## Preparing the dataset

We used the `json` we generated for the Cassandra homework and ran the following code to transform the  'location' field into `GeoJSON` format.

```python
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
input_file = 'merged_df.json'  # Replace with your input file path
output_file = 'output_earthquake_data_geojson.json'  # Desired output file path

transform_to_geojson(input_file, output_file)
```

---
## Queries

For more readability we didn't write the outputs (except for the hard query).
### Easy

1. Retrieve all earthquakes
```
db["Earthquake"].find({})
```

2. Get earthquakes with magnitude greater than 4.0
```
db["Earthquake"].find({ mag: { $gt: 4.0 } })
```

3. Find earthquakes that occurred in California
```
db["Earthquake"].find({ place: /California/ })
```

4. List all earthquake IDs and their magnitudes
```
db["Earthquake"].find({}, { id: 1, mag: 1, _id: 0 })
```

5. Get earthquakes with a specific status (e.g., "AUTOMATIC")
```
db["Earthquake"].find({ status: "AUTOMATIC" })
```

6. Find the top 5 strongest earthquakes
```
db["Earthquake"].find({}).sort({ mag: -1 }).limit(5)
```

### Complex

1. Returns all earthquakes from the year 2013
```
var startOf2013 = new Date("2013-01-01T00:00:00Z").getTime();
var endOf2013 = new Date("2013-12-31T23:59:59Z").getTime();

db["Earthquake"].find({ 
    time: { $gte: startOf2013, $lte: endOf2013 } 
});
```

2. Get the average magnitude of earthquakes in California
```
db["Earthquake"].aggregate([
  { $match: { place: /California/ } },
  { $group: { _id: null, avg_magnitude: { $avg: "$mag" } } }
])
```

### Hard

1. Find the closest earthquake to a given location (latitude: 38.8232, longitude: -122.7955)
```
db["Earthquake"].find(
  {
    location: {
      $near: {
        $geometry: {
          type: "Point",
          coordinates: [-122.7955, 38.8232]
        }
      }
    }
  },
  { location: 1, _id: 0 }
).limit(1)
```
---
```output
{
  location: {
    type: 'Point',
    coordinates: [
      -122.7955,
      38.8232
    ]
  }
}
```
