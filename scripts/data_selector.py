"""
Data Folder Selection Utility
Provides terminal UI for selecting data folders
"""

import os
from pathlib import Path

def get_available_data_folders():
    """Get all available data folders"""
    data_dir = Path('~/E2E-network-measurement/data').expanduser()
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return []
    
    folders = []
    for item in data_dir.iterdir():
        if item.is_dir():
            folders.append(item.name)
    
    return sorted(folders)

def select_data_folder():
    """Display terminal UI for data folder selection"""
    folders = get_available_data_folders()
    
    if not folders:
        print("No data folders found!")
        return None
    
    print("\n" + "="*60)
    print("Available Data Folders:")
    print("="*60)
    
    for i, folder in enumerate(folders, 1):
        print(f"{i}. {folder}")
    
    print("="*60)
    
    while True:
        try:
            choice = input(f"Select data folder (1-{len(folders)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Operation cancelled.")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(folders):
                selected_folder = folders[choice_num - 1]
                data_path = Path('~/E2E-network-measurement/data').expanduser() / selected_folder
                print(f"\nSelected: {selected_folder}")
                print(f"Path: {data_path}")
                return data_path
            else:
                print(f"Please enter a number between 1 and {len(folders)}")
                
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

def get_data_folder_interactive():
    """Get data folder with interactive selection"""
    return select_data_folder()
