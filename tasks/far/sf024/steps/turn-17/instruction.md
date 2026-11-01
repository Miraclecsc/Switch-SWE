Also, Extend the method to `dual_graph(*, contract_edges=())`. The argument is a
single-pass iterable of primal endpoint pairs selecting edges to contract in
the **dual**, not in the primal embedding. Transitive contractions merge incident
face regions. Remove exactly the selected dual edges; retain every unselected
edge, including loops that already existed or are created by merging faces.
Selecting a primal bridge only removes its corresponding dual loop. Keep
resulting dual nodes even when all their edges have been selected.

Repeated selections and reversed endpoint pairs are idempotent. Consume the
argument once. Invalid endpoint pairs, wrong-length entries and edges absent
from the embedding raise `NetworkXError`; input structure remains unchanged.
Contractions cannot merge disconnected components without an actual connecting
dual edge.

Maintain original face provenance: `faces` and `half_edge_faces` still describe
the original embedding, including darts of selected edges. `face_to_node`
reflects the resulting regions. Each result node is the minimum original face
ID in its region, with all member IDs in its sorted `faces` tuple. Edge incidence
uses the resulting region nodes. Do not sort the primal node labels.

The method belongs on `PlanarEmbedding`, keeping representation-dependent
half-edge traversal and incidence bookkeeping inside the class. No particular
union/find implementation, error wording, or edge endpoint orientation is required.