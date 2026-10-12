# main.py
"""
Main entry point for the OOP Task Manager CLI application.
"""

from src.task_manager import TaskManager


def display_menu():
    """Displays the main menu options to the user."""
    print("\n--- OOP Task Manager Menu ---")
    print("1. Add Task")
    print("2. List Tasks")
    print("3. Complete Task")
    print("4. Delete Task")
    print("5. Exit")
    print("-------------------------")


def read_task_id(prompt: str):
    """Asks for a task ID. Returns an int, or None (after printing an error) if the input is not a number."""
    try:
        return int(input(prompt).strip().lstrip("#"))
    except ValueError:
        print("Invalid input. Please enter a number for Task ID.")
        return None


def main():
    """Main function to run the Task Manager application."""
    manager = TaskManager()

    try:
        while True:
            display_menu()
            choice = input("Enter your choice (1-5): ").strip()

            if choice == '1':
                manager.add_task(input("Enter task description: "))
            elif choice == '2':
                manager.list_tasks()
            elif choice == '3':
                task_id = read_task_id("Enter ID of task to complete: ")
                if task_id is not None:
                    manager.complete_task(task_id)
            elif choice == '4':
                task_id = read_task_id("Enter ID of task to delete: ")
                if task_id is not None:
                    manager.delete_task(task_id)
            elif choice == '5':
                print("Exiting Task Manager. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
    except (KeyboardInterrupt, EOFError):
        # Every change is already saved, so we can simply leave
        print("\nExiting Task Manager. Goodbye!")


if __name__ == "__main__":
    main()
