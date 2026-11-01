For the checkout at /work/w01, Fix for issue #7645: Do not preserve 'cw' and 'ccw' attributes in PlanarEmbedding.to_undirected()

I propose this fix for [issue #7645](https://github.com/networkx/networkx/issues/7645). The changes ensure that the 'cw' and 'ccw' attributes are not preserved for both graphs and multi-graphs in the result of PlanarEmbedding.to_undirected().

I have included tests to verify that the issue is resolved.

I would be grateful for any feedback or suggestions to improve this PR. I am more than happy to incorporate any necessary changes based on the review. Thank you for your time and guidance!

Fixes #7645

Fix for issue #7645: Do not preserve 'cw' and 'ccw' attributes in PlanarEmbedding.to_undirected() I propose this fix for [issue #7645]( The changes ensure that the 'cw' and 'ccw' attributes are not preserved for both graphs and multi-graphs in the result of PlanarEmbedding.to_undirected(). I have included tests to verify that the issue is resolved. I would be grateful for any feedback or suggestions to improve this PR. I am more than happy to incorporate any necessary changes based on the review. Thank you for your time and guidance! Fixes #7645

My update has now added an overload of the `to_undirected()` method to the class `PlanarEmbedding`. I have removed the parameter and corresponding functionality, because in my understanding its not relevant for planarity. Am I correct? For the `as_view `parameter I am actually not sure if its useful or not. I left the parameter but did not write a test (yet), until ist confirmed that this functionality is wanted in class `PlanarEmbedding`. Thank you for your support. Looking forward to your feedback.