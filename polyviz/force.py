"""
This module contains the code to produce a force-directed graph.
"""

import bw2data
from d3blocks import D3Blocks

from .dataframe import format_supply_chain_dataframe
from .utils import calculate_supply_chain, check_filepath


def force(
    activity: bw2data.backends.peewee.proxies.Activity,
    method: tuple,
    level: int = 3,
    cutoff: float = 0.01,
    filepath: str = None,
    title: str = None,
    notebook: bool = False,
) -> str:
    """
    Generate a force-directed graph for a given activity and method.
    :param activity: Brightway2 activity
    :param method: tuple representing a Brightway2 method
    :param level: Maximum level of recursion
    :param cutoff: Minimum value of the impact to be displayed
    :param filepath: Path to save the HTML file
    :param title: Title of the force-directed graph
    :param notebook: Whether to display the force-directed graph in a Jupyter notebook
    :return: Path to the generated HTML file
    """

    if level < 2:
        raise ValueError("The level of recursion should be at least 2.")

    title = title or f"{activity['name']} ({activity['unit']}, {activity['location']})"
    filepath = check_filepath(filepath, title, "force")

    result, amount = calculate_supply_chain(activity, method, level, cutoff)

    dataframe = format_supply_chain_dataframe(result, amount)

    figsize = (800, 600)

    # dataframe should at least be 3 rows
    if len(dataframe) < 3:
        raise ValueError("No enough data to generate a Chord diagram.")

    # Create a new D3Blocks object
    d3_graph = D3Blocks()
    d3_graph.d3graph(
        df=dataframe[1:],
        title=title,
        filepath=filepath,
        notebook=notebook,
        figsize=figsize,
    )

    return str(filepath)
