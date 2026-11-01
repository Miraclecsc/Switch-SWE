Also, i think we usually use `request.applymarker`

Preserve the storage backend and the reduction's natural dtype, including promotion of integer mean/variance results to floating dtype. String reductions retain their string storage and missing-value convention. Reducing must not mutate the original array or its mask.