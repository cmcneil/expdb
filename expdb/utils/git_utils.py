import subprocess


def get_most_recent_commit():
    """Returns the most recent Git commit hash."""
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD']
        ).strip().decode('utf-8')
        return commit_hash
    except subprocess.CalledProcessError as e:
        print("Error: Could not retrieve the most recent Git commit.")
        return None

def no_uncommitted_changes():
    """Checks if there are any uncommitted changes."""
    try:
        # `--porcelain` gives a clean output, useful for scripts
        status_output = subprocess.check_output(
            ['git', 'status', '--porcelain']
        ).strip().decode('utf-8')

        if status_output:
            return False  # There are uncommitted changes
        else:
            return True  # No uncommitted changes
    except subprocess.CalledProcessError as e:
        print("Error: Could not check for uncommitted changes.")
        return None
