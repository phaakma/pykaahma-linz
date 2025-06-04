# pykaahma-linz
A Pythonic client for accessing and querying datasets from the LINZ Data Service.

## Overview  
pykaahma-linz is a Python package that provides a clean, Pythonic interface to the Koordinates geospatial content management system. It allows users to connect to the Koordinates API, retrieve metadata, and query datasets such as vector layers, tables, rasters, and point clouds. As the name indicates, this was written with LINZ (Land Information New Zealand) in mind and simplifies programmatic access to their open geospatial data. 

Source code and documentation available at [Github repo](https://github.com/phaakma/pykaahma-linz)  

## Disclaimer  
This is a hobby project and the modules are provided as-is on a best-effort basis and you assume all risk for using it.  
The author has no affiliation with either Koordinates nor LINZ. As such, the underlying API's and services may change at any time without warning and break these modules. The author is not privvy to any inside knowledge or documentation beyond what is available online or by inspecting the payloads returned by the services.  

This project does not cover the full spectrum of the Koordinates API and probably never will. It focuses currently on basic workflows such as connecting using an api key, getting references to datasets and downloading them. The package has not been tested against any other Koordinates deployment and there may be LINZ specific logic buried in the code. 

The author is happy to take feedback and consider suggestions and code contributions as time allows. Preferred method for feedback is via the Github repository issues page.    

## Installation  

Documentation is non-existent at the moment, but here is the basic approach so far. 
 
```bash
pip install pykaahma-linz
```

## Usage  

* Import KServer.  
* Create a KServer object, passing in an api key.  
* Get a reference to an item using {kserver}.content.get({layer_id})
* Perform actions on the item.  

Basic example:  
```python
from pykaahma_linz.KServer import KServer
linz = KServer(api_key)
rail_station_layer_id = "50318"
itm = linz.content.get(rail_station_layer_id)
data = itm.query()
data.head()
```

## Tests  
Tests are written using pytest. To run tests using UV:  

```bash
uv run -m pytest --log-cli-level=INFO
```

There is currently very limited test coverage. Any live tests require a "LINZ_API_KEY" entry to exist in a .env file in the root project folder.  