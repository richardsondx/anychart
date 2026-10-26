# Rust plan: no, not yet, and why

## Short answer

v0.1 is Python, stdlib only. Rust is planned for v1, after the geometry
and metadata model are proven, not before.

## Why Python first

- The bottleneck for an agent using a chart is not parser speed. It is
  vision tokens, network calls, and wrong metadata. A Python parser
  runs in milliseconds for one chart. AnyDoc's Rust speed matters
  because it converts thousands of documents in pipelines. Anychart
  converts one chart at a time for an agent.
- Testing found two real bugs, tick filtering and integer rounding,
  that would have been ported to Rust if Rust had come first. Fixing
  a model in Python, with a test corpus, is faster than fixing it
  across a Rust core plus bindings.
- Python is the language most agents and data teams already run.
  A pip install with no compiled dependency is the lowest friction
  proof that the metadata model is useful.

## What Rust would buy, when it is worth it

- A single binary, no Python runtime, for CLI distribution
- Node and Python bindings without a Python dependency, like anydoc
- A WASM demo where files never leave the browser, like anydoc's demo
- Speed at scale, if Evidence ingestion starts converting thousands
  of publisher SVGs in a batch

None of those are needed to prove the idea, and all of them are
expensive before the model is stable.

## Rust v1 plan, if v0.1 proves useful in the wild

1. Port `detect.py`, `svg.py`, and `model.py` to a Rust core, with
   the same function names and the same output envelope.
2. Port the test corpus in `tests/test_cred_fred.py` to Rust tests.
   Rust output must match Python output within the same tolerances,
   or the port is not done.
3. Add Python bindings with PyO3 and Node bindings, and a WASM build
   for the browser demo.
4. Benchmark Python vs Rust on the same corpus, and publish the
   numbers, not a speed claim.
5. Keep the Python package as a thin binding, not a second implementation,
   so the two do not drift.

## What would change this decision

- Evidence ingestion needs a single binary, or a WASM demo, before
  the Python proof has users. Then Rust moves up, but the test corpus
  moves with it, unchanged.
- A contributor offers a Rust core with the test corpus passing.
  That is a welcome pull request, not a rewrite from scratch.
