"""
This schema used to validate data dictionaries related to study submissions.

This schema should be used to ensure that data dictionaries are in a format
that can be processed by FTD tools. 

A data dictionary that conforms to this schema will be:
 - compatible with MapDragon Table insertion.
 - compatible with the pipeline-utils package dd handlers.
 - compatible with the DEVA package dd handlers.
 - compatible with the kf-inc-injest package dd handlers.

 * Note: Pipeline packages with dd handlers will be modifying the information
 in the data dictionary to fit their needs, but this schema ensures that the
 original data dictionary is in a format that can be processed by all of them.

"""

ALLOWED_DATA_TYPES = [
    "string",
    "integer",
    "number",
    # "float", # 'float' is not a standard Cerberus type, and 'number' can cover both int and float, so we use 'number' instead of 'float'
    "boolean",
    "enumeration",
    "date"
]

schema = {
    "variable_name": {
        "type": "string",
        "required": True,
        "empty": False,
        "regex": "^[A-Za-z_][A-Za-z0-9_]*$",
    },
    "description": {
        "type": "string",
        "nullable": True
    },
    "data_type": {
        "type": "string",
        "required": True,
        "allowed": ALLOWED_DATA_TYPES
    },
    "min": {
        "type": "number",
        "nullable": True,
        "check_with": "numeric_constraints"
    },
    "max": {
        "type": "number",
        "nullable": True,
        "check_with": "numeric_constraints"
    },
    "units": {
        "type": "string",
        "nullable": True
    },
    "enumerations": {
        "type": "string",
        "nullable": True,
        # Accepts: enum1=definition1;enum2=definition2 OR enum1;enum2 (spaces allowed, but not ; or = in names/defs)
        "regex": r"^([^;=]+(=[^;=]+)?)(;[^;=]+(=[^;=]+)?)*$",
    },
    "comment": {
        "type": "string",
        "nullable": True
    },
    "required": {
        "type": "string",
        "nullable": True,
        "allowed": ["yes", "no", None]
    },
}
