# Base Graph Package

Una libreria Python semplice ed efficiente per lavorare con grafi.

## Installazione
```bash
pip install base_graph
```

## Uso rapido
```python
from base_graph import BaseGraph, Node

# Crea un grafo con attributi tipizzati
graph = BaseGraph(name="", priority=0, active=True)

# Aggiungi nodi
task1 = graph.add_node(name="Task 1", priority=1, active=True)
task2 = graph.add_node(name="Task 2", priority=2, active=True)

# Aggiungi archi
graph.add_edge(task1, task2, "depends_on")

# Interroga il grafo
neighbors = graph.get_neighbors(task1, "depends_on")
print(neighbors)  # {task2}

# Modifica nodi
graph.modify_node(task1, active=False)

# Rimuovi nodi (rimuove anche gli archi)
graph.del_node(task1)
```

## Caratteristiche

- ✅ Nodi con attributi tipizzati
- ✅ Archi multi-tipo
- ✅ Navigazione bidirezionale (successori e predecessori)
- ✅ Gestione automatica degli UID
- ✅ Validazione dei tipi
- ✅ Test completi

## Sviluppo
```bash
# Clona il repository
git clone https://github.com/itlearningcod/base_graph.git
cd base_graph

# Installa in modalità sviluppo
pip install -e ".[dev]"

# Esegui i test
pytest tests/ -v --cov

# Formatta il codice
black src/ tests/
```

## Licenza

MIT License
