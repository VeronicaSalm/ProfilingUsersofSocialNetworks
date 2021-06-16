"""
Contains useful definitions and variables for interfacing with a settings file.

The following configuration variables can be set in a json file:
{
    "num_iterations" : INT,
    "location_source" : STRING
}

where
    num_iterations is the number of SLP iterations to run
    location_source is the name of a tsv.gz file mapping each user
                    ID to their lat and lon coordinates, i.e.,
                                USER_ID\tLAT\tLON
"""

NUM_ITERATIONS = "num_iterations"
LOCATION_SOURCE = "location_source"
