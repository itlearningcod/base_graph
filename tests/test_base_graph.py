import pytest
from base_graph import BaseGraph, Node


class TestNode:
    """Test per la classe Node"""
    
    def test_node_creation_with_uid(self):
        """Test creazione nodo con uid"""
        node = Node("test-1", name="Test Node")
        assert node.uid == "test-1"
        assert node.name == "Test Node"
    
    def test_node_creation_with_multiple_attributes(self):
        """Test creazione nodo con attributi multipli"""
        node = Node("test-2", name="Node", value=42, active=True)
        assert node.uid == "test-2"
        assert node.name == "Node"
        assert node.value == 42
        assert node.active is True
    
    def test_node_str_representation(self):
        """Test rappresentazione stringa del nodo"""
        node = Node("test-3")
        assert str(node) == "test-3"
    
    def test_node_repr_representation(self):
        """Test rappresentazione repr del nodo"""
        node = Node("test-4")
        assert repr(node) == "test-4"
    
    def test_node_update(self):
        """Test aggiornamento attributi del nodo"""
        node = Node("test-5", name="Original", value=10)
        node.update(name="Updated", value=20, new_attr="New")
        
        assert node.name == "Updated"
        assert node.value == 20
        assert node.new_attr == "New"
    
    def test_node_equality(self):
        """Test confronto tra nodi basato su uid"""
        node1 = Node("test-6", name="Node1")
        node2 = Node("test-6", name="Node2")
        node3 = Node("test-7", name="Node1")
        
        assert node1 == node2  # Stesso uid
        assert node1 != node3  # Uid diverso
    
    def test_node_hash(self):
        """Test che i nodi possono essere usati in set e dict"""
        node1 = Node("test-8")
        node2 = Node("test-9")
        node3 = Node("test-8")  # Stesso uid di node1
        
        node_set = {node1, node2, node3}
        assert len(node_set) == 2  # node1 e node3 sono lo stesso
        
        node_dict = {node1: "value1", node2: "value2"}
        assert node_dict[node3] == "value1"  # node3 ha stesso uid di node1


