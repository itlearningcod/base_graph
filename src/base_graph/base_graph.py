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

    def next_auto_uid(self):
        uid = f'node-{self.progress}'
        self.progress += 1
        if uid in self.nodes:
            return self.next_auto_uid()
        return uid

    def check_validity(self, **kwargs):
        """Valida kwargs contro le chiavi definite nel grafo"""
        valid_dict_pairs = {}
        for key, value in kwargs.items():
            if key in self.keys and isinstance(value, type(self.keys[key])):
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
        return uid  # Utile per sapere quale uid è stato assegnato

    def modify_node(self, uid, **kwargs):
        """Modifica attributi di un nodo esistente"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")
        
        valid_dict_pairs = self.check_validity(**kwargs)
        self.nodes[uid].update(**valid_dict_pairs)
    
    def del_node(self, uid):
        """Rimuove un nodo e tutti i suoi archi"""
        if uid not in self.nodes:
            raise KeyError(f"Node with uid '{uid}' does not exist")
        
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
        return (tipo in self.edges and 
                v1 in self.edges[tipo] and 
                v2 in self.edges[tipo][v1])


class Node:
    def __init__(self, uid: str, **kwargs):
        self.uid = uid
        for key, value in kwargs.items():
            setattr(self, key, value)

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
