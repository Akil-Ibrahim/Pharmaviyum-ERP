# CI verification

This marker commit exists to execute the `dev` CI pipeline after the immutable release hardening changes.

The expected verification chain is:

1. lint and type checks
2. unit and integration tests
3. security scans
4. RAG regression evaluation
5. immutable GHCR image build
6. SBOM and provenance attestations
7. release manifest containing the image digest

This file can be removed after the first successful end-to-end CI verification if desired.
