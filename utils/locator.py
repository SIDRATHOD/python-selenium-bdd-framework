class Locator:
    """A wrapper to hold locator data and its source metadata."""
    def __init__(self, value, name, file_path):
        self.value = value      # The actual tuple, e.g., ("id", "profile-pic")
        self.name = name        # The variable name, e.g., "PROFILE_PICTURE"
        self.file_path = file_path # The absolute path to the file where it's defined

    def __str__(self):
        return f"Locator(name='{self.name}', value={self.value})"