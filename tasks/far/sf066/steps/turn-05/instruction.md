In the checkout at /work/w02, Clausets local community detection algorithm

This PR adds Clauset’s original local community detection (LCD) algorithm. The algorithm enables identification of communities starting from a source node, using a greedy expansion approach based on local modularity optimisation.

This method is particularly advantageous when:
- The complete graph is unknown or only partially observable.
- The graph is too large for global community detection methods to be computationally feasible.

The algorithm is efficient for discovering localized communities without requiring access to global network information, making it useful for applications such as web crawling, social network analysis, or large-scale graph exploration.

There are many LCD algorithms, but Clausets original algorithm will be a good place to start including LCD into NetworkX

 ### References

- The original paper by Clauset (2005) can be found [here](https://arxiv.org/pdf/physics/0503036).
- For a broader introduction to local community detection, see [here](https://doi.org/10.1109/ACCESS.2022.3213980).

This looks like an excellent addition to NetworkX! I haven't looked at the PR in depth yet, but have two requests on a quick look: - can you add a section to the documentation hooks that let sphinx (our doc builder) know where to pull the doc_strings from your module as it builds the docs? The file that is relevant (I think...) is `doc/reference/algorithsm/community.rst` and I think you can copy/paste/change an existing section to make it work with your code. The module name is listed in some preamble stuff, and then the function names are listed with appropriate whitespace around them. - Can you wrap your doc_string lines to something like 80 chars? Code is <88 chars on a line, so the doc_strings look good between 75-88 or so. We don't have an automated tool to do that yet I believe, but we're working on it. Thanks!