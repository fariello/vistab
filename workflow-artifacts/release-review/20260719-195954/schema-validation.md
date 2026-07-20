# Schema validation

No formal data-contract schemas (no JSON Schema, OpenAPI, DB migrations, protobufs). The relevant "contracts" are:
- themes.json (user config): malformed file now warns + continues (bugs-B2, executed). Validated by TestBrokenThemesConfig.
- CSV input parsing (csv.Sniffer): covered by CLI tests.
- Golden .txt fixtures: byte-exact render contracts; all green.
Not applicable beyond the above; no schema tooling introduced.
