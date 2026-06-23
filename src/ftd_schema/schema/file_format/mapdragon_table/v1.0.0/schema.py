"""
This schema is used to validate data dictionaries intended for direct import
into the MapDragon table.

A data dictionary that conforms to this schema will be:
 - compatible with MapDragon Table insertion.

Differences from pipeline_format schema:
 - Broader set of allowed data types (quantity, float, datetime are also valid).
 - Variable names may contain spaces and mixed casing (no strict identifier regex).
 - Duplicate variable names are permitted; later rows overwrite earlier ones on import.

"""

ALLOWED_DATA_TYPES = [
    "string",
    "integer",
    "number",
    "float",
    "quantity",
    "boolean",
    "enumeration",
    "date",
    "datetime",
]

schema = {
    "variable_name": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "description": {
        "type": "string",
        "nullable": True,
    },
    "data_type": {
        "type": "string",
        "required": True,
        "allowed": ALLOWED_DATA_TYPES,
    },
    "min": {
        "type": "number",
        "nullable": True,
        "check_with": "numeric_constraints",
    },
    "max": {
        "type": "number",
        "nullable": True,
        "check_with": "numeric_constraints",
    },
    "units": {
        "type": "string",
        "nullable": True,
    },
    "enumerations": {
        "type": "string",
        "nullable": True,
        # Accepts: enum1=definition1;enum2=definition2  OR  enum1;enum2
        # Spaces are allowed within names/values; semicolons and equals signs are delimiters only.
        "regex": r"^([^;=]+(=[^;=]+)?)(;[^;=]+(=[^;=]+)?)*$",
    },
    "comment": {
        "type": "string",
        "nullable": True,
    },
}
