"""
Minimal package for asymmetric multi-agent experiments.

This module is intentionally small; the main entry point is
`run_asymmetric_agents.py`, which wires together:

- a dataset loader for the released asymmetric reasoning data
- two LLM-backed agents (Alice / Bob)
- an information-exchange style conversation loop
"""
