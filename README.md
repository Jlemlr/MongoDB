# Report MongoDB
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
- create a new database and open the json file from the github repository you downloaded

You can directly write your queries in the UI of MongoDb Compass.

## Queries

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

6. Find earthquakes that happened in the last 24 hours NOT WORKING
```
var twentyFourHoursAgo = Date.now() - 24 * 60 * 60 * 1000;
db["Earthquake"].find({ time: { $gte: twentyFourHoursAgo } })
```

### Complex

>Find the top 5 strongest earthquakes
```
db["Earthquake"].find({}).sort({ mag: -1 }).limit(5)
```

>Get the average magnitude of earthquakes in California
```
db["Earthquake"].aggregate([
  { $match: { place: /California/ } },
  { $group: { _id: null, avg_magnitude: { $avg: "$mag" } } }
])
```

### Hard

>Find the closest earthquake to a given location (latitude: 38.8232, longitude: -122.7955)
```
db["Earthquake"].createIndex({ location: "2dsphere" })
db["Earthquake"].find({
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [-122.7955, 38.8232]
      }
    }
  }
}).limit(1)
```
