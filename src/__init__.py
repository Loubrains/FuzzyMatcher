"""
FuzzyMatcher Application

This application is designed to provide a user-friendly interface for performing fuzzy matching and categorization of survey data.

Key features:
    - Fuzzy Matching: Users to input a string and find similar responses within the dataset based on a fuzziness threshold.
    - Category Management: Users can create, rename, and delete categories.
    - Categorization: Users can categorize selected responses into selected categories, or recategorize responses.
    - Categorization type: Users can select "Single" or "Multi" categorization type for whether responses can go into only one category or multiple.
    - Project Management: Users can start new projects, loading existing projects, appending data to projects, saving progress, and exporting results to CSV files.

Modules:
    - main: The entry point of the application, initializing the application components and starting the application loop.
    - controller: Acts as the intermediary between the user interface and the data model, managing the flow of data upon user interaction.
    - fuzzy_ui: Manages the user interface, displaying data and receiving user input.
    - data_model: Handles the core data processing, including fuzzy matching, category management, categorization, and project management.
    - file_handler: Provides functionalities for reading, saving, and exporting files.
    - logging_utils: Configures logging for the application and provides utility functions for formatting logs.

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""
