"""
This module contains the function to generate a treemap.
"""

import bw2data
from d3blocks import D3Blocks
from typing import Union

from .dataframe import get_geo_distribution_of_impacts
from .utils import check_filepath

try:
    from bw2data.backends.peewee import Activity as PeeweeActivity
except ImportError:
    PeeweeActivity = None

try: 
    from bw2data.backends import Activity as BW25Activity
except ImportError:
    BW25Activity = None

def treemap(
    activity: Union[PeeweeActivity, BW25Activity],
    method: tuple,
    cutoff: float = 0.0001,
    filepath: str = None,
    title: str = None,
    notebook: bool = False,
    figsize: tuple = (1000, 500),
) -> str:
    """
    Generate a choropleth diagram for a given activity and method.
    :param activity: Brightway2 activity
    :param method: tuple representing a Brightway2 method
    :param cutoff: Cutoff value for the impact
    :param filepath: Path to save the HTML file
    :param title: Title of the plot
    :param notebook: Whether to display the plot in a notebook
    :param figsize: Size of the plot
    :return: Path to the generated HTML file
    """

    title = title or f"{activity['name']} ({activity['unit']}, {activity['location']})"
    filepath = check_filepath(filepath, title, "treemap", method)

    assert isinstance(method, tuple), "`method` should be a tuple."
    assert isinstance(
        activity, (PeeweeActivity, BW25Activity)
    ), "`activity` should be a brightway2 activity."

    # fetch unit of method
    unit = bw2data.Method(method).metadata["unit"]

    # create a pandas dataframe
    # and categorize impacts per country
    dataframe = get_geo_distribution_of_impacts(activity, method, cutoff)
    dataframe["unit"] = unit

    # Create a new D3Blocks object
    d3_graph = D3Blocks()
    d3_graph.treemap(
        df=dataframe,
        title=title,
        filepath=filepath,
        notebook=notebook,
        figsize=figsize,
    )

    return str(filepath)