class TestGraph:
    """Test per la classe BaseGraph"""
    
    def test_graph_initialization_empty(self):
        """Test inizializzazione grafo vuoto"""
        graph = BaseGraph()
        assert graph.nodes == {}
        assert graph.edges == {}
        assert graph.rev_edges == {}
        assert graph.progress == 0
        assert graph.keys == {}
    
    def test_graph_initialization_with_keys(self):
        """Test inizializzazione grafo con chiavi"""
        graph = BaseGraph(name="", value=0, active=True)
        assert graph.keys == {"name": "", "value": 0, "active": True}
    
    def test_next_auto_uid_sequential(self):
        """Test generazione UID automatici sequenziali"""
        graph = BaseGraph()
        uid1 = graph.next_auto_uid()
        uid2 = graph.next_auto_uid()
        uid3 = graph.next_auto_uid()
        
        assert uid1 == "node-0"
        assert uid2 == "node-1"
        assert uid3 == "node-2"
    
    def test_next_auto_uid_skips_existing(self):
        """Test che auto UID salta quelli già esistenti"""
        graph = BaseGraph()
        graph.nodes["node-0"] = Node("node-0")
        
        uid = graph.next_auto_uid()
        assert uid == "node-1"
    
    def test_check_validity(self):
        """Test validazione degli attributi"""
        graph = BaseGraph(name="", value=0, active=True)
        
        # Attributi validi
        valid = graph.check_validity(name="Test", value=42, active=False)
        assert valid == {"name": "Test", "value": 42, "active": False}
        
        # Attributi con tipo sbagliato
        invalid = graph.check_validity(name="Test", value="wrong_type")
        assert invalid == {"name": "Test"}  # value escluso
        
        # Chiave non definita
        unknown = graph.check_validity(name="Test", unknown_key="value")
        assert unknown == {"name": "Test"}  # unknown_key escluso
    
    def test_add_node_with_auto_uid(self):
        """Test aggiunta nodo con UID automatico"""
        graph = BaseGraph(name="", value=0)
        uid = graph.add_node(name="Test", value=42)
        
        assert uid == "node-0"
        assert len(graph.nodes) == 1
        assert "node-0" in graph.nodes
        assert graph.nodes["node-0"].name == "Test"
        assert graph.nodes["node-0"].value == 42
    
    def test_add_node_with_custom_uid(self):
        """Test aggiunta nodo con UID personalizzato"""
        graph = BaseGraph(name="")
        uid = graph.add_node(uid="custom-1", name="Custom Node")
        
        assert uid == "custom-1"
        assert "custom-1" in graph.nodes
        assert graph.nodes["custom-1"].uid == "custom-1"
        assert graph.nodes["custom-1"].name == "Custom Node"
    
    def test_add_node_with_duplicate_uid_uses_auto(self):
        """Test che UID duplicati generano auto-UID"""
        graph = BaseGraph(name="")
        uid1 = graph.add_node(uid="test-1", name="First")
        uid2 = graph.add_node(uid="test-1", name="Second")
        
        assert uid1 == "test-1"
        assert uid2 == "node-0"  # Auto-generato
        assert graph.nodes["test-1"].name == "First"
        assert graph.nodes["node-0"].name == "Second"
    
    def test_add_node_invalid_attributes_ignored(self):
        """Test che attributi non validi vengono ignorati"""
        graph = BaseGraph(name="", value=0)
        graph.add_node(name="Valid", value=10, invalid_key="Ignored", wrong_type=["list"])
        
        node = graph.nodes["node-0"]
        assert node.name == "Valid"
        assert node.value == 10
        assert not hasattr(node, "invalid_key")
        assert not hasattr(node, "wrong_type")
    
    def test_modify_node(self):
        """Test modifica attributi di un nodo esistente"""
        graph = BaseGraph(name="", value=0, active=True)
        uid = graph.add_node(name="Original", value=10, active=False)
        
        graph.modify_node(uid, name="Modified", value=20)
        
        assert graph.nodes[uid].name == "Modified"
        assert graph.nodes[uid].value == 20
        assert graph.nodes[uid].active == False  # Non modificato
    
    def test_modify_node_nonexistent_raises_error(self):
        """Test che modificare un nodo inesistente solleva errore"""
        graph = BaseGraph(name="")
        
        with pytest.raises(KeyError, match="does not exist"):
            graph.modify_node("nonexistent", name="Test")
    
    def test_modify_node_invalid_attributes_ignored(self):
        """Test che attributi non validi sono ignorati in modify_node"""
        graph = BaseGraph(name="", value=0)
        uid = graph.add_node(name="Test", value=10)
        
        graph.modify_node(uid, name="Updated", invalid_key="Ignored")
        
        assert graph.nodes[uid].name == "Updated"
        assert not hasattr(graph.nodes[uid], "invalid_key")
    
    def test_del_node(self):
        """Test rimozione di un nodo"""
        graph = BaseGraph()
        uid = graph.add_node()
        
        assert uid in graph.nodes
        graph.del_node(uid)
        assert uid not in graph.nodes
    
    def test_del_node_nonexistent_raises_error(self):
        """Test che rimuovere un nodo inesistente solleva errore"""
        graph = BaseGraph()
        
        with pytest.raises(KeyError, match="does not exist"):
            graph.del_node("nonexistent")
    
    def test_del_node_removes_edges(self):
        """Test che rimuovere un nodo rimuove anche i suoi archi"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        
        graph.add_edge(v1, v2, "link")
        graph.add_edge(v2, v3, "link")
        graph.add_edge(v1, v3, "other")
        
        # Rimuovi v2
        graph.del_node(v2)
        
        # Gli archi con v2 devono essere rimossi
        assert not graph.has_edge(v1, v2, "link")
        assert not graph.has_edge(v2, v3, "link")
        # L'arco v1->v3 deve rimanere
        assert graph.has_edge(v1, v3, "other")
    
    def test_add_edge_between_existing_nodes(self):
        """Test aggiunta arco tra nodi esistenti"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        
        graph.add_edge(v1, v2, "connection")
        
        assert "connection" in graph.edges
        assert v1 in graph.edges["connection"]
        assert v2 in graph.edges["connection"][v1]
        assert "connection" in graph.rev_edges
        assert v2 in graph.rev_edges["connection"]
        assert v1 in graph.rev_edges["connection"][v2]
    
    def test_add_edge_nonexistent_source_raises_error(self):
        """Test che aggiungere arco con sorgente inesistente solleva errore"""
        graph = BaseGraph()
        v2 = graph.add_node()
        
        with pytest.raises(KeyError, match="Source node"):
            graph.add_edge("nonexistent", v2, "link")
    
    def test_add_edge_nonexistent_target_raises_error(self):
        """Test che aggiungere arco con target inesistente solleva errore"""
        graph = BaseGraph()
        v1 = graph.add_node()
        
        with pytest.raises(KeyError, match="Target node"):
            graph.add_edge(v1, "nonexistent", "link")
    
    def test_add_multiple_edges_same_type(self):
        """Test aggiunta di più archi dello stesso tipo"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        
        graph.add_edge(v1, v2, "links")
        graph.add_edge(v1, v3, "links")
        graph.add_edge(v2, v3, "links")
        
        assert len(graph.edges["links"][v1]) == 2
        assert v2 in graph.edges["links"][v1]
        assert v3 in graph.edges["links"][v1]
    
    def test_add_multiple_edge_types(self):
        """Test aggiunta di archi con tipi diversi"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        
        graph.add_edge(v1, v2, "type_a")
        graph.add_edge(v1, v2, "type_b")
        
        assert "type_a" in graph.edges
        assert "type_b" in graph.edges
        assert v2 in graph.edges["type_a"][v1]
        assert v2 in graph.edges["type_b"][v1]
    
    def test_del_edge(self):
        """Test rimozione di un arco specifico"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        
        graph.add_edge(v1, v2, "connection")
        assert graph.has_edge(v1, v2, "connection")
        
        graph.del_edge(v1, v2, "connection")
        assert not graph.has_edge(v1, v2, "connection")
    
    def test_del_edge_cleans_empty_structures(self):
        """Test che del_edge rimuove strutture vuote"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        
        graph.add_edge(v1, v2, "link")
        graph.del_edge(v1, v2, "link")
        
        # Le strutture vuote devono essere rimosse
        assert "link" not in graph.edges
        assert "link" not in graph.rev_edges
    
    def test_del_edge_nonexistent_safe(self):
        """Test che rimuovere un arco inesistente non causa errori"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        
        # Non dovrebbe causare errori
        graph.del_edge(v1, v2, "nonexistent")
        graph.del_edge("fake", v2, "link")
    
    def test_has_edge(self):
        """Test verifica esistenza arco"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        
        graph.add_edge(v1, v2, "link")
        
        assert graph.has_edge(v1, v2, "link") is True
        assert graph.has_edge(v2, v1, "link") is False  # Direzione opposta
        assert graph.has_edge(v1, v3, "link") is False  # Arco inesistente
        assert graph.has_edge(v1, v2, "other") is False  # Tipo diverso
    
    def test_get_neighbors(self):
        """Test ottenimento vicini (successori)"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        v4 = graph.add_node()
        
        graph.add_edge(v1, v2, "link")
        graph.add_edge(v1, v3, "link")
        graph.add_edge(v1, v4, "other")
        
        # Vicini di tipo "link"
        neighbors_link = graph.get_neighbors(v1, "link")
        assert neighbors_link == {v2, v3}
        
        # Vicini di tipo "other"
        neighbors_other = graph.get_neighbors(v1, "other")
        assert neighbors_other == {v4}
        
        # Tutti i vicini
        all_neighbors = graph.get_neighbors(v1)
        assert all_neighbors == {v2, v3, v4}
    
    def test_get_neighbors_empty(self):
        """Test get_neighbors per nodo senza vicini"""
        graph = BaseGraph()
        v1 = graph.add_node()
        
        neighbors = graph.get_neighbors(v1)
        assert neighbors == set()
    
    def test_get_neighbors_nonexistent_raises_error(self):
        """Test che get_neighbors su nodo inesistente solleva errore"""
        graph = BaseGraph()
        
        with pytest.raises(KeyError, match="does not exist"):
            graph.get_neighbors("nonexistent")
    
    def test_get_predecessors(self):
        """Test ottenimento predecessori"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        v4 = graph.add_node()
        
        graph.add_edge(v1, v4, "link")
        graph.add_edge(v2, v4, "link")
        graph.add_edge(v3, v4, "other")
        
        # Predecessori di tipo "link"
        pred_link = graph.get_predecessors(v4, "link")
        assert pred_link == {v1, v2}
        
        # Predecessori di tipo "other"
        pred_other = graph.get_predecessors(v4, "other")
        assert pred_other == {v3}
        
        # Tutti i predecessori
        all_pred = graph.get_predecessors(v4)
        assert all_pred == {v1, v2, v3}
    
    def test_get_predecessors_empty(self):
        """Test get_predecessors per nodo senza predecessori"""
        graph = BaseGraph()
        v1 = graph.add_node()
        
        predecessors = graph.get_predecessors(v1)
        assert predecessors == set()
    
    def test_get_predecessors_nonexistent_raises_error(self):
        """Test che get_predecessors su nodo inesistente solleva errore"""
        graph = BaseGraph()
        
        with pytest.raises(KeyError, match="does not exist"):
            graph.get_predecessors("nonexistent")
    
    def test_neighbors_returns_copy(self):
        """Test che get_neighbors restituisce una copia (non modifica originale)"""
        graph = BaseGraph()
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        
        graph.add_edge(v1, v2, "link")
        
        neighbors = graph.get_neighbors(v1, "link")
        neighbors.add(v3)  # Modifica la copia
        
        # L'originale non deve essere modificato
        assert v3 not in graph.edges["link"][v1]


