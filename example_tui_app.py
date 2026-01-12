#!/usr/bin/env python3
"""
Simple example TUI application for testing the MCP server.
This demonstrates a basic interactive terminal UI.
"""

import sys
import time


def main():
    print("=" * 50)
    print("Welcome to Example TUI App")
    print("=" * 50)
    print()
    
    options = [
        "1. Show system information",
        "2. Display current time",
        "3. Echo user input",
        "4. Exit"
    ]
    
    while True:
        print("\nOptions:")
        for option in options:
            print(f"  {option}")
        
        print()
        choice = input("Select an option (1-4): ").strip()
        
        if choice == "1":
            print("\nSystem Information:")
            import platform
            print(f"  Platform: {platform.system()} {platform.release()}")
            print(f"  Python: {sys.version.split()[0]}")
            print(f"  Processor: {platform.processor()}")
        
        elif choice == "2":
            print(f"\nCurrent Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        elif choice == "3":
            user_input = input("\nEnter text to echo: ").strip()
            print(f"You entered: {user_input}")
        
        elif choice == "4":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid option. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted.")
        sys.exit(0)
