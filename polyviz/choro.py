"""
Module that contains code to produce a Choropleth diagram.
"""

from typing import Union

import bw2data
from d3blocks import D3Blocks

from .dataframe import distribute_region_impacts
from .utils import check_filepath, get_geo_distribution_of_impacts_for_choro_graph

try:
    from bw2data.backends.peewee import Activity as PeeweeActivity
except ImportError:
    PeeweeActivity = None

try:
    from bw2data.backends import Activity as BW25Activity
except ImportError:
    BW25Activity = None


def choro(
    activity: Union[PeeweeActivity, BW25Activity],
    method: tuple,
    cutoff: float = 0.001,
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
    filepath = check_filepath(filepath, title, "choro", method)

    assert isinstance(method, tuple), "`method` should be a tuple."
    assert isinstance(
        activity, (PeeweeActivity, BW25Activity)
    ), "`activity` should be a brightway2 activity."

    # fetch unit of method
    unit = bw2data.Method(method).metadata["unit"]

    dataframe = get_geo_distribution_of_impacts_for_choro_graph(
        activity, method, cutoff
    )
    dataframe = distribute_region_impacts(dataframe, cutoff=cutoff)
    dataframe["unit"] = unit

    if len(dataframe) > 0:
        # Create a new D3Blocks object
        d3_graph = D3Blocks()
        d3_graph.choro(
            df=dataframe,
            title=title,
            filepath=filepath,
            notebook=notebook,
            figsize=figsize,
        )

        return str(filepath)

    else:
        print("No data to plot.")
        return None
