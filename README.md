## ``polygraphx``: An interface between ``brightway2`` and [D3.js](https://d3js.org/)

This is a Python package that provides an interface between the
[`brightway2`](https://brightway.dev) LCA framework and the [`D3.js`](https://d3js.org) JavaScript library.
It is designed to be used in Jupyter notebooks, and provides
interactive visualizations of LCA results.

<div style="text-align:center">
<img src="https://github.com/romainsacchi/polyviz/raw/master/docs/chord_sample.png" height="300"/>
</div>

This interface extends the capabilities of  [``d3blocks``](https://github.com/d3blocks/d3blocks), a Python package developed
by [Erdogan Taskesen](https://github.com/erdogant).

``polygraphx`` allows the following visualizations to be created from LCA results:
* Sankey diagrams
* Force-directed graphs
* Chord diagrams
* Violin plots
* Tree maps
* Choropleth maps

## Limitations

Tested only with ``brightway2`` version 2.4.5.

Probably works with version 2.5 too, but not tested.

## Installation

Install ``polygraphx`` from PyPI:

```bash
pip install polyviz
```

Usage
-----

### Sankey diagrams

```python
from polygraphx import sankey
import bw2data

act = bw2data.get_activity(("some db", "some activity"))
method = ("some method", "some method")
sankey(activity=act, method=method)
```

`sankey()` returns a filepath to an HTML file that can be opened in a browser.

Alternatively, you can track a specific flow:

```python

from polygraphx import sankey
import bw2data

act = bw2data.get_activity(("some db", "some activity"))
flow_type = "kilowatt hour"
sankey(activity=act, flow_type=flow_type)
```

Other examples are available in the [examples](github.com/romainsacchi/polyviz/tree/master/examples) folder.

## Support

Do not hesitate to report issues in the Github repository.

## Maintainers

* [Romain Sacchi](https://github.com/romainsacchi)

## Contributing

See [contributing](https://github.com/romainsacchi/carculator/blob/master/CONTRIBUTING.md).

## License

[BSD-3-Clause](https://github.com/romainsacchi/polygraphx/blob/master/LICENSE).
