Please check this too: Please also add a test for the import, using `with pytest.warns(DeprecationWarning, ...):`

Verify legacy pickle class references for both module paths resolve with the deprecation warning; new instances must round-trip through pickle as the corrected exception class without a deprecation warning.