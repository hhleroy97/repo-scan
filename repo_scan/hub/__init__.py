"""hub — the remote-control layer: run state, decision inbox, daemon, server.

Everything here is file-backed under docs/<docs_dir>/.radar/ so any surface
(terminal, web dashboard, future channels) reads and writes the same state.
The directory is runtime state, not knowledge — keep it out of git.
"""
