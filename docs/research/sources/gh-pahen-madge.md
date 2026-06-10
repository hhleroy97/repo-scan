---
id: "gh-pahen-madge"
type: "github"
url: "https://github.com/pahen/madge"
raw_url: "https://github.com/pahen/madge"
tags: ["amd", "circular-dependencies", "cli", "commonjs", "css-preprocessors", "dependency-graph", "es6-modules", "graphviz", "javascript", "module-resolution", "repo", "static-analysis", "typescript"]
linked_files: []
relevance: "Useful reference for repo-scan when extending or comparing JavaScript/TypeScript dependency extraction, circular-import detection, orphan/leaf analysis, and graph export patterns against Python-centric tooling like pydeps and deprank."
ingested_at: "2026-06-10 03:26 UTC"
---

# pahen/madge — Create graphs from your CommonJS, AMD or ES6 module dependencies

## Summary

Madge is a mature JavaScript developer tool (~10k GitHub stars) for building module dependency graphs from CommonJS, AMD, and ES6 code, with additional support for Sass, Stylus, and Less imports. It uses dependency-tree for extraction and optional Graphviz for SVG/DOT visualization, and exposes both a programmatic API and CLI for listing dependencies, detecting circular imports, finding orphans/leaves, and rendering graphs. NPM and core Node built-ins are excluded by default, and resolution can be tuned with webpack, TypeScript, and RequireJS configs.

## Key claims

- Generates visual dependency graphs and detects circular dependencies in JavaScript (AMD, CommonJS, ES6) and CSS preprocessor imports (Sass, Stylus, Less)
- Uses Joel Kemp's dependency-tree (via node-dependency-tree) to extract the dependency tree from source files
- Excludes NPM-installed dependencies and core Node.js modules by default; child dependencies are traversed automatically
- Programmatic API returns dependency objects plus helpers for circular(), circularGraph(), depends(), orphans(), leaves(), dot(), svg(), and image() output
- Supports configuration via .madgerc, package.json madge key, or inline config (baseDir, includeNpm, fileExtensions, excludeRegExp, webpackConfig, tsConfig, requireConfig, detectiveOptions, dependencyFilter)
- CLI supports --circular, --depends, --orphans, --leaves, --exclude, --json, --stdin piping, --dot, and --image (Graphviz required for visual output)
- Mixed JS/TS projects may need both webpackConfig and tsConfig; mixed import syntax and type-only imports can be controlled via detectiveOptions
- Unresolved or skipped files can be surfaced with --warning and --debug

## Notes

_yours to annotate_
