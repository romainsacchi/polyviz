"""
Violin plot for a given activity and method.
"""

from typing import Union

import bw2calc
import bw2data
import numpy as np
import pandas as pd

try:
    from bw2calc.monte_carlo import MultiMonteCarlo
except ModuleNotFoundError:
    MultiMonteCarlo = None

from d3blocks import D3Blocks

from .utils import check_filepath

try:
    from bw2data.backends.peewee import Activity
except ImportError:
    from bw2data.backends import Activity


def violin(
    activities: list,
    method: tuple,
    iterations=100,
    filepath: str = None,
    title: str = None,
    notebook: bool = False,
) -> str:
    """
    Generate a Sankey diagram for a given activity and method.
    :param activity: Brightway2 activity
    :param method: tuple representing a Brightway2 method
    :param iterations: Number of iterations for Monte Carlo simulation
    :param filepath: Path to save the HTML file
    :param notebook: If True, the HTML file is displayed in the notebook.
    :param title: Title of the plot
    :return: Path to the generated HTML file
    """

    assert isinstance(method, tuple), "`method` should be a tuple."

    for act in activities:
        assert isinstance(act, Activity), "`activity` should be a Brightway activity."

    def make_name(activities):
        """
        Quickly format the activity name
        :param activities: list of activity names to format
        :return: formatted string
        """
        name = ""
        for act in activities:
            name += f"{act['name'][:10]} ({act['location']}) vs "
        return name[:-4]

    title = title or make_name(activities)

    filepath = check_filepath(filepath, title, "violin", method)

    if MultiMonteCarlo:
        res = MultiMonteCarlo(
            [{act: 1} for act in activities],
            method,
            iterations,
        ).calculate()
    else:
        lca = bw2calc.LCA(
            demand={activities[0]: 1}, method=method, use_distributions=True
        )
        lca.lci()
        lca.lcia()
        res = np.zeros((len(activities), iterations))
        for a, activity in enumerate(activities):
            lca.lci({activity.id: 1})
            res[a, :] = [lca.score for _ in zip(range(iterations), lca)]

    list_res = []
    for r in range(0, res.shape[0]):
        vals = res[r, :]
        list_res.extend(
            [
                [
                    v,
                    f"{activities[r]['name']} ({activities[r]['location']})",
                ]
                for v in vals
            ]
        )

    dataframe = pd.DataFrame(list_res, columns=["val", "name"])

    # fetch unit of method
    unit = bw2data.Method(method).metadata["unit"]

    # Create a new D3Blocks object
    d3_graph = D3Blocks()
    d3_graph.violin(
        x=dataframe["name"].values,
        y=dataframe["val"].values,
        unit=unit,
        bins=50,  # Bins used for the histogram
        figsize=[None, None],  # Figure size is automatically determined.
        filepath=filepath,  # Path to save the HTML file
        notebook=notebook,  # If True, the HTML file is displayed in the notebook.
    )

    return str(filepath)
