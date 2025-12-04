import pathlib

from app.core.exceptions import PathError


def ensure_dir(directory_path: str) -> pathlib.Path:
    """
    Validates a directory path, ensures it exists and is writable.

    Args:
        directory_path: String path to validate

    Returns:
        pathlib.Path object if valid

    Raises:
        PathError: If path cannot be created or is not writable
    """
    try:
        path = pathlib.Path(directory_path).resolve()

        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise PathError(directory_path, f"Cannot create directory: {str(e)}")

        if not path.is_dir():
            raise PathError(directory_path, "Path exists but is not a directory")

        test_file = path / ".write_test.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise PathError(directory_path, f"Directory is not writable: {str(e)}")

        return path

    except PathError:
        raise
    except Exception as e:
        raise PathError(directory_path, f"Unexpected error: {str(e)}")
