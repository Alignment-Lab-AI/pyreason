import networkx as nx
import numba

import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge
import pyreason.scripts.numba_wrapper.numba_types.node_type as node
import pyreason.scripts.numba_wrapper.numba_types.edge_type as edge
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


class GraphmlParser:
    def __init__(self):
        self.graph = None
        self.non_fluent_facts = None
        
    def parse_graph(self, graph_path):
        self.graph = nx.read_graphml(graph_path)
        return self.graph

    def parse_graph_attributes(self, timesteps):
        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node.node_type))
        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge.edge_type))
        for n in self.graph.nodes:
            for key, value in self.graph.nodes[n].items():
                l = f'{key}-{value}'
                if label.Label(l) not in specific_node_labels.keys():
                    specific_node_labels[label.Label(l)] = numba.typed.List.empty_list(node.node_type)
                specific_node_labels[label.Label(l)].append(node.Node(n))
                f = fact_node.Fact(node.Node(n), label.Label(l), interval.closed(1, 1), 0, timesteps, static=True)
                facts_node.append(f)
        for e in self.graph.edges:
            for key, value in self.graph.edges[e].items():
                l = f'{key}-{value}'
                if label.Label(l) not in specific_edge_labels.keys():
                    specific_edge_labels[label.Label(l)] = numba.typed.List.empty_list(edge.edge_type)
                specific_edge_labels[label.Label(l)].append(edge.Edge(e[0], e[1]))
                f = fact_edge.Fact(edge.Edge(e[0], e[1]), label.Label(l), interval.closed(1, 1), 0, timesteps, static=True)
                facts_edge.append(f)

        return facts_node, facts_edge, specific_node_labels, specific_edge_labels                
