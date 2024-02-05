"""
The 'src' package forms the core of the Fuzzy Matcher Application, encapsulating the data model, user interface, application control logic, and supporting utilities. It is structured to promote separation of concerns, ensuring that each module within the package has a distinct responsibility, leading to a codebase that is more maintainable, modular, and scalable.

Modules included in the 'src' package:

- Main (main.py): Serves as the entry point of the application. It initializes and configures the main components of the application, including setting up logging, instantiating the data model, user interface, and controller, and starting the application loop.
- Data Model (data_model.py): Defines the DataModel class, responsible for handling all data-related operations, including data manipulation, fuzzy matching logic, categorization of responses, and interaction with the file system for data persistence.
- User Interface (fuzzy_ui.py): Implements the FuzzyUI class, managing the graphical user interface of the application. It handles the layout, widgets, and user interactions, providing a user-friendly interface for interacting with the application's core functionality.
- Controller (controller.py): Contains the Controller class, serving as the intermediary between the user interface and the data model. It processes user actions, invokes data model operations based on user input, and updates the user interface based on the results of these operations.
- Logging Tools (logging_utils.py): Provides utility functions and configurations for application-wide logging, ensuring that meaningful log messages are generated and recorded, facilitating debugging and monitoring of application behavior.

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""
