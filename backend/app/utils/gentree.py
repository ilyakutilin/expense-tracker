import os


def generate_tree_structure(
    root_dir, exclude_dirs=None, exclude_files=None, max_depth=None
):
    """
    Generate a tree structure of the given directory.

    Args:
        root_dir (str): Root directory to start from
        exclude_dirs (list): List of directory names to exclude
        exclude_files (list): List of file extensions/patterns to exclude
        max_depth (int): Maximum depth to traverse
    """
    if exclude_dirs is None:
        exclude_dirs = [
            ".git",
            ".mypy_cache",
            ".vscode",
            "__pycache__",
            "tmp",
            "logs",
            ".venv",
            "venv",
            "node_modules",
        ]
    if exclude_files is None:
        exclude_files = [".pyc", ".pyo", ".pyd", ".DS_Store"]

    def should_exclude(path, is_dir=False):
        name = os.path.basename(path)
        if is_dir:
            return name in exclude_dirs
        else:
            return any(name.endswith(ext) for ext in exclude_files)

    def walk_directory(current_path, prefix="", depth=0):
        if max_depth is not None and depth > max_depth:
            return

        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            print(f"{prefix}├── [Permission Denied]")
            return

        # Separate directories and files
        dirs = []
        files = []

        for item in items:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                if not should_exclude(item_path, True):
                    dirs.append(item)
            else:
                if not should_exclude(item_path, False):
                    files.append(item)

        # Print directories first
        for i, dir_name in enumerate(dirs):
            is_last = (i == len(dirs) - 1) and (len(files) == 0)
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{dir_name}/")

            new_prefix = prefix + ("    " if is_last else "│   ")
            walk_directory(os.path.join(current_path, dir_name), new_prefix, depth + 1)

        # Print files
        for i, file_name in enumerate(files):
            is_last = i == len(files) - 1
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{file_name}")

    print(f"{os.path.basename(root_dir)}/")
    walk_directory(root_dir, "", 0)


# Usage
if __name__ == "__main__":
    import sys

    # Use current directory if no argument provided
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_tree_structure(root_directory, max_depth=5)
