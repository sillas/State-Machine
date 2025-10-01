# from machines.example_machine import main as main_from_def
from machines.example_machine_def import main as main_from_yml

# uv run main.py

if __name__ == "__main__":
    # print("Run from script")
    # main_from_def()

    print("\n\n\nRun from yml file")
    main_from_yml()
