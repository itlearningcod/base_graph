# Base Graph Package

A simple and efficient Python library for working with directed graphs.

## Installation
```bash
pip install base_graph
```

## Usage

### Creating a graph

Keyword arguments passed to `BaseGraph` define the node schema — the key names and their types (inferred from the default values). `uid` is reserved and cannot be used as a property name.

```python
from base_graph import BaseGraph

graph = BaseGraph(name="", priority=0, active=True)
```

### Adding and modifying nodes

```python
# Add nodes — returns the assigned uid
task1 = graph.add_node(uid="task-1", name="Design", priority=1, active=True)
task2 = graph.add_node(name="Implement", priority=2, active=True)  # auto uid
task3 = graph.add_node(name="Review", priority=3, active=True)

# Attributes not in the schema or of the wrong type are silently ignored
graph.modify_node(task1, active=False)

# Remove a node — also removes all its edges
graph.del_node(task3)
```

### Adding and querying edges

Edges are directed and typed. The type (`tipo`) is an arbitrary string created on demand.

```python
graph.add_edge(task1, task2, "depends_on")

# Outgoing neighbours of a specific type
graph.get_neighbors(task1, "depends_on")   # {"node-0"}

# Incoming neighbours
graph.get_predecessors(task2, "depends_on")  # {"task-1"}

# All neighbours regardless of type
graph.get_neighbors(task1)

graph.has_edge(task1, task2, "depends_on")  # True
graph.del_edge(task1, task2, "depends_on")
```

### Dynamic ordered edges

`register_ordering` creates a named chain of edges that is automatically kept in sync whenever nodes are added, removed, or modified. Nodes that do not have the ordering property set are placed at the tail of the chain in insertion order.

> **Note:** the edge type (`tipo`) used for an ordering is fully managed by it — any manually added edges of that type will be overwritten on the next rebuild.

```python
graph = BaseGraph(date="", title="")

a = graph.add_node(uid="a", date="2024-03-15", title="March event")
b = graph.add_node(uid="b", date="2024-01-10", title="January event")
c = graph.add_node(uid="c", date="2024-02-20", title="February event")
d = graph.add_node(uid="d", title="Undated event")  # no date

graph.register_ordering("date", "timeline")
# Chain: b → c → a → d  (sorted by date; undated node at tail)

# Adding a new node automatically updates the chain
e = graph.add_node(uid="e", date="2024-01-25", title="Late January")
# Chain: b → e → c → a → d

# Modifying the ordering property also triggers a rebuild
graph.modify_node("b", date="2024-04-01")
# Chain: e → c → a → b → d

# Removing a node closes the gap
graph.del_node("c")
# Chain: e → a → b → d

# Reverse ordering
graph.register_ordering("date", "reverse_timeline", reverse=True)
# Chain: b → a → e → d  (descending; undated still at tail)
```

### Property delegation

Nodes can transparently inherit properties from another node without physically copying them. When an attribute is not set on the delegating node, access falls back to the source node. Local values always win over delegated ones.

```python
graph = BaseGraph(name="", age=0, role="")

base = graph.add_node(uid="base", name="Base", age=30, role="admin")
child = graph.add_node(uid="child", name="Child")  # only has 'name'

graph.delegate_to("child", "base")

node = graph.nodes["child"]
node.name   # "Child"  — local value, not inherited
node.age    # 30       — inherited from base
node.role   # "admin"  — inherited from base
```

**Delegation chains** are supported. If `base` also delegates to another node, the lookup continues along the chain.

**Querying and removing delegation:**

```python
graph.get_delegate("child")   # "base"
graph.undelegate("child")
graph.get_delegate("child")   # None
```

**Ordering constraint (cycle prevention)**

You can designate a schema attribute as the delegation ordering key. When set, `delegate_to` only accepts links that go strictly forward in the ordering direction, which prevents cycles.

```python
graph = BaseGraph(name="", priority=0)
graph.register_delegation_ordering("priority")  # delegation must go low → high

low  = graph.add_node(uid="low",  priority=1, name="Low")
high = graph.add_node(uid="high", priority=5, name="High", role="admin")

graph.delegate_to("low", "high")   # valid: high.priority > low.priority
graph.delegate_to("high", "low")   # raises ValueError — wrong direction
```

Use `reverse=True` for descending ordering (delegation must go high → low).

Nodes that lack the ordering key are exempt from the check and can delegate freely.

**Delegation is persisted** in `save_json`/`load_json` and `to_dict`/`from_dict`, including the ordering config. Deleting a source node automatically clears the delegation on any node that pointed to it.

### Serialization

```python
# JSON — full roundtrip including ordering config
graph.save_json("graph.json")
restored = BaseGraph.load_json("graph.json")

# GraphML — for use with tools like Gephi or Cytoscape
graph.export_graphml("graph.graphml")
restored = BaseGraph.import_graphml("graph.graphml")

# Plain dict
data = graph.to_dict()
restored = BaseGraph.from_dict(data)
```

## Development
```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov

# Run a single test
pytest tests/test_base_graph.py::TestDynamicOrdering::test_add_node_triggers_rebuild -v

# Format
black src/ tests/

# Lint
flake8 src/ tests/
```

## License

MIT License
