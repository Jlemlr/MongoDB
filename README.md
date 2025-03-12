---
title: OCC2 MongoDB Report
author:
 - Klink, Carl
 - Lefebvre, Romain
 - Matthews, Louis-Marie
 - Muller, Julie
date: March the 10th, 2025
---

# Setup

## Cloning the repository

We start our journey by simpling cloning our repository, which contains the original version of the dataset we are working on: `earthquakes_big.geojson.json`.

```
git clone git@github.com:Jlemlr/MongoDB.git
```

## Preparing the dataset

First, as instructed, we will display one row of the original dataset. (We only formatted the first row for readability, no transformation of any kind was performed.)

```json
{
    "type": "Feature",
    "properties": {
        "mag": 0.8,
        "place": "6km W of Cobb, California",
        "time": 1370259968000,
        "updated": 1370260630761,
        "tz": -420,
        "url": "http://earthquake.usgs.gov/earthquakes/eventpage/nc72001620",
        "detail": "http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/nc72001620.geojson",
        "felt": null,
        "cdi": null,
        "mmi": null,
        "alert": null,
        "status": "AUTOMATIC",
        "tsunami": null,
        "sig": 10,
        "net": "nc",
        "code": "72001620",
        "ids": ",nc72001620,",
        "sources": ",nc,",
        "types": ",general-link,geoserve,nearby-cities,origin,phase-data,scitech-link,",
        "nst": null,
        "dmin": 0.00898315,
        "rms": 0.06,
        "gap": 82.8,
        "magType": "Md",
        "type": "earthquake"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [
            -122.7955,
            38.8232,
            3
        ]
    },
    "id": "nc72001620"
}
```

Next, we load our original dataset `earthquakes_big.geojson.json` into a Pandas DataFrame and transform it into another DataFrame called `merged_df`, the same we used for the Cassandra assignment. For this, we will use `prepare_dataset` function defined in `utils.py`. This is the same preparation code than we used in the Cassandra assignment, with a few minor code improvements (which are documented in the file `utils.py`.).

Before anything, we install the Python librairies needed by our code:

```bash
pip install -r requirements.txt
```

Then, we create the `merged_df` DataFrame.

```python
merged_df = utils.prepare_dataset(utils.DATASET_PATH)
```

The resulting `merged_df` dataset has the correct types applied. Unneeded (*i.e.* static) columns are removed. Timestamps are converted to the right format and are made timezone-independent. Nested properties are flattened, etc.

We can see that there are duplicates of the same magnitude: `mb_Lg` and `MbLg` stand for the same thing, as for `ML` and `Ml` and `ml`, and finally, `mb` and `Mb`. Let’s fix that:

```python
df['magtype'] = df['magtype'].str.lower().str.replace('_', '')
df['magtype'].unique()
```

We now run the following code to create a `location` field into correct `GeoJSON` format. And then we save the file.

```python
def transform_to_mongodbdate(datetime):
    if datetime is not None:
        return {
            "$date": datetime,
        }
    else:
        return None

df['time'] = df['time'].apply(transform_to_mongodbdate)

df['updated'] = df['updated'].apply(transform_to_mongodbdate)
```

We save our file:

```python
df.to_json('earthquakes_transformed.json', orient='records')
```

We now have a nicely formatted JSON file that is correctly formatted for importing into MongoDB!

```json
{
    "id": "nc72001620",
    "mag": 0.8,
    "place": "6km W of Cobb, California",
    "time": {
        "$date": 1370259968000
    },
    "updated": {
        "$date": 1370260630761
    },
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
}
```

## Loading the JSON into MongoDB

### Creating the database

We will use Docker to install a local MongoDB server as well as a shell to access the database.

For this, we first download the `mongo` image.

```bash
docker pull mongo
```

Then we create and run a container with that image.

```bash
docker run --name mongodb -d -p 27017:27017 mongo
```

We now have a MongoDB container (which is like a virtual MongoDB server) running!

### MongoDB Compass

Compass is a tool that provides a GUI for interacting with a MongoDB database. It provides interesting features such as a graphical interface (as previously stated), as well as access to the Mongo shell, index optimisation features, natural language queries, and many more.

If MongoDB is installed, here are the steps to install it:

1. Start Compass
1. Create a connection (`mongodb://localhost:27017/`). If this doesn’t work make sure your container was created with the name `mongodb` withh the port `27017` open.
1. Create a new database and open the `earthquakes_transformed.json.json` file from the github repository you downloaded.

You can now directly write your queries in the UI of `MongoDb` Compass.

## Importing the JSON file into MongoDB

We now need to connect to our MongoDB standalone cluster, *i.e.* server, to create the database and import the transformed `earthquakes_transformed.json` dataset.

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
root@279d3593702c:/root# mongoimport --uri mongodb://127.0.0.1:27017/?directConnection=true --db=dibi --collection earthquakes --type json --file earthquakes_transformed.json --jsonArray
2025-03-12T00:57:38.101+0000    connected to: mongodb://127.0.0.1:27017/?directConnection=true
2025-03-12T00:57:38.492+0000    7669 document(s) imported successfully. 0 document(s) failed to import.
```

Notice we used `mongodb://127.0.0.1:27017/?directConnection=true` because this is what appeared in the log when we ran `mongosh`.

So, from reading the logs, all 7669 earthquakes were imported. We remember from the previous report that we all 7669 reports. Just to check though, from our Pandas dataframe:

```python
len(df)
```

This does return 7669 rows, great!

Let’s now connect back to our server and our database, and check the number of documents in our `earthquakes` collection. (And also check that the `dibi` database and `earthquakes` collection were both successfully created by the `mongoimport` command!)

