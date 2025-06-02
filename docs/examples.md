# Examples  
Note: this is a work in progress and subject to change. Mostly just copy/pasting from developing notebook cells, so this may need tidying up and re-writing into proper documentation.  

Most of the examples assume they are building upon the first example of getting a reference to an item.  

## Get a reference to an item  

For this snippet to work, create a .env file in the project root folder and include a variable called 'LINZ_API_KEY'.  

```python
from dotenv import load_dotenv, find_dotenv
from pykaahma_linz import KServer
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
api_key = os.getenv('LINZ_API_KEY')

#create server object
linz = KServer.KServer(api_key)

#get item object
rail_station_layer_id = "50318" #rail station 175 points
itm = linz.content.get(rail_station_layer_id)
#print item title
print(itm.title)
```

## Query an item using WFS endpoint  

Get all data  
```python  
data = itm.query()
```

Get first 5 records. Could be any records as there doesn't appear to be a sort argument, so probably only useful for data exploration.  
```python
data = itm.query(count=5)
```

Data is returned as a geopandas GeoDataFrame, typed by the fields provided by the API.  
```python
print(data.dtypes())
print(data.head())
```

## Get a changeset using WFS endpoint  

Also returned as a GeoDataFrame.
```python
changeset = itm.get_changeset(from_time="2024-01-01T00:00:00Z")
print((f"Total records returned {itm.title}: {changeset.shape[0]}"))
```

## Generate an export  

```python
job = itm.export("geodatabase", crs="EPSG:2193",)
print(job.status)
```
Download the job data once it is ready. If this method is called before the job is complete, it will keep polling the status of the job until it is ready and then downloads it.  
```python
job.download(folder=r"c:/temp")
```

## Generate an export with extent geometry  

```python
waikato_polygon = {
        "coordinates": [
          [
            [
              174.30400216373914,
              -36.87399457472202
            ],
            [
              174.30400216373914,
              -38.83764306196984
            ],
            [
              176.83017911725346,
              -38.83764306196984
            ],
            [
              176.83017911725346,
              -36.87399457472202
            ],
            [
              174.30400216373914,
              -36.87399457472202
            ]
          ]
        ],
        "type": "Polygon"
      }

job = itm.export("geodatabase", crs="EPSG:2193", extent=waikato_polygon,)
print(job.status)
```

## Export two items synchronously  

This is just an expanded example of above, doing two items, one at a time.

```python
def run_export_sync(itm, export_format, crs, output_folder):
    job = itm.export(export_format, crs=crs)
    print(f"Started export job {job.id}")
    file_path = job.download(output_folder)
    print(f"{job.id} downloaded to {file_path}")
    return file_path

def export_multiple_items_sync():
    output_folder = r"c:\temp\data\sync"

    logging.info("Starting multiple export jobs synchronously...")
    start_time = time.time()
    result1 = run_export_sync(itm, "geodatabase", "EPSG:2193", output_folder)
    result2 = run_export_sync(itm2, "geodatabase", "EPSG:2193", output_folder)
    end_time = time.time()
    logging.info(f"Both export jobs completed in {end_time - start_time:.2f} seconds")

    print(f"Both exports completed: {str([result1, result2])}")

# Call main_sync() in a normal script or notebook cell
export_multiple_items_sync()
```

## Export two items asynchronously  

This is to contrast the synchronous example, and shows how two jobs could be initiated and downloaded asynchonously.  

The alternative could be just to initiate two jobs seperately, and then write your own logic to poll both every few seconds and download as soon as one is ready.  

```python
def run_export_sync(itm, export_format, crs, output_folder):
    job = itm.export(export_format, crs=crs)
    print(f"Started export job {job.id}")
    file_path = job.download(output_folder)
    print(f"{job.id} downloaded to {file_path}")
    return file_path

def export_multiple_items_sync():
    output_folder = r"c:\temp\data\sync"

    logging.info("Starting multiple export jobs synchronously...")
    start_time = time.time()
    result1 = run_export_sync(itm, "geodatabase", "EPSG:2193", output_folder)
    result2 = run_export_sync(itm2, "geodatabase", "EPSG:2193", output_folder)
    end_time = time.time()
    logging.info(f"Both export jobs completed in {end_time - start_time:.2f} seconds")

    print(f"Both exports completed: {str([result1, result2])}")

# Call main_sync() in a normal script or notebook cell
export_multiple_items_sync()
```