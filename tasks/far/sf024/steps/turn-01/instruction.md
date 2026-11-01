I have this in /work/w03: Implement `PlanarEmbedding.faces()` on the original NetworkX base. Enumerate
component-local facial boundary walks with each directed half-edge visited once.
Walk order and repeated nodes matter, especially around bridges and cut vertices.
Isolated vertices yield no walks. Disconnected components do not identify a
single common outer face. Encapsulate traversal bookkeeping in the class.
Preserve all 44 original required tests and the input embedding.