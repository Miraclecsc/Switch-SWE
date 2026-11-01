Please check this too: Thanks - refactored and added `algorithms.is_monotonic` with tests.

Keep the new mode linear without sorting/ranking and without mutating caller data. Test nullable numeric/boolean, datetime/NaT, duplicate values, all-missing arrays and non-orderable remaining values, while preserving all original dtype normalization and monotonicity test partitions.