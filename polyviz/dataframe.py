"""
This module contains functions to format the result of
the recursive calculation into a pandas dataframe.
"""

from collections import defaultdict
from io import StringIO
from typing import List

import pandas as pd
import numpy as np
import bw2data


from .utils import calculate_lcia_score, get_region_definitions, get_gdp_per_country



def format_supply_chain_dataframe(
    results: List[List], amount: int = 1, flow_type: str = None
) -> pd.DataFrame:
    """
    Format the result of the recursive calculation into a pandas dataframe.
    :param result: string containing the result of the recursive calculation
    :param amount: reference amount
    :param flow_type: if not None, only keep flows with a matching unit
    :return: a pandas dataframe
    """

    list_res = []
    last_supplier = {}

    for result in results:
        level, _, impact, amount, name, location, unit = result
        last_supplier[level] = f"{name} ({location})"

        if not flow_type:
            list_res.append(
                [
                    f"{name} ({location})" if location else name,
                    f"{name} ({location})" if level == 0 else last_supplier[level - 1],
                    impact,
                    level
                ]
            )
        else:
            if unit == flow_type:
                list_res.append(
                    [
                        f"{name} ({location})" if location else name,
                        f"{name} ({location})" if level == 0 else last_supplier[level - 1],
                        amount,
                        level
                    ]
                )

    dataframe = pd.DataFrame(list_res, columns=["source", "target", "weight", "level"])
    dataframe = dataframe.replace("market for", "m. for", regex=True)
    dataframe = dataframe.replace("market group for", "m. gr. for", regex=True)

    # sum duplicate rows
    dataframe = dataframe.groupby(["source", "target", "level"]).sum().reset_index()

    # reorder by level and target
    dataframe = dataframe.sort_values(by=["level", "target"])

    # remove negative values
    if amount > 0:
        dataframe = dataframe[dataframe["weight"] > 0]
    else:
        dataframe.loc[dataframe["weight"] < 0, "weight"] *= -1

    # add rows representing emissions
    if not flow_type:
        for level in dataframe["level"].unique():
            for i, row in dataframe.loc[dataframe["level"] == level].iterrows():
                if row["source"] not in ["loss", "activities below cutoff", "emissions"] and level + 1 in dataframe["level"].unique():
                    sum_emissions = row["weight"]
                    downstream_emissions = find_downstream_emissions(dataframe, row["source"], level)

                    if downstream_emissions < sum_emissions:
                        # insert a row with the missing emissions
                        dataframe = pd.concat(
                            [
                                dataframe,
                                pd.DataFrame(
                                    {
                                        "source": "emissions",
                                        "target": row["source"],
                                        "weight": sum_emissions - downstream_emissions,
                                        "level": level + 1,
                                    },
                                    index = [0]
                                ),
                            ],
                            ignore_index=True
                        )

        # reorder by level and target
        dataframe = dataframe.sort_values(by=["level", "target"])

    # drop the `level` column
    dataframe = dataframe.drop(labels="level", axis=1)

    return dataframe

def find_downstream_emissions(
        dataframe: pd.DataFrame,
        target: str,
        level: int,
):
    return dataframe.loc[
        (dataframe["level"] == level + 1)
        & (dataframe["target"] == target),
        "weight",
    ].sum()


def add_country_column(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Add a column with the country of the activity.
    :param dataframe: a pandas dataframe
    :return: a pandas dataframe with a new column
    """
    # extract the country from the `source` column
    dataframe["country"] = dataframe["source"].apply(lambda x: x.split("(")[-1].strip(")"), 1)
    return dataframe

def get_geo_distribution_of_impacts(
        activity: bw2data.backends.peewee.proxies.Activity,
        method: tuple,
        cutoff: float = 0.0001,
):
    """
    Get a pandas dataframe with the distribution of impacts per country.
    :param activity: a brightway2 activity
    :param method: a tuple representing a brightway2 method
    :param cutoff: a cutoff value for the impact
    :return: a pandas dataframe
    """

    score, c_matrix, rev = calculate_lcia_score(activity, method)

    results = defaultdict(dict)
    for nz_idx in np.argwhere(c_matrix > cutoff * score):
        act = bw2data.get_activity(rev[nz_idx[1]])

        if act["name"] not in results[act["location"]]:
            results[act["location"]][act["name"]] = 0

        results[act["location"]][act["name"]] += c_matrix[0, nz_idx[1]]

    countries = []
    activities = []

    for country, value in results.items():
        countries.append(country)
        activities.append(pd.DataFrame.from_dict(value, orient="index"))

    dataframe = pd.concat(activities, keys=countries)
    dataframe = dataframe.reset_index()

    # rename columns
    dataframe.columns = ["country", "activity", "weight"]

    # aggregate the rows for which the weight is less than 1% of the total weight
    # and rename the country as "other"
    dataframe.loc[dataframe["weight"] < dataframe["weight"].sum() * 0.01, "country"] = "other"

    # create a column "name" which concatenates "country" and "activity"
    dataframe["name"] = dataframe["country"] + "." + dataframe["activity"]

    return dataframe

def distribute_region_impacts(dataframe, cutoff):
    """
    Distribute the impacts of a region to the countries of the region.
    :param dataframe: pandas dataframe with the impact distribution per region
    :param cutoff: a cutoff value for the impact
    :return: pandas dataframe
    """

    regions = get_region_definitions()
    gdp = get_gdp_per_country()

    for i, row in dataframe.loc[dataframe["country"].isin(regions)].iterrows():
        # find the counrties of the region
        # and distirbute the impact of the region to the countries
        # based on their GDP
        countries = regions.get(row["country"], [])

        if countries:
            # sum of gdp
            gdp_sum = 0
            for country in countries:
                gdp_sum += gdp.get(country, 0)

            # distribute the impact
            for country in countries:
                if country in gdp:
                    # add a row for the country
                    dataframe = pd.concat(
                        [
                            dataframe,
                            pd.DataFrame(
                                {
                                    "country": country,
                                    "weight": row["weight"] * gdp.get(country, 0) / gdp_sum,
                                },
                                index = [0]
                            ),
                        ]
                    )

    # remove the rows of the regions
    dataframe = dataframe.loc[~dataframe["country"].isin(regions)]

    # remove the rows with a weight inferior to 1%
    # of the sum
    dataframe = dataframe.loc[dataframe["weight"] > dataframe["weight"].sum() * cutoff]


    return dataframe
