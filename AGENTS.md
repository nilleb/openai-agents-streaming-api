# AGENTS

Do not use a global try/except around your functions. Reason a bit more and put those blocks only where it makes sense.

Use a logger to print debug messages. (utils.logging)

Use uv to run python scripts and manage dependencies.

Write unit tests for the implementation of the features.

Use ruff and ty to check and/or reformat the code.

Avoid using nested function.

Functions do just one thing at a time.

Use pydantic to represent the Settings (use the environment variables).

Use the commands defined in the cli executable (lint, typecheck, test).