class TestGraphIntegration:
    """Test di integrazione per scenari complessi"""
    
    def test_complex_graph_scenario(self):
        """Test scenario complesso con nodi e archi multipli"""
        graph = BaseGraph(name="", weight=0)
        
        # Crea una rete di nodi
        a = graph.add_node(uid="A", name="Node A", weight=10)
        b = graph.add_node(uid="B", name="Node B", weight=20)
        c = graph.add_node(uid="C", name="Node C", weight=30)
        d = graph.add_node(uid="D", name="Node D", weight=40)
        
        # Crea archi
        graph.add_edge(a, b, "parent")
        graph.add_edge(a, c, "parent")
        graph.add_edge(b, d, "parent")
        graph.add_edge(a, d, "skip")
        
        # Verifica struttura
        assert len(graph.nodes) == 4
        assert graph.get_neighbors(a, "parent") == {b, c}
        assert graph.get_predecessors(d, "parent") == {b}
        assert graph.has_edge(a, d, "skip")
    
    def test_graph_modification_workflow(self):
        """Test workflow completo: creazione, modifica, rimozione"""
        graph = BaseGraph(name="", status="", priority=0)
        
        # Crea nodi
        task1 = graph.add_node(name="Task 1", status="todo", priority=1)
        task2 = graph.add_node(name="Task 2", status="todo", priority=2)
        task3 = graph.add_node(name="Task 3", status="todo", priority=3)
        
        # Crea dipendenze
        graph.add_edge(task1, task2, "depends_on")
        graph.add_edge(task2, task3, "depends_on")
        
        # Modifica stato
        graph.modify_node(task1, status="done")
        assert graph.nodes[task1].status == "done"
        
        # Rimuovi task intermedio
        graph.del_node(task2)
        
        # Verifica che le dipendenze siano aggiornate
        assert task2 not in graph.nodes
        assert not graph.has_edge(task1, task2, "depends_on")
        assert not graph.has_edge(task2, task3, "depends_on")
        assert len(graph.nodes) == 2
    
    def test_circular_dependencies(self):
        """Test gestione dipendenze circolari"""
        graph = BaseGraph()
        
        v1 = graph.add_node()
        v2 = graph.add_node()
        v3 = graph.add_node()
        
        # Crea ciclo
        graph.add_edge(v1, v2, "next")
        graph.add_edge(v2, v3, "next")
        graph.add_edge(v3, v1, "next")
        
        # Verifica che il ciclo esista
        assert v2 in graph.get_neighbors(v1, "next")
        assert v3 in graph.get_neighbors(v2, "next")
        assert v1 in graph.get_neighbors(v3, "next")
    
    def test_multiple_edge_types_same_nodes(self):
        """Test nodi connessi con più tipi di archi"""
        graph = BaseGraph()
        
        person1 = graph.add_node()
        person2 = graph.add_node()
        
        graph.add_edge(person1, person2, "friend")
        graph.add_edge(person1, person2, "colleague")
        graph.add_edge(person1, person2, "neighbor")
        
        # Verifica che esistano tutti i tipi
        assert graph.has_edge(person1, person2, "friend")
        assert graph.has_edge(person1, person2, "colleague")
        assert graph.has_edge(person1, person2, "neighbor")
        
        # Rimuovi un tipo
        graph.del_edge(person1, person2, "colleague")
        
        # Verifica che gli altri tipi rimangano
        assert graph.has_edge(person1, person2, "friend")
        assert not graph.has_edge(person1, person2, "colleague")
        assert graph.has_edge(person1, person2, "neighbor")
