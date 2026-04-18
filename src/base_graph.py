class BaseGraph:
    """Graph to represent various things"""

    def __init__(self, **kwargs):
        # available keys and type values for nodes
        self.keys = {k: v for k, v in kwargs.items() if k != "uid"}
        # for automatic node uid generation
        self.progress = 0
        self.nodes = {}
        # edges and reverse flow edges
        self.edges = {}
        self.rev_edges = {}
        # dynamic orderings: {tipo: {"key": str, "reverse": bool}}
        self._orderings = {}
        # delegation ordering constraint
        self._delegation_key = None
        self._delegation_reverse = False

    def add_property(self, key, value):
        if key == "uid":
            raise KeyError(f"Cannot use key '{key}', reserved")
        if key in self.keys:
            raise KeyError(f"key '{key}' already present")
        self.keys[key] = value

    def next_auto_uid(self):
        uid = f"node-{self.progress}"
        self.progress += 1
        if uid in self.nodes:
            return self.next_auto_uid()
        return uid

    def check_validity(self, **kwargs):
        """Valida kwargs contro le chiavi definite nel grafo"""
        valid_dict_pairs = {}
        for key, value in kwargs.items():
            if (
                key != "uid"
                and key in self.keys
                and isinstance(value, type(self.keys[key]))
            ):
                valid_dict_pairs[key] = value
        return valid_dict_pairs

    def add_node(self, **kwargs):
        """Aggiunge un nodo al grafo"""
        # Estrai uid se presente
        uid = None
        if "uid" in kwargs:
            uid_str = str(kwargs["uid"])
            if uid_str not in self.nodes:
                uid = uid_str

        # Se uid non fornito o già esistente, genera automaticamente
        if not uid or uid in self.nodes:
            uid = self.next_auto_uid()

        # Valida gli altri attributi (escluso uid)
        valid_dict_pairs = self.check_validity(**kwargs)

        # Crea e aggiungi il nodo
        new_node = Node(uid, **valid_dict_pairs)
        self.nodes[uid] = new_node
        for tipo in self._orderings:
            self._rebuild_ordering(tipo)
        return uid  # Utile per sapere quale uid è stato assegnato

    def modify_node(self, uid, **kwargs):
        """Modifica attributi di un nodo esistente"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")

        valid_dict_pairs = self.check_validity(**kwargs)
        self.nodes[uid].update(**valid_dict_pairs)
        for tipo, config in self._orderings.items():
            if config["key"] in valid_dict_pairs:
                self._rebuild_ordering(tipo)

    def del_node(self, uid):
        """Rimuove un nodo e tutti i suoi archi"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")

        # Clear _delegate on nodes that were delegating to this uid
        for delegating_uid in list(self.rev_edges.get("_delegates", {}).get(uid, set())):
            try:
                object.__delattr__(self.nodes[delegating_uid], "_delegate")
            except AttributeError:
                pass

        # Rimuovi tutti gli archi in uscita
        for tipo in list(self.edges.keys()):
            if uid in self.edges[tipo]:
                for target in list(self.edges[tipo][uid]):
                    self.del_edge(uid, target, tipo)

        # Rimuovi tutti gli archi in entrata
        for tipo in list(self.rev_edges.keys()):
            if uid in self.rev_edges[tipo]:
                for source in list(self.rev_edges[tipo][uid]):
                    self.del_edge(source, uid, tipo)

        # Rimuovi il nodo
        del self.nodes[uid]
        for tipo in self._orderings:
            self._rebuild_ordering(tipo)

    def register_ordering(self, key: str, tipo: str, reverse: bool = False) -> None:
        """Register a dynamic ordering that chains nodes sorted by a property.

        Creates and maintains directed edges of type `tipo` forming a linked-list
        chain of all nodes ordered by the value of `key`. Nodes that do not have
        the `key` attribute set are placed at the tail in stable insertion order.

        The edge type `tipo` is fully owned by this ordering — any manually added
        edges of that tipo will be overwritten on the next rebuild.

        Args:
            key: Schema attribute name to sort by. Must exist in self.keys.
            tipo: Edge type string to use for the chain edges.
            reverse: If True, sort in descending order.

        Raises:
            KeyError: If `key` is not in the graph schema.
        """
        if key not in self.keys:
            raise KeyError(f"Key '{key}' is not in graph schema")
        self._orderings[tipo] = {"key": key, "reverse": reverse}
        self._rebuild_ordering(tipo)

    def register_delegation_ordering(self, key: str, reverse: bool = False) -> None:
        """Set which schema attribute governs delegation direction (prevents cycles).

        When set, delegate_to() requires the source node's key value to be
        strictly ahead of the delegating node's key value in the ordering direction.
        Nodes that lack the key attribute are exempt from this check.

        Args:
            key: Schema attribute name to use as the ordering key.
            reverse: If True, delegation must go in descending order of key values.

        Raises:
            KeyError: If key is not in the graph schema.
        """
        if key not in self.keys:
            raise KeyError(f"Key '{key}' is not in graph schema")
        self._delegation_key = key
        self._delegation_reverse = reverse

    def delegate_to(self, uid: str, source_uid: str) -> None:
        """Make node uid inherit missing properties from source_uid.

        Local attributes always take priority over delegated ones.
        Chains are supported: if source_uid also delegates, the lookup
        continues along the chain.

        Args:
            uid: The delegating node.
            source_uid: The node to delegate to.

        Raises:
            KeyError: If either node does not exist.
            ValueError: If uid == source_uid, or if the delegation violates
                        the registered delegation ordering constraint.
        """
        if uid not in self.nodes:
            raise KeyError(f"Node '{uid}' not found")
        if source_uid not in self.nodes:
            raise KeyError(f"Node '{source_uid}' not found")
        if uid == source_uid:
            raise ValueError("A node cannot delegate to itself")

        # Ordering direction constraint
        if self._delegation_key is not None:
            key = self._delegation_key
            uid_val = getattr(self.nodes[uid], key, None)
            src_val = getattr(self.nodes[source_uid], key, None)
            if uid_val is not None and src_val is not None:
                if not self._delegation_reverse and src_val <= uid_val:
                    raise ValueError(
                        f"Delegation from '{uid}' ({key}={uid_val}) to '{source_uid}' "
                        f"({key}={src_val}) violates ascending ordering constraint"
                    )
                if self._delegation_reverse and src_val >= uid_val:
                    raise ValueError(
                        f"Delegation from '{uid}' ({key}={uid_val}) to '{source_uid}' "
                        f"({key}={src_val}) violates descending ordering constraint"
                    )

        # Remove existing delegation if any
        self.undelegate(uid)

        # Add edge for persistence + wire the reference
        self.add_edge(uid, source_uid, "_delegates")
        self.nodes[uid]._delegate = self.nodes[source_uid]

    def undelegate(self, uid: str) -> None:
        """Remove any delegation from node uid.

        Raises:
            KeyError: If the node does not exist.
        """
        if uid not in self.nodes:
            raise KeyError(f"Node '{uid}' not found")
        if "_delegates" in self.edges and uid in self.edges["_delegates"]:
            for source_uid in list(self.edges["_delegates"][uid]):
                self.del_edge(uid, source_uid, "_delegates")
        try:
            object.__delattr__(self.nodes[uid], "_delegate")
        except AttributeError:
            pass

    def get_delegate(self, uid: str) -> "str | None":
        """Return the uid of the node that uid delegates to, or None.

        Raises:
            KeyError: If the node does not exist.
        """
        if uid not in self.nodes:
            raise KeyError(f"Node '{uid}' not found")
        targets = self.edges.get("_delegates", {}).get(uid, set())
        return next(iter(targets)) if targets else None

    def _rebuild_ordering(self, tipo: str) -> None:
        """Wipe and rebuild the chain edges for a registered ordering."""
        config = self._orderings[tipo]
        key = config["key"]
        reverse = config["reverse"]

        node_list = list(self.nodes.keys())

        with_key = [
            (getattr(self.nodes[uid], key), i, uid)
            for i, uid in enumerate(node_list)
            if hasattr(self.nodes[uid], key)
        ]
        without_key = [
            (i, uid)
            for i, uid in enumerate(node_list)
            if not hasattr(self.nodes[uid], key)
        ]

        # Sort by (attr_value, insertion_index) for stability
        with_key.sort(key=lambda x: (x[0], x[1]))
        if reverse:
            # Re-sort descending on attr value; ties stay in ascending insertion order
            with_key.sort(key=lambda x: x[0], reverse=True)

        chain = [uid for *_, uid in with_key] + [uid for _, uid in without_key]

        # Wipe existing edges of this tipo
        for v1 in list(self.edges.get(tipo, {}).keys()):
            for v2 in list(self.edges[tipo][v1]):
                self.del_edge(v1, v2, tipo)

        # Rebuild chain as a linked list
        for i in range(len(chain) - 1):
            self.add_edge(chain[i], chain[i + 1], tipo)

    def add_edge(self, v1: str, v2: str, tipo: str):
        """Aggiunge un arco tra due nodi"""
        if v1 not in self.nodes:
            raise KeyError(f"Source node '{v1}' does not exist")
        if v2 not in self.nodes:
            raise KeyError(f"Target node '{v2}' does not exist")

        self.edges.setdefault(tipo, {})
        self.rev_edges.setdefault(tipo, {})
        self.edges[tipo].setdefault(v1, set())
        self.edges[tipo][v1].add(v2)
        self.rev_edges[tipo].setdefault(v2, set())
        self.rev_edges[tipo][v2].add(v1)

    def del_edge(self, v1: str, v2: str, tipo: str):
        """Rimuove un arco specifico tra due nodi"""
        if tipo in self.edges:
            if v1 in self.edges[tipo]:
                self.edges[tipo][v1].discard(v2)
                # Pulizia: rimuovi chiave se set vuoto
                if not self.edges[tipo][v1]:
                    del self.edges[tipo][v1]

            if v2 in self.rev_edges[tipo]:
                self.rev_edges[tipo][v2].discard(v1)
                # Pulizia: rimuovi chiave se set vuoto
                if not self.rev_edges[tipo][v2]:
                    del self.rev_edges[tipo][v2]

            # Pulizia: rimuovi tipo se vuoto
            if not self.edges[tipo]:
                del self.edges[tipo]
            if tipo in self.rev_edges and not self.rev_edges[tipo]:
                del self.rev_edges[tipo]

    def get_neighbors(self, uid: str, tipo: str = None):
        """Ottiene i vicini (successori) di un nodo"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")

        if tipo:
            return self.edges.get(tipo, {}).get(uid, set()).copy()
        else:
            # Tutti i vicini di tutti i tipi
            neighbors = set()
            for edge_dict in self.edges.values():
                if uid in edge_dict:
                    neighbors.update(edge_dict[uid])
            return neighbors

    def get_predecessors(self, uid: str, tipo: str = None):
        """Ottiene i predecessori di un nodo"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")

        if tipo:
            return self.rev_edges.get(tipo, {}).get(uid, set()).copy()
        else:
            # Tutti i predecessori di tutti i tipi
            predecessors = set()
            for edge_dict in self.rev_edges.values():
                if uid in edge_dict:
                    predecessors.update(edge_dict[uid])
            return predecessors

    def has_edge(self, v1: str, v2: str, tipo: str) -> bool:
        """Verifica se esiste un arco tra due nodi"""
        return (
            tipo in self.edges and v1 in self.edges[tipo] and v2 in self.edges[tipo][v1]
        )

    def to_dict(self):
        """Serializza il grafo in un dizionario"""
        return {
            "keys": self.keys,
            "progress": self.progress,
            "nodes": {uid: node.to_dict() for uid, node in self.nodes.items()},
            "edges": {
                tipo: {v1: list(v2_set) for v1, v2_set in edges_dict.items()}
                for tipo, edges_dict in self.edges.items()
            },
            "orderings": self._orderings,
            "delegation_key": self._delegation_key,
            "delegation_reverse": self._delegation_reverse,
        }

    @classmethod
    def from_dict(cls, data):
        """Ricrea un grafo da un dizionario"""
        graph = cls(**data["keys"])
        graph.progress = data["progress"]

        # Ricrea i nodi
        for uid, node_data in data["nodes"].items():
            node = Node(node_data["uid"], **node_data["attributes"])
            graph.nodes[uid] = node

        # Ricrea gli archi
        for tipo, edges_dict in data["edges"].items():
            for v1, v2_list in edges_dict.items():
                for v2 in v2_list:
                    graph.add_edge(v1, v2, tipo)

        # Restore ordering config and rebuild chains
        # (overrides any stored ordering edges from the edges block above)
        for tipo, config in data.get("orderings", {}).items():
            graph._orderings[tipo] = config
            graph._rebuild_ordering(tipo)

        # Restore delegation ordering config
        graph._delegation_key = data.get("delegation_key")
        graph._delegation_reverse = data.get("delegation_reverse", False)

        # Rewire _delegate references from persisted edges
        for delegating_uid, source_list in data.get("edges", {}).get("_delegates", {}).items():
            for source_uid in source_list:
                if delegating_uid in graph.nodes and source_uid in graph.nodes:
                    graph.nodes[delegating_uid]._delegate = graph.nodes[source_uid]

        return graph

    def save_json(self, filepath):
        """Salva il grafo in un file JSON"""
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_json(cls, filepath):
        """Carica il grafo da un file JSON"""
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def export_graphml(self, filepath):
        """Esporta il grafo in formato GraphML per visualizzazione"""
        import xml.etree.ElementTree as ET
        from xml.dom import minidom

        # Crea root element
        graphml = ET.Element("graphml")
        graphml.set("xmlns", "http://graphml.graphdrawing.org/xmlns")
        graphml.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        graphml.set(
            "xsi:schemaLocation",
            "http://graphml.graphdrawing.org/xmlns "
            "http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd",
        )

        # Definisci gli attributi dei nodi (keys)
        key_id = 0
        key_mapping = {}
        for attr_name, attr_value in self.keys.items():
            key_elem = ET.SubElement(graphml, "key")
            key_elem.set("id", f"k{key_id}")
            key_elem.set("for", "node")
            key_elem.set("attr.name", attr_name)

            # Determina il tipo
            if isinstance(attr_value, bool):
                key_elem.set("attr.type", "boolean")
            elif isinstance(attr_value, int):
                key_elem.set("attr.type", "int")
            elif isinstance(attr_value, float):
                key_elem.set("attr.type", "double")
            else:
                key_elem.set("attr.type", "string")

            key_mapping[attr_name] = f"k{key_id}"
            key_id += 1

        # Definisci l'attributo per il tipo di edge
        edge_type_key = ET.SubElement(graphml, "key")
        edge_type_key.set("id", "edge_type")
        edge_type_key.set("for", "edge")
        edge_type_key.set("attr.name", "type")
        edge_type_key.set("attr.type", "string")

        # Crea il grafo
        graph_elem = ET.SubElement(graphml, "graph")
        graph_elem.set("id", "G")
        graph_elem.set("edgedefault", "directed")

        # Aggiungi i nodi
        for uid, node in self.nodes.items():
            node_elem = ET.SubElement(graph_elem, "node")
            node_elem.set("id", uid)

            # Aggiungi gli attributi del nodo
            for attr_name, key_id_str in key_mapping.items():
                if hasattr(node, attr_name):
                    data_elem = ET.SubElement(node_elem, "data")
                    data_elem.set("key", key_id_str)
                    value = getattr(node, attr_name)
                    data_elem.text = (
                        str(value).lower() if isinstance(value, bool) else str(value)
                    )

        # Aggiungi gli archi
        edge_id = 0
        for tipo, edges_dict in self.edges.items():
            for v1, v2_set in edges_dict.items():
                for v2 in v2_set:
                    edge_elem = ET.SubElement(graph_elem, "edge")
                    edge_elem.set("id", f"e{edge_id}")
                    edge_elem.set("source", v1)
                    edge_elem.set("target", v2)

                    # Aggiungi il tipo di edge come attributo
                    data_elem = ET.SubElement(edge_elem, "data")
                    data_elem.set("key", "edge_type")
                    data_elem.text = tipo

                    edge_id += 1

        # Formatta e salva con indentazione
        xml_str = ET.tostring(graphml, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Rimuovi linee vuote extra
        lines = [line for line in pretty_xml.split("\n") if line.strip()]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @classmethod
    def import_graphml(cls, filepath):
        """Importa un grafo da formato GraphML"""
        import xml.etree.ElementTree as ET

        tree = ET.parse(filepath)
        root = tree.getroot()

        # Namespace GraphML
        ns = {"g": "http://graphml.graphdrawing.org/xmlns"}

        # Parse le definizioni delle chiavi
        node_keys = {}
        edge_type_key = None

        for key_elem in root.findall("g:key", ns):
            key_id = key_elem.get("id")
            key_for = key_elem.get("for")
            attr_name = key_elem.get("attr.name")
            attr_type = key_elem.get("attr.type")

            if key_for == "node":
                node_keys[key_id] = {"name": attr_name, "type": attr_type}
            elif key_for == "edge" and attr_name == "type":
                edge_type_key = key_id

        # Determina i keys per il grafo basandosi sui tipi
        graph_keys = {}
        for key_info in node_keys.values():
            attr_name = key_info["name"]
            attr_type = key_info["type"]

            if attr_type == "boolean":
                graph_keys[attr_name] = True
            elif attr_type == "int":
                graph_keys[attr_name] = 0
            elif attr_type == "double":
                graph_keys[attr_name] = 0.0
            else:
                graph_keys[attr_name] = ""

        # Crea il grafo
        graph = cls(**graph_keys)

        # Trova l'elemento graph
        graph_elem = root.find("g:graph", ns)

        # Parse i nodi
        for node_elem in graph_elem.findall("g:node", ns):
            uid = node_elem.get("id")
            node_attrs = {"uid": uid}

            for data_elem in node_elem.findall("g:data", ns):
                key_id = data_elem.get("key")
                if key_id in node_keys:
                    key_info = node_keys[key_id]
                    attr_name = key_info["name"]
                    attr_type = key_info["type"]
                    value_text = data_elem.text

                    # Converti il valore al tipo appropriato
                    if attr_type == "boolean":
                        value = value_text.lower() == "true"
                    elif attr_type == "int":
                        value = int(value_text)
                    elif attr_type == "double":
                        value = float(value_text)
                    else:
                        value = value_text

                    node_attrs[attr_name] = value

            graph.add_node(**node_attrs)

        # Parse gli archi
        for edge_elem in graph_elem.findall("g:edge", ns):
            source = edge_elem.get("source")
            target = edge_elem.get("target")
            edge_type = "default"

            # Cerca il tipo di edge
            if edge_type_key:
                for data_elem in edge_elem.findall("g:data", ns):
                    if data_elem.get("key") == edge_type_key:
                        edge_type = data_elem.text
                        break

            graph.add_edge(source, target, edge_type)

        return graph


class Node:
    def __init__(self, uid: str, **kwargs):
        self.uid = uid
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name: str):
        # Only called when normal attribute lookup fails.
        # Follow the delegation chain if a delegate is set.
        try:
            delegate = object.__getattribute__(self, "_delegate")
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(delegate, name)

    def update(self, **kwargs):
        """Aggiorna attributi del nodo"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return self.uid

    def __repr__(self):
        return self.uid

    def __eq__(self, other):
        """Confronto basato su uid"""
        if isinstance(other, Node):
            return self.uid == other.uid
        return False

    def __hash__(self):
        """Hash basato su uid per permettere uso in set/dict"""
        return hash(self.uid)

    def to_dict(self):
        """Serializza il nodo in un dizionario"""
        return {
            "uid": self.uid,
            "attributes": {
                k: v for k, v in self.__dict__.items()
                if k != "uid" and not k.startswith("_")
            },
        }
