from pyreason.scripts.interpretation.interpretation import Interpretation


class Program:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = []
	specific_edge_labels = []

	def __init__(self, graph, tmax, facts_node, facts_edge, rules, ipl, reverse_graph):
		self._graph = graph
		self._tmax = tmax
		self._facts_node = facts_node
		self._facts_edge = facts_edge
		self._rules = rules
		self._ipl = ipl
		self._reverse_graph = reverse_graph

	def diffusion(self, history):
		# Set up available labels
		Interpretation.available_labels_node = self.available_labels_node
		Interpretation.available_labels_edge = self.available_labels_edge
		Interpretation.specific_node_labels = self.specific_node_labels
		Interpretation.specific_edge_labels = self.specific_edge_labels

		interp = Interpretation(self._graph, self._tmax, history, self._ipl, self._reverse_graph)
		
		interp.start_fp(self._facts_node, self._facts_edge, self._rules)

		return interp		
