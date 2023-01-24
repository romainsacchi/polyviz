"""
Utility functions for polyviz.
"""

from collections import defaultdict
from io import StringIO
from pathlib import Path

import bw2calc
import bw2data
import numpy as np
import pandas as pd
import yaml


def calculate_supply_chain(
    activity: bw2data.backends.peewee.proxies.Activity,
    method: tuple,
    level: int = 3,
    cutoff: float = 0.01,
) -> [StringIO, int]:
    """
    Calculate the supply chain of an activity.
    :param activity: a brightway2 activity
    :param method: a tuple representing a brightway2 method
    :param level: the maximum level of the supply chain
    :param cutoff: the cutoff value for the supply chain
    :return: a StringIO object and the reference amount
    """

    assert isinstance(
        activity, bw2data.backends.peewee.proxies.Activity
    ), "`activity` should be a brightway2 activity."

    amount = -1 if identify_waste_process(activity) else 1

    print("Calculating supply chain score...")

    try:
        results = recursive_calculation(
            activity,
            method or list(bw2data.methods)[0],
            cutoff=cutoff,
            max_level=level,
            amount=amount,
        )
    except ZeroDivisionError as err:
        raise ZeroDivisionError(
            "Could not compute the recursive calculation because "
            "one of the flows has a null impact value."
        ) from err

    return results, amount


def calculate_lcia_score(
    activity: bw2data.backends.peewee.proxies.Activity,
    method: tuple,
) -> float:
    """
    Calculate the LCIA score for a given activity and method.
    :param activity: Brightway2 activity
    :param method: tuple representing a Brightway2 method
    :return: LCIA score, C matrix, and reverse dictionary
    """
    assert isinstance(
        activity, bw2data.backends.peewee.proxies.Activity
    ), "`activity` should be a brightway2 activity."

    print("Calculating LCIA score...")

    amount = -1 if identify_waste_process(activity) else 1
    lca = bw2calc.LCA({activity: amount}, method)
    lca.lci()
    lca.lcia()
    rev, _, _ = lca.reverse_dict()
    c_matrix = lca.characterized_inventory.sum(0)

    return lca.score, c_matrix, rev


def make_name_safe(filename: str) -> str:
    """
    Make a filename safe for saving.
    :param filename: filename to make safe
    :return: safe filename
    """
    # https://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c == " "]
    ).rstrip()


def identify_waste_process(activity: bw2data.backends.peewee.proxies.Activity) -> bool:
    """
    Identify if a process is a waste process.
    :param activity: a brightway2 activity
    :return: boolean
    """
    # check if reference flow amount is negative
    for exc in activity.production():
        if exc["amount"] < 0:
            return True
    return False


def get_geo_distribution_of_impacts_for_choro_graph(
    activity: bw2data.backends.peewee.proxies.Activity,
    method: tuple,
    cutoff: float = 0.0001,
) -> pd.DataFrame:
    """
    Get the geographic distribution of impacts for a given activity and method.
    :param activity: a brightway2 activity
    :param method: a tuple representing a brightway2 method
    :param cutoff: a cutoff value for the impact
    :return: a pandas dataframe with the geographic distribution of impacts
    """

    amount = -1 if identify_waste_process(activity) else 1
    lca = bw2calc.LCA({activity: amount}, method)
    lca.lci()
    lca.lcia()

    rev, _, _ = lca.reverse_dict()

    c_matrix = lca.characterized_inventory.sum(0)

    results = defaultdict(float)

    for nz_idx in np.argwhere(c_matrix > cutoff * lca.score):
        results[bw2data.get_activity(rev[nz_idx[1]])["location"]] += c_matrix[
            0, nz_idx[1]
        ]

    dataframe = pd.DataFrame.from_dict(results, orient="index", columns=["weight"])

    # make index a column
    # and name it "country"
    dataframe = dataframe.reset_index().rename(columns={"index": "country"})

    return dataframe


def check_filepath(
        filepath: str,
        title: str,
        graph_type: str,
        method: tuple = None,
        flow_type: str = None
) -> Path:
    """
    Check if a filepath exists.
    :param filepath: a filepath
    :param title: a title
    :param graph_type: a graph type
    :param method: an LCIA method
    :param flow_type: a flow type
    :return: filepath
    """
    if filepath is None:
        method = method or flow_type
        filepath = Path.cwd() / f"{make_name_safe(title)} {make_name_safe(''.join(method))} {graph_type}.html"
    else:
        filepath = Path(filepath)

    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True)

    return filepath


def recursive_calculation(
    activity,
    lcia_method,
    amount=1,
    max_level=3,
    cutoff=1e-2,
    lca_obj=None,
    total_score=None,
    level=0,
    previous_activity=None,
    results=None,
):
    """
    ADAPTED FROM BRIGHTWAY2-ANALYZER:
    https://github.com/brightway-lca/brightway2-analyzer/blob/0d2b14a13d631cba7537793670ea87361b349c64/bw2analyzer/utils.py#L88

    Traverse a supply chain graph, and calculate the LCA scores of each component.
    Return the results as a list of lists.

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        lcia_method: tuple. LCIA method to use when traversing supply chain graph.
        amount: int. Amount of ``activity`` to assess.
        max_level: int. Maximum depth to traverse.
        cutoff: float. Fraction of total score to use as cutoff when deciding whether to traverse deeper.
        lca_obj: ``LCA``. Internal argument (used during recursion, do not touch).
        total_score: float. Internal argument (used during recursion, do not touch).
        level: int. Internal argument (used during recursion, do not touch).

    Internal args (used during recursion, do not touch);
        level: int.
        lca_obj: ``LCA``.
        total_score: float.
        first: bool.

    Returns:
        A list of lists, where each list is a row in the output table.

    """

    if lca_obj is None:
        lca_obj = bw2calc.LCA({activity: amount}, lcia_method)
        lca_obj.lci()
        lca_obj.lcia()
        total_score = lca_obj.score
        results = []
    elif total_score is None:
        raise ValueError
    else:
        lca_obj.redo_lcia({activity: amount})
        if abs(lca_obj.score) <= abs(total_score * cutoff):
            results.append(
                [
                    level,
                    lca_obj.score / total_score,
                    lca_obj.score,
                    float(amount),
                    "activities below cutoff",
                    None,
                    None,
                ]
            )
            return results

    if (
        activity["name"],
        activity["reference product"],
        activity["location"],
    ) == previous_activity:
        results.append(
            [
                level,
                lca_obj.score / total_score,
                lca_obj.score,
                float(amount),
                "loss",
                None,
                None,
            ]
        )
        return results

    results.append(
        [
            level,
            lca_obj.score / total_score,
            lca_obj.score,
            float(amount),
            activity["name"],
            activity["location"],
            activity["unit"],
        ]
    )

    if level < max_level:
        for exc in activity.technosphere():
            recursive_calculation(
                activity=exc.input,
                lcia_method=lcia_method,
                amount=amount * exc["amount"],
                max_level=max_level,
                cutoff=cutoff,
                lca_obj=lca_obj,
                total_score=total_score,
                level=level + 1,
                previous_activity=(
                    activity["name"],
                    activity["reference product"],
                    activity["location"],
                ),
                results=results,
            )

    return results


def get_gdp_per_country():
    """
    Get GDP per country from yaml file
    :return: dictionary with GDP per country
    """
    # load yaml file GDP_countries.yaml
    # in data folder
    with open(Path(__file__).parent / "data" / "GDP_countries.yaml", "r") as file:
        gdp_per_country = yaml.safe_load(file)

    return gdp_per_country


def get_region_definitions():
    """
    Get region definitions from yaml file
    :return: dictionary with region definitions
    """
    # load yaml file regions.yaml
    # in data folder
    with open(Path(__file__).parent / "data" / "regions.yaml", "r") as file:
        region_definitions = yaml.safe_load(file)

    return region_definitions
