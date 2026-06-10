---
id: "gh-David-OConnor-pydeps"
type: "github"
url: "https://github.com/David-OConnor/pydeps"
raw_url: "https://github.com/David-OConnor/pydeps"
tags: ["caching", "dependencies", "dependency-resolution", "heroku", "package-metadata", "pypi", "python", "repo", "rest-api"]
linked_files: ["repo_scan/graphs.py"]
relevance: "Useful reference for building or improving Python dependency scanning when warehouse metadata is insufficient and install-based resolution with shared caching is needed."
ingested_at: "2026-06-10 03:25 UTC"
---

# David-OConnor/pydeps — Store dependency info for each PyPi package

## Summary

David-OConnor/pydeps is a Python service that stores and serves top-level dependency information for PyPI packages via a REST API. It resolves dependencies by downloading and installing packages on the server rather than trusting PyPI warehouse metadata alone. First requests for a package/version pair are slow while the package is installed and analyzed; later requests are fast because results are cached for all users.

## Key claims

- Exposes GET endpoints to fetch top-level dependencies for a PyPI package and for a specific version (e.g. /requests and /requests/2.21.0)
- Provides a POST API for querying dependency info on specified versions
- Determines dependencies by downloading and installing packages on the server because PyPI warehouse metadata is unreliable
- First request for a given package/version combination is slow; subsequent requests by any user are fast due to server-side caching
- Example deployment is available at pydeps.herokuapp.com

## Notes

_yours to annotate_
