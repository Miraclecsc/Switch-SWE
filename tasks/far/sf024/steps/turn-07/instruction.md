Please check this too: Add `PlanarEmbedding.dual_graph()` returning a new undirected `nx.MultiGraph`.
For this method let original face IDs be the indices from `list(self.faces())`.
One dual node represents each original face. One dual edge represents each
undirected primal edge, joining the two faces containing its opposite directed
half-edges. Keep parallel edges and self-loops: a triangle has two dual nodes
and three parallel edges; a three-edge tree has one dual node with three loops.
Disconnected primal components have separate component-local duals. Edgeless
embeddings return an empty dual, including when isolated vertices exist.

Return the following usable incidence information:

- `dual.graph["faces"]`: a tuple of original boundary-walk tuples.
- `dual.graph["half_edge_faces"]`: each directed primal endpoint pair maps to
  its original face ID.
- `dual.graph["face_to_node"]`: each original face ID maps to its current dual
  node; without contractions this is the identity map.
- Each dual node has `faces`, a sorted tuple of the original face IDs it contains.
  Its node ID is the smallest of those integer IDs.
- Each dual edge's key is the `frozenset` of its primal endpoints. Its
  `primal_edge` attribute is a two-endpoint tuple in either orientation.

These are public API data semantics, not a required private implementation.
Support arbitrary hashable, mutually unorderable node labels. Validate the
embedding with its existing structural validity contract; malformed embeddings
raise that type exception. Do not mutate the embedding. Returned boundary
containers, incidence dictionaries and graph topology must be detached so later
edits of the input or result cannot change the other's structural data.