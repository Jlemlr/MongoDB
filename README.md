---
title: OCC2 MongoDB Report
author:
 - Klink, Carl
 - Lefebvre, Romain
 - Matthews, Louis-Marie
 - Muller, Julie
date: March the 10th, 2025
---

# Initial setup

## Creating the database

We will use Docker to install a local MongoDB server as well as a shell to access the database.

For this, we first download the `mongo` image.

```bash
docker pull mongo
```

Then we create and run a container with that image.

```bash
docker run --name mongodb -d -p 27017:27017 mongo
```

## Cloning the repository

We can now clone our Git repository.

```
git clone git@github.com:Jlemlr/MongoDB.git
```

## MongoDB Compass

Compass is a tool that provides a GUI for interacting with a MongoDB database. It provides interesting features such as a graphical interface (as previously stated), as well as access to the Mongo shell, index optimisation features, natural language queries, and many more.

If MongoDB is installed, here are the steps to install it:

1. Start Compass
1. Create a connection (`mongodb://localhost:27017/`). If this doesn’t work make sure your container was created with the name `mongodb` withh the port `27017` open.
1. Create a new database and open the `output_earthquake_data_geojson.json` file from the github repository you downloaded.

You can directly write your queries in the UI of `MongoDb` Compass.

# Preparing the dataset

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

We now have a nicely formatted JSON file that is correctly formatted for importing into MongoDB!

```json
[
    {
        "id": "nc72001620",
        "mag": 0.8,
        "place": "6km W of Cobb, California",
        "time": 1370259942800,
        "updated": 1370260605561,
        "url": "http:\/\/earthquake.usgs.gov\/earthquakes\/eventpage\/nc72001620",
        "detail": "http:\/\/earthquake.usgs.gov\/earthquakes\/feed\/v1.0\/detail\/nc72001620.geojson",
        "felt": null,
        "cdi": null,
        "mmi": null,
        "alert": null,
        "status": "AUTOMATIC",
        "tsunami": false,
        "sig": 10,
        "net": "nc",
        "code": "72001620",
        "ids": [
            "nc72001620"
        ],
        "sources": [
            "nc"
        ],
        "types": [
            "general-link",
            "geoserve",
            "nearby-cities",
            "origin",
            "phase-data",
            "scitech-link"
        ],
        "nst": null,
        "dmin": 0.00898315,
        "rms": 0.06,
        "gap": 82.8,
        "magtype": "Md",
        "type": "earthquake",
        "location": {
            "type": "Point",
            "coordinates": [
                -122.7955,
                38.8232
            ]
        }
    },
    ...
```

## Loading the JSON into MongoDB

We first need to connect to our MongoDB standalone cluster, *i.e.* server.

To do that, from the MongoDB container, we run: `mongosh` to run the shell.

```bash
root@279d3593702c:/# mongosh
Current Mongosh Log ID: 67d0d9e85ba9a55c1051e943
Connecting to:          mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.0
Using MongoDB:          8.0.5
Using Mongosh:          2.4.0

For mongosh info see: https://www.mongodb.com/docs/mongodb-shell/
```

This is useful to us, as we get the parameters necessary to connect to our MongoDB server. This output is followed by non-critical warnings that relate to performance (because of the filesystem) and security considerations, details into which we won’t delve as this is only a local database used for testing.

Now that we know how to connect to our server, we can exit the shell by typing `exit`.

We will now run `mongoimport` to import the our JSON into a collection of a new database in our server.

```bash
root@279d3593702c:/root# mongoimport --uri mongodb://127.0.0.1:27017/?directConnection=true --db=dibi --collection earthquakes --type json --f
ile output_earthquake_data_geojson.json --jsonArray
2025-03-12T00:57:38.101+0000    connected to: mongodb://127.0.0.1:27017/?directConnection=true
2025-03-12T00:57:38.492+0000    7669 document(s) imported successfully. 0 document(s) failed to import.
```

So, from reading the logs, all 7669 earthquakes were imported. We remember from the previous report that we all 7669 reports. Just to check though, from our Pandas dataframe:

```python
len(df)
```

This does return 7669 rows, great!

Let’s now connect back to our server and our database, and check the number of documents in our `earthquakes` collection. (And also check that the `dibi` database and `earthquakes` collection were both successfully created by the `mongoimport` command!)

```bash
root@279d3593702c:/root# mongosh
Current Mongosh Log ID: 67d0de0fdd76ee883751e943
Connecting to:          mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.0
Using MongoDB:          8.0.5
Using Mongosh:          2.4.0

For mongosh info see: https://www.mongodb.com/docs/mongodb-shell/

------
   The server generated these startup warnings when booting
   2025-03-12T00:38:10.932+00:00: Using the XFS filesystem is strongly recommended with the WiredTiger storage engine. See http://dochub.mongodb.org/core/prodnotes-filesystem
   2025-03-12T00:38:11.964+00:00: Access control is not enabled for the database. Read and write access to data and configuration is unrestricted
   2025-03-12T00:38:11.964+00:00: For customers running the current memory allocator, we suggest changing the contents of the following sysfsFile
   2025-03-12T00:38:11.964+00:00: We suggest setting the contents of sysfsFile to 0.
   2025-03-12T00:38:11.964+00:00: Your system has glibc support for rseq built in, which is not yet supported by tcmalloc-google and has critical performance implications. Please set the environment variable GLIBC_TUNABLES=glibc.pthread.rseq=0
   2025-03-12T00:38:11.964+00:00: vm.max_map_count is too low
   2025-03-12T00:38:11.964+00:00: We suggest setting swappiness to 0 or 1, as swapping can cause performance problems.
------

test> show dbs
TP      22.21 MiB
admin   40.00 KiB
config  72.00 KiB
dibi     1.37 MiB
local   72.00 KiB
test     1.37 MiB
test> use dibi
switched to db dibi
dibi> show collections
earthquakes
dibi> db.earthquakes.countDocuments()
7669
```

Okay, so our `dibi` database was successfully created. Our collection `earthquakes` was also created and does contain our 7669 earthquakes as expected!

Let’s now remove the `test` database for proper housekeeping.

```bash
dibi> use test
switched to db test
test> db.dropDatabase()
{ ok: 1, dropped: 'test' }
```

😊.

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
