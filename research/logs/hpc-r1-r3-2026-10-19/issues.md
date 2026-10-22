# Execution issues and corrections

- R1 computation exited 0; automatic transfer initially failed because pytest's disposable pytest-tmp directory contained a normal symlink. No test failure or output loss. The inventory now excludes the specifically designated pytest-tmp subtree while retaining symlink rejection for evidence/output paths. Original failed transfer logs remain in the session; run status and outputs are preserved on HPC. Retry pull after verified source sync.
