# Tests  

To run all tests:  

To run all tests with logging. Leave off the log parameter if not wanting logging.  
```bash
uv run -m pytest --log-cli-level=INFO
```  

To run a specific test, replace the relevant file name and test function.  
```bash
uv run -m pytest tests/test_simple.py::test_validate_layer_export_params --log-cli-level=INFO
```  

