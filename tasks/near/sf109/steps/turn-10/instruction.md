One more thing: Fixed #20024 -- Fixed handling of __in lookups with None in exclude().

The None-aware exclusion result must remain correct when a backend splits large IN lists into smaller clauses. Duplicate None values and all-None lists must behave exactly as without splitting. Keep the original composite-primary-key semantics and avoid modifying lookup inputs during compilation.