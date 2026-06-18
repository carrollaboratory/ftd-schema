# Data Dictionary Format

## Introduction
The data dictionary format is a standardized structure used to define and validate datasets. It ensures consistency and clarity across tools and workflows. This document outlines the required columns, their expectations, and how they are used by various tools.

## Required Columns
The following columns are required for submission:

| Column Name       | Description                                                                 | Data Type       | Required | Notes                                      |
|-------------------|-----------------------------------------------------------------------------|-----------------|----------|--------------------------------------------|
| `variable_name`   | The name of the variable/column in the dataset.                            | `string`        | Yes      | Must be unique and descriptive.            |
| `description`     | A brief description of the variable.                                       | `string`        | Yes      | Should provide context for the variable.   |
| `data_type`       | The data type of the variable (e.g., `integer`, `string`, `enumeration`).  | `string`        | Yes      | Must match predefined data types.          |
| `min`             | The minimum value for numeric variables.                                   | `numeric`       | No       | Leave blank if not applicable.             |
| `max`             | The maximum value for numeric variables.                                   | `numeric`       | No       | Leave blank if not applicable.             |
| `enumerations`    | A list of valid values for categorical variables.                         | `string` (list) | No       | Required if `data_type` is `enumeration`.  |

## Column Details

### `variable_name`
- **Purpose**: Identifies the variable in the dataset.
- **Data Type**: `string`
- **Validation Rules**: Must be unique and non-empty.

### `description`
- **Purpose**: Provides context and explanation for the variable.
- **Data Type**: `string`
- **Validation Rules**: Should not exceed 255 characters.

### `data_type`
- **Purpose**: Specifies the type of data stored in the variable.
- **Data Type**: `string`
- **Validation Rules**: Must be one of the predefined types (`integer`, `string`, `enumeration`, etc.).

### `min` and `max`
- **Purpose**: Define the range of values for numeric variables.
- **Data Type**: `numeric`
- **Validation Rules**: Must be numeric if provided. Leave blank for non-numeric variables.

### `enumerations`
- **Purpose**: Lists valid values for categorical variables.
- **Data Type**: `string` (list)
- **Validation Rules**: Required if `data_type` is `enumeration`. Values must match the regex validation rules.

## Tool-Specific Usage

### `generate_datadictionary`
- **Purpose**: Generates a data dictionary from a dataset.
- **Usage**: Ensures all required columns are populated. Calculates `min` and `max` for numeric variables.

### `merge_datadictionary`
- **Purpose**: Merges multiple data dictionaries into one.
- **Usage**: Validates column consistency across dictionaries.

### `validate_datadictionary`
- **Purpose**: Validates the data dictionary against predefined rules.
- **Usage**: Checks for missing or invalid values in required columns.

## Examples

### Example Data Dictionary

| variable_name | description       | data_type   | min | max | enumerations       |
|---------------|-------------------|-------------|-----|-----|--------------------|
| age           | Age of the person | integer     | 0   | 120 |                    |
| gender        | Gender of person  | enumeration |     |     | Male, Female, Other|
| height        | Height in cm      | numeric     | 50  | 250 |                    |

### Example Usage
```json
{
  "variable_name": "age",
  "description": "Age of the person",
  "data_type": "integer",
  "min": 0,
  "max": 120,
  "enumerations": ""
}
```