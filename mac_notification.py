import os


def display_notification(title, message):
    command = f"""
    osascript -e 'display notification "{message}" with title "{title}"'
    """
    os.system(command)
