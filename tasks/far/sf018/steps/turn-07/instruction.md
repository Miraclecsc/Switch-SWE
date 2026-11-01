Please check this too: [RAM] Accept service principals and IAM ARNs as resource share principals ## Summary Expanded principal validation in `add_principals` to accept service principals (e.g. `backup.amazonaws.com`) and IAM role/user ARNs in addition to 12-digit account IDs The existing regex only matched `^\d{12}$`, rejecting valid principal types that AWS RAM supports per the [API docs]( ## Tests `test_create_resource_share_with_service_principal`: creates a resource share with `backup.amazonaws.com` as principal `test_create_resource_share_with_iam_role_principal`: creates a resource share with an IAM role ARN as principal Full RAM test suite: 33/33 passing Fixes #9439

implement CreateResourceShare clientToken idempotency in
this RAM backend, including requests with the newly accepted principals.
The AWS SDK RAM service model documents case-sensitive client tokens: repeating
the same token with the same parameters must not create another resource share;
using it with different parameters raises IdempotentParameterMismatchException
(HTTP 400). Return clientToken with resourceShare. When it is omitted, generate
a fresh token and return it so that the caller can explicitly retry that result.
Different tokens, including tokens differing only in case, remain independent.

Each successful retry must preserve the share ARN and avoid duplicating its
principal/resource associations. Compare all request parameters, not just the
name or principal list, even parameters this old backend otherwise ignores.
Keep all previous principal validation and existing tests. Add tests through
the boto3 RAM client as well as the backend where ownership of mutable objects
is relevant.