# Development Notes  

These are just general notes for the author to help remember design choices, rabbit holes and how they panned out, etc.  

## Development using Jupyter Notebooks  
I got the following tips from Cookie Cutter Data Science.  
[Cookie Cutter Data Science](https://cookiecutter-data-science.drivendata.org/)  

Make the project a python package and install it locally. I was using UV, so I ran this command:
```
uv pip install -e .  
```  
Then, in my notebook, I included this cell first:  
```jupyter
%load_ext autoreload
%autoreload 2
```  
This allowed me to load my local python package like this:  
```jupyter  
from k_data_helpers import KServer  
```  
And it would hot reload any changes I made while developing.

## Notes on design choices  

### OWSLib  
I investigated using the OWSLib python package to download the WFS data, but discovered that it doesn't support the CQL filter keyword option that the LINZ GeoServer provides. OGC filters were still an option, but seem very complex to construct and I believe most users would prefer to use the simpler CQL which is more similar to SQL. So I moved back to using a basic request to the WFS endpoint. The OWSLib package would provide more scope for expansion, but since the intent of this helper library is primarily focused on Koordinates and LINZ in particular, we can afford to be a little more opinionated on our approach, such as not having to support all the WFS versions.  
I'm not sure if the LINZ WFS endpoint is strictly equivalent with all other Koordinates WFS endpoints. So the implementation at the moment is coded to work with LINZ and might not work in other places.  


