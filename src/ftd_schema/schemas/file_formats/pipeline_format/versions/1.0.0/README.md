# Pipeline Format Schema v1.0.0

This directory contains the schema for validating pipeline data dictionary files.

The Pipeline Format defines the expected structure and metadata for data dictionaries that describe study submissions and are processed by FTD pipeline tools.

## Files

- `schema.py` - Cerberus validation schema for pipeline format data dictionaries

## Compatibility

This schema ensures data dictionaries are compatible with:
- MapDragon Table insertion
- pipeline-utils package dd handlers
- DEVA package dd handlers
- kf-inc-injest package dd handlers

## Usage

```python
from schema import schema
from cerberus import Validator

v = Validator(schema)
data_dict = [...]  # Your data dictionary records
if v.validate(data_dict):
    print("Valid!")
else:
    print(v.errors)
```
