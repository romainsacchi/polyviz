"""
This module contains the code to generate a Sankey diagram for a given activity and method.
"""

from typing import Union

import bw2data
from d3blocks import D3Blocks

from .dataframe import format_supply_chain_dataframe
from .utils import calculate_supply_chain, check_filepath

try:
    from bw2data.backends.peewee import Activity as PeeweeActivity
except ImportError:
    PeeweeActivity = None

try:
    from bw2data.backends import Activity as BW25Activity
except ImportError:
    BW25Activity = None


def sankey(
    activity: Union[PeeweeActivity, BW25Activity],
    method: tuple = None,
    flow_type: str = None,
    level: int = 3,
    cutoff: float = 0.01,
    filepath: str = None,
    title: str = None,
    notebook: bool = False,
) -> str:
    """
    Generate a Sankey diagram for a given activity and method.
    :param activity: Brightway2 activity
    :param method: tuple representing a Brightway2 method
    :param flow_type: string representing a flow type e.g., "kilogram", "kilowatt hour", "cubic meter", "liter"
    :param level: number of levels to display in the Sankey diagram
    :param cutoff: cutoff value for the Sankey diagram
    :param filepath: Path to save the HTML file
    :param title: Title of the Sankey diagram
    :param notebook: Whether to display the Sankey diagram in a Jupyter notebook
    :return: Path to the generated HTML file
    """

    if level < 2:
        raise ValueError("The level of recursion should be at least 2.")

    title = title or f"{activity['name']} ({activity['unit']}, {activity['location']})"
    filepath = check_filepath(filepath, title, "sankey", method, flow_type)

    result, amount = calculate_supply_chain(activity, method, level, cutoff)

    if method:
        assert isinstance(method, tuple), "`method` should be a tuple."
        dataframe = format_supply_chain_dataframe(result, amount)
        # fetch unit of method
        unit = bw2data.Method(method).metadata["unit"]
    else:
        assert isinstance(flow_type, str), "`flow_type` should be a string."
        assert flow_type in ["kilogram", "kilowatt hour", "cubic meter", "liter"]
        dataframe = format_supply_chain_dataframe(result, amount, flow_type)
        # fetch unit of method
        unit = flow_type

    dataframe["unit"] = unit

    if level != 3:
        figsize = (800 / 3 * level, 600)
    else:
        figsize = (800, 600)

    # dataframe should at least be 3 rows
    if len(dataframe) < 3:
        print("Not enough data to generate a Sankey diagram.")
        return

    # Create a new D3Blocks object
    d3_graph = D3Blocks()
    d3_graph.sankey(
        df=dataframe[1:],
        link={"color": "source-target"},
        title=title,
        filepath=filepath,
        notebook=notebook,
        figsize=figsize,
    )

    return str(filepath)
