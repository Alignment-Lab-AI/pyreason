# PyReason Python Library
pypi project: https://pypi.org/project/pyreason/

## Install
```bash
pip install pyreason
```

## Usage
Example:
```python
import pyreason as pr

pr.load_graph(path_to_graph)
pr.load_rules(path_to_rules)
pr.load_labels(path_to_labels)
pr.load_facts(path_to_facts)
pr.load_inconsistent_predicate_list(path_to_ipl)

pr.settings.verbose = True
interpretation = pr.reason()
```

`load_graph` and `load_rules` have to be called before `pr.reason`. Loading of facts and labels is optional but recommended; if they are not loaded the program will use only the information from attributes in the graphml file.

`settings` contains several parameters that can be modified by the user

`interpretation` is the final interpretation after the reasoning is complete. 