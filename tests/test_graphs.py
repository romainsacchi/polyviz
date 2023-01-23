import bw2analyzer
import bw2calc
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


def test_sankey():
    act = bw2data.Database("Mobility example").random()
    sankey(activity=act, cutoff=0.001, method=method)
    sankey(activity=act, flow_type="kilogram")


def test_chord():
    act = bw2data.Database("Mobility example").random()
    chord(activity=act, cutoff=0.001, method=method)


def test_force():
    act = bw2data.Database("Mobility example").random()
    force(activity=act, cutoff=0.001, method=method)


def test_tree():
    act = bw2data.Database("Mobility example").random()
    treemap(activity=act, cutoff=0.001, method=method)


def test_violin():
    acts = [bw2data.Database("Mobility example").random() for _ in range(5)]

    violin(activities=acts, method=method, iterations=5)


def choropleth():
    act = bw2data.Database("Mobility example").random()
    choro(activity=act, cutoff=0.001, method=method)
