import bw2data
import bw2io

from polyviz import chord, choro, force, sankey, treemap, violin

if "polyviz" in bw2data.projects:
    bw2data.projects.delete_project("polyviz", delete_dir=True)

bw2data.projects.set_current("polyviz")

if "Mobility example" in bw2data.databases:
    del bw2data.databases["Mobility example"]
bw2io.bw2setup()
bw2io.add_example_database()

method = ("IPCC", "simple")
bw2data.Method(method).metadata["unit"] = "kg CO2-eq."

act = bw2data.get_activity(("Mobility example", "Electricity"))

def test_force():
    force(activity=act, cutoff=0.001, method=method, level=2)


def test_violin():
    acts = [act, act]
    violin(activities=acts, method=method, iterations=5)


def choropleth():
    choro(activity=act, cutoff=0.001, method=method)
