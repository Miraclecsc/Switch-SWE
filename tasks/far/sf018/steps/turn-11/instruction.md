Please check this too: Tighten RAM principal regex and add missing test coverage Restrict service principal pattern from [\w.-]+ to [a-z0-9-]+ to reject uppercase and underscore characters that are not valid service names Support aws-cn and aws-us-gov partitions in IAM principal ARN matching Add tests for IAM user ARN, root principal, and invalid principal rejection

For this emulator (these lifecycle and
comparison details are explicit emulator requirements, not additional claims
about undocumented AWS retention/ordering guarantees):

* Normalize absent principals/resourceArns to [] and absent
  allowExternalPrincipals to True when comparing requests. Mapping key order
  is irrelevant; list order and multiplicity remain significant. Other
  parameters retain their supplied values.
* A successful token belongs to this RAM backend's account/region and lasts
  until backend reset. It is not a global token. Failed principal or resource
  validation must not reserve a token or publish a partial share. The existing
  add_principals already validates the whole batch before appending: preserve
  that behavior rather than inventing or weakening it.
* Check a previously successful token before constructing/revalidating a new
  share. Exact replay returns the original creation response snapshot, even
  if the live share was later renamed/deleted or its organizational-unit
  principal no longer exists. It must not resurrect or roll back live state.
  A changed request with that token must fail as a parameter mismatch.
* Own deep snapshots of the request and response. Caller mutation of nested
  input lists/dicts or any returned response must not corrupt the token
  comparison, future replay, or stored principal associations.