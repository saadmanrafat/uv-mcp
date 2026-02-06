"""Configuration constants for UV-MCP."""

# Default timeouts (seconds)
DEFAULT_COMMAND_TIMEOUT = 120.0
DEFAULT_CHECK_TIMEOUT = 5.0

# Size limits
MAX_TREE_OUTPUT = 5 * 1024 * 1024  # 5MB
MAX_CACHE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_OUTPUT_SIZE = 2 * 1024 * 1024  # 2MB for general output

# Concurrency limits
MAX_CONCURRENT_COMMANDS = 10

# Retry policy
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds
