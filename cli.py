import argparse

def main() -> None:
  
  parser = argparse.ArgumentParser(description="Knowledge Tracer CLI")
  subparser = parser.add_subparsers(dest="command", help="Available Commands")
  
  