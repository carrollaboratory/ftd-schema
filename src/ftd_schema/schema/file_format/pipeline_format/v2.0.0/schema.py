"""Validation schema for pipeline data dictionaries in the expanded(2.0.0) table format."""

# Supports canonical types plus SQL-like varchar(N) values used in table specs.
DATA_TYPE_REGEX = (
    r"^(string|integer|number|float|boolean|enumeration|date|datetime|quantity|"
    r"varchar\([1-9][0-9]*\))$"
)

YES_NO_ALLOWED = ["Yes", "No", "yes", "no", None]

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
        "regex": DATA_TYPE_REGEX,
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
        "nullable": True,
    },
    "Required": {
        "type": "string",
        "nullable": True,
        "allowed": YES_NO_ALLOWED,
    },
    "Primary Key": {
        "type": "string",
        "nullable": True,
        "allowed": YES_NO_ALLOWED,
    },
    "Foreign Key": {
        "type": "string",
        "nullable": True,
        "allowed": YES_NO_ALLOWED,
    },
    "FK Table": {
        "type": "string",
        "nullable": True,
    },
    "FK Domain": {
        "type": "string",
        "nullable": True,
    },
    "tests": {
        "type": "string",
        "nullable": True,
    },
}
