"""
Module that contains code to produce a Choropleth diagram.
"""

from d3blocks import D3Blocks
import bw2data

from .utils import get_geo_distribution_of_impacts_for_choro_graph, check_filepath
from .dataframe import distribute_region_impacts


def choro(
    activity: bw2data.backends.peewee.proxies.Activity,
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
    filepath = check_filepath(filepath, title, "choro")

    assert isinstance(method, tuple), "`method` should be a tuple."
    assert isinstance(
        activity, bw2data.backends.peewee.proxies.Activity
    ), "`activity` should be a brightway2 activity."

    # fetch unit of method
    unit = bw2data.Method(method).metadata["unit"]

    dataframe = get_geo_distribution_of_impacts_for_choro_graph(activity, method, cutoff)
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