```bash
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

We’re all set, the setup is completed!

# Queries

For more readability, we limited all the queries to return only the first one or two results.

### Easy queries

#### 1 Retrieve the first earthquake stored in the collection

```bash
dibi> db.earthquakes.find().limit(1)
[
  {
    _id: ObjectId('67d15c3057df22624788ad13'),
    id: 'ak10729211',
    mag: 1.2,
    place: '97km WSW of Cantwell, Alaska',
    time: ISODate('2013-06-03T11:41:03.000Z'),
    updated: ISODate('2013-06-03T11:48:50.916Z'),
    url: 'http://earthquake.usgs.gov/earthquakes/eventpage/ak10729211',
    detail: 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/ak10729211.geojson',
    felt: null,
    cdi: null,
    mmi: null,
    alert: null,
    status: 'AUTOMATIC',
    tsunami: false,
    sig: 22,
    net: 'ak',
    code: '10729211',
    ids: [ 'ak10729211' ],
    sources: [ 'ak' ],
    types: [
      'general-link',
      'geoserve',
      'nearby-cities',
      'origin',
      'tectonic-summary'
    ],
    nst: null,
    dmin: null,
    rms: 0.83,
    gap: null,
    magtype: 'Ml',
    type: 'earthquake',
    location: { type: 'Point', coordinates: [ -150.8246, 63.1584 ] }
  }
]
```

#### 2 Get the place of earthquakes with magnitude greater than 4.0

```bash
dibi> db.earthquakes.find({ mag: { $gt: 4.0 } }, { place: 1, _id: 0 }).limit(2)
[
  { place: '155km WSW of Panguna, Papua New Guinea' },
  { place: "251km E of Kuril'sk, Russia" }
]
```

#### 3 Find the magnitude of earthquakes that occurred in California

The complete output being very long, only the first five rows are displayed here.

```bash
dibi> db.earthquakes.find({ place: /California/ }, { _id: 0, mag: 1 })
[
  { mag: 1.4 },
  { mag: 0.8 },
  { mag: 1 },  
  { mag: 1.1 },
  { mag: 0.4 },
  …
]
```

#### 4 Find the top 5 strongest earthquakes

```bash
dibi> db.earthquakes.find({}, { mag: 1 }).sort({ mag: -1 }).limit(5)
...
[
  { _id: ObjectId('67d0dc0298be26e220e73c19'), mag: 8.3 },
  { _id: ObjectId('67d0dc0298be26e220e73ce9'), mag: 7.4 },
  { _id: ObjectId('67d0dc0298be26e220e7471f'), mag: 6.8 },
  { _id: ObjectId('67d0dc0298be26e220e73b55'), mag: 6.7 },
  { _id: ObjectId('67d0dc0298be26e220e74054'), mag: 6.4 }
]
```

#### 5 List and order all earthquakes that caused a tsunami

```bash
dibi> db.earthquakes.find({ tsunami: true }, { id: 1, mag: 1, magtype: true, _id: 0 })
[
  { id: 'usb000hbrt', mag: 6.2, magtype: 'Mww' },
  { id: 'pr13152001', mag: 4.4, magtype: 'Md' },
  { id: 'pr13151003', mag: 4.2, magtype: 'Md' },
  { id: 'ci15350729', mag: 4.8, magtype: 'Mw' },
  { id: 'usb000h543', mag: 6.7, magtype: 'Mt' },
  { id: 'usb000h4jh', mag: 8.3, magtype: 'Mw' },
  { id: 'nc71996906', mag: 5.7, magtype: 'Mw' },
  { id: 'usb000h40b', mag: 6.3, magtype: 'Mw' },
  { id: 'usb000h3k3', mag: 7.4, magtype: 'Mw' },
  { id: 'usb000h0bv', mag: 4.7, magtype: 'Mb' },
  { id: 'usb000gzlm', mag: 6.4, magtype: 'Mw' },
  { id: 'pr13139004', mag: 4.1, magtype: 'Md' },
  { id: 'ak10718820', mag: 4.4, magtype: 'Ml' },
  { id: 'ci15343145', mag: 4, magtype: 'Mw' },
  { id: 'ak10714815', mag: 4.4, magtype: 'Ml' }
]
```

#### 6 Find the possible types of magnitudes

```bash
dibi> db.earthquakes.distinct("magtype")
[
  null,   'h',   'mb',
  'mblg', 'md',  'me',
  'ml',   'mt',  'mw',
  'mwb',  'mwp', 'mww'
]
```

#### 7 Get earthquakes that have a "felt" value specified

Because the `felt` value is often null, we will check the earthquakes for whom the `felt` value is provided.

```
dibi> db.earthquakes.find({ felt: { $ne: null } }, { _id: 0, felt: 1, mag: 1 })
[
  { mag: 2.6, felt: 6 },  { mag: 5.6, felt: 7 },
  { mag: 4.5, felt: 2 },  { mag: 2, felt: 2 },
  { mag: 4.5, felt: 6 },  { mag: 5.1, felt: 1 },
  { mag: 2.5, felt: 1 },  { mag: 2.7, felt: 3 },
  { mag: 1.7, felt: 6 },  { mag: 6.2, felt: 53 },
  { mag: 1.98, felt: 3 }, { mag: 2.5, felt: 21 },
  { mag: 1.1, felt: 1 },  { mag: 3.4, felt: 9 },
  { mag: 3.4, felt: 4 },  { mag: 4.8, felt: 1 },
  { mag: 1.8, felt: 2 },  { mag: 3.2, felt: 3 },
  { mag: 3.4, felt: 0 },  { mag: 5.6, felt: 35 }
]
```

Interesting to notice the correlation between the manitude and the `felt` value, although it is sometimes very far off!


### Complex queries

#### 1 Returns all earthquakes from the year 2013

```bash
var startOf2013 = new Date("2013-01-01T00:00:00Z").getTime();
var endOf2013 = new Date("2013-12-31T23:59:59Z").getTime();

db.earthquakes.find(
  { 
    time: { $gte: startOf2013, $lte: endOf2013 } 
  },
  {
    _id: 0,
    mag: 1,
    time: 1,
  }
  );
```

2. Get the average magnitude of earthquakes in California
```
db.earthquakes.aggregate([
  { $match: { place: /California/ } },
  { $group: { _id: null, avg_magnitude: { $avg: "$mag" } } }
])
```

### Hard

#### 1 Find the closest earthquake to a given location (latitude: 38.8232, longitude: -122.7955)

To filter queries based on the location, we first need to create an index on it:

```bash
dibi> db.earthquakes.createIndex({location: "2dsphere"})
location_2dsphere
```

Only then can we make our query:

```
db.earthquakes.find(
  {
    location: {
      $near: {
        $geometry: {
          type: "Point",
          coordinates: [48.86, 2.35]
        }
      }
    }
  },
  { _id: 0, id: 1, place: 1, location: 1, url: 1 }
).limit(1)
```
---
```output
[
  {
    id: 'usc000gntf',
    place: '135km SSE of Burum, Yemen',
    url: 'http://earthquake.usgs.gov/earthquakes/eventpage/usc000gntf',
    location: { type: 'Point', coordinates: [ 49.561, 13.279 ] }
  }
]
```
