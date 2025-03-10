---
title: OCC2 MongoDB Report
author:
 - Klink, Carl
 - Lefebvre, Romain
 - Matthews, Louis-Marie
 - Muller, Julie
date: March the 10th, 2025
---

## Setting up the database

We will use Docker to install a local MongoDB server as well as a shell to access the database.

For this, we first download the `mongo` image.

```bash
docker pull mongo
```

Then we create and run a container with that image.

```bash
docker run --name mongodb -d -p 27017:27017 mongo
```

### Download the files

We can now clone our Git repository.

```
git clone git@github.com:Jlemlr/MongoDB.git
```

### MongoDB Compass

Compass is a tool that provides a GUI for interacting with a MongoDB database. It provides interesting features such as a graphical interface (as previously stated), as well as access to the Mongo shell, index optimisation features, natural language queries, and many more.

If MongoDB is installed, here are the steps to install it:

1. Start Compass
1. Create a connection (`mongodb://localhost:27017/`). If this doesn’t work make sure your container was created with the name `mongodb` withh the port `27017` open.
1. Create a new database and open the `output_earthquake_data_geojson.json` file from the github repository you downloaded.

You can directly write your queries in the UI of `MongoDb` Compass.

---
## Preparing the dataset

Next, we load and transform our original dataset `earthquakes_big.geojson.json` into `merged_df.json`, the same we used for the Cassandra assignment.

This dataset has the correct types applied. Unneeded (*i.e.* static) columns are removed. Timestamps are converted to the right format and are made timezone-independent. Nested properties are flattened, etc.

First, we install the dependencies required for our function:

```bash
pip install -r requirements.txt
```

Then, we create the `merged_df` DataFrame.

```python
merged_df = utils.prepare_dataset(utils.DATASET_PATH)
```

We now run the following code to create a `location` field into correct `GeoJSON` format. And then we save the file.

```python
def transform_to_geojson(df):
    """Transform the location for MongoDB."""

    df['location'] = df['coordinates'].apply(lambda coords: {'type': 'Point', 'coordinates': coords[:2]})

    # Delete `coordinates` column
    df.drop('coordinates', axis=1, inplace=True)
    
    return df

df = transform_to_geojson(merged_df)
df.to_json('output_earthquake_data_geojson.json', orient='records')
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
