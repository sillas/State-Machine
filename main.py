from logging_config import setup_logging
from machines.out_of_machine import main

# uv run main.py

setup_logging()

if __name__ == "__main__":
    main()
