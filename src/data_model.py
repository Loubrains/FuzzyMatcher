"""
Provides a `DataModel` class for the FuzzyMatcher application.

Responsible for storing and manipulating the data involved in the fuzzy matching and categorization processes
and serving data to the `controller` of the FuzzyMatcher application.

Key Functionalities:
- Initializing and managing the data structures.
- Preprocessing text and handling missing data.
- Performing fuzzy matching of responses against a provided string and processing the results.
- Categorizing responses into user-defined categories and recategorizing them as needed.
- Category management (category creation, renaming, and deletion)
- Handling importing of data for new projects, appending data, saving and loading projects, and exporting categorized data to CSV.
- Validating loaded/saved data.
- Calculating and formatting data for display.

Main dependencies:
- thefuzz: for performing fuzzy matching.
- pandas: for data manipulation.
- re: for pattern matching during data cleaning.
- io: for converting data to json serializable format.
- file_handler: a module from this project for performing file saving and loading functions.

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
import logging_utils
import re
from thefuzz import fuzz
import pandas as pd
from io import StringIO
from typing import Any, Tuple
from pandas._libs.missing import NAType
from file_handler import FileHandler

# Setup logging
logger = logging.getLogger(__name__)


class DataModel:
    """
    A class responsible for managing and processing the data for fuzzy matching and categorization of responses.

    Attributes:
        file_handler (FileHandler): An instance of FileHandler for handling file operations.
        raw_data (pd.DataFrame): DataFrame containing the raw imported data. Expects first column to be uuids and subsequent columns to contain responses.
        data_to_append (pd.DataFrame): DataFrame of imported data to append onto the current project data.
        data_loaded (dict[str, Any]): Loaded project data (all the relevant class attributes) from json file.
        response_columns (list[str]): List of response column names.
        preprocessed_responses (pd.DataFrame): DataFrame of cleaned response columns from raw_data.
        stacked_responses (pd.Series): Series containing the stacked, deduplicated responses, excluding missing data.
        response_counts (dict[str, int]): Dictionary holding counts of responses, including missing data.
        categorized_data (pd.DataFrame): DataFrame containing categorized responses. This is the main DataFrame of the application.
            First column contains uuids, the next columns are the response columns, and then the subsequent columns are for each category, repeated out for each response column (with the name appended on the end).
            The values of the category columns are 1, 0, or pd.NA, depending on whether or not the responses in their associated response column are categorized into that category, or missing data.
        categorized_dict (dict[str, str]): Dictionary of categories to deduplicated responses, excluding missing data.
        fuzzy_match_results (pd.DataFrame): DataFrame holding results and score of fuzzy matching.
        currently_displayed_category (str): The category currently being displayed in the UI.
        expected_json_structure (dict[str, type]): A dictionary of types for each class attribute, for validation loaded project data.
        export_df (pd.DataFrame): categorized_data with the response columns removed, for exporting to CSV.

    Methods:
        initialize_data_structures: Initializes empty data structures used in the model.
        fuzzy_match_logic: Handles the logic for performing fuzzy matching on the data.
        fuzzy_match: Used by fuzzy_match_logic to perform the fuzzy matching.
        categorize_responses: Categorizes selected responses into selected categories.
        recategorize_responses: Recategorizes selected responses into selected categories.
        add_responses_to_category: Used by categorize_responses and recategorize_responses to add specified responses to a category in categorized_data and categorized_dict.
        remove_responses_from_category: Used by categorize_responses and recategorize_responses to remove specified responses from a category in categorized_data and categorized_dict.
        create_category: Creates a new category in categorized_data and categorized_dict.
        rename_category: Renames an existing category in categorized_data and categorized_dict.
        delete_categories: Deletes selected categories from categorized_data and categorized_dict, and handles associated data cleanup.
        file_import_on_new_project: Handles importing data for a new project.
        populate_data_structures_on_new_project: Populates data structures for a new project.
        file_import_on_load_project: Handles importing data for loading an existing project.
        populate_data_structures_on_load_project: Populates data structures when loading a project.
        file_import_on_append_data: Handles importing data to append to the current project.
        populate_data_structures_on_append_data: Populates data structures when appending data.
        save_project: Saves all the current project's relevant data (the class attributes) to a JSON file.
        export_data_to_csv: Exports the categorized data to a CSV file.
        preprocess_text: Cleans text data (e.g. response text).
        process_fuzzy_match_results: Filters, aggregates and sorts the fuzzy match results for display.
        handle_missing_data: Handles missing data in categorized_data and categorized_dict.
        validate_loaded_json: Validates the structure of loaded JSON project data.
        get_responses_and_counts: Retrieves responses and their counts for a specific category.
        format_categories_metrics: Formats metrics for categories to be displayed.
        sum_response_counts: Sums the response counts for a set of responses.
        calculate_percentage: Calculates the percentage of responses for a category, with or without missing data.
    """

    def __init__(self, file_handler: FileHandler) -> None:
        """
        Sets up the data structures and file handler.

        Args:
            file_handler (FileHandler): An instance of FileHandler.
        """

        logger.info("Initializing data model")
        self.file_handler = file_handler
        self.initialize_data_structures()  # Empty/default variables.

    def initialize_data_structures(self):
        """
        Initializes and resets data structures used in the model. This includes data frames for raw data, preprocessed responses, categorized data,
        dictionaries for response counts and categorized responses, and other necessary data structures for managing the data model.
        """

        logger.debug("Initializing data structures")
        # Empty variables which will be populated during new project/load project
        self.raw_data = pd.DataFrame()
        self.preprocessed_responses = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categorized_dict = {"Uncategorized": set()}
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # default
        self.currently_displayed_category = "Uncategorized"  # default

        # For validation of loaded project data.
        # NOTE: Update this when the data structure changes.
        # TODO: Need to update this and validate_loaded_json() to use more specific typing (e.g. dict[str, set[str]) and handle stringified json too
        self.expected_json_structure = {
            "raw_data": str,
            "preprocessed_responses": str,
            "response_columns": list,
            "categorized_data": str,
            "response_counts": dict,
            "categorized_dict": dict,
            "categorization_type": str,
            "is_including_missing_data": bool,
        }

        logging_utils.format_and_log_data_for_debug(logger, vars(self))

    ### ----------------------- Main functionality ----------------------- ###
    def fuzzy_match_logic(self, string_to_match: str) -> Tuple[bool, str]:
        """
        Handles the logic for performing fuzzy matching on the data against a provided string.

        Args:
            string_to_match (str): The string to be matched fuzzily against the data.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        # NOTE: This check is probably not needed?
        if self.categorized_data.empty or self.categorized_data is None:
            message = "There is no dataset in the current project to match against"
            logger.warning(message)
            logger.debug(f"categorized_data:\n{self.categorized_data}")
            return False, message

        logger.info(f'Preparing to perform fuzzy match: "{string_to_match}"')
        uncategorized_responses = self.categorized_dict["Uncategorized"]
        uncategorized_df = self.preprocessed_responses[
            self.preprocessed_responses.isin(uncategorized_responses)
        ].dropna(how="all")

        # Perform fuzzy matching on these uncategorized responses
        self.fuzzy_match_results = self.fuzzy_match(uncategorized_df, string_to_match)

        return True, "Performed fuzzy match successfully"

    def fuzzy_match(self, preprocessed_responses: pd.DataFrame, match_string: str) -> pd.DataFrame:
        """
        Performs fuzzy matching on preprocessed responses against a provided match string, returning a DataFrame with the results.

        Args:
            preprocessed_responses (pd.DataFrame): The preprocessed responses to be matched against.
            match_string (str): The string to be matched fuzzily against the responses.

        Returns:
            pd.DataFrame: A DataFrame containing the fuzzy match results.
        """

        logger.info('Performing fuzzy match: "%s"', match_string)

        def _fuzzy_match(element) -> int:
            return fuzz.WRatio(
                match_string, str(element)
            )  # Weighted ratio of several fuzzy matching protocols

        # Get fuzzy matching scores and format result: {response: score}
        results = []
        for row in preprocessed_responses.itertuples(index=True, name=None):
            for response in row[1:]:
                score = _fuzzy_match(response)
                results.append({"response": response, "score": score})

        logger.info("Performed fuzzy match successfully")
        return pd.DataFrame(results)

    def categorize_responses(
        self, responses: set[str], categories: set[str], categorization_type: str
    ):
        """
        Categorizes selected responses into selected categories based on the provided categorization type.

        Args:
            responses (set[str]): A set of responses to be categorized.
            categories (set[str]): A set of categories into which the responses will be categorized.
            categorization_type (str): The type of categorization to be performed ('Single' or 'Multi').
        """

        logger.info("Categorizing responses")
        for response_column in self.response_columns:
            mask = self.categorized_data[response_column].isin(responses)

            if categorization_type == "Single":
                self.remove_responses_from_category(
                    responses, "Uncategorized", response_column, mask
                )

            for category in categories:
                self.add_responses_to_category(responses, category, response_column, mask)

        # Additionally, remove the responses from fuzzy_match_results
        if categorization_type == "Single":
            fuzzy_mask = self.fuzzy_match_results["response"].isin(responses)
            self.fuzzy_match_results = self.fuzzy_match_results[~fuzzy_mask].reset_index(drop=True)

        logger.info("Responses categorized")

    def recategorize_responses(self, responses: set[str], categories: set[str]) -> None:
        """
        Recategorizes selected responses into selected categories. This is typically used to change the categories of already categorized responses.

        Args:
            responses (set[str]): A set of responses to be recategorized.
            categories (set[str]): A set of new categories into which the responses will be categorized.
        """

        logger.info("Recategorizing responses")
        for response_column in self.response_columns:
            mask = self.categorized_data[response_column].isin(responses)
            self.remove_responses_from_category(
                responses, self.currently_displayed_category, response_column, mask
            )
            for category in categories:
                self.add_responses_to_category(responses, category, response_column, mask)
        logger.info("Responses recategorized")

    def add_responses_to_category(
        self, responses: set[str], category: str, response_column: str, mask: pd.Series
    ):
        """
        Adds specified responses to a category in a given response column based on a mask.

        Args:
            responses (set[str]): A set of responses to be added to the category.
            category (str): The category to which the responses will be added.
            response_column (str): The response column where the responses are located.
            mask (pd.Series): A boolean series used as a mask to identify rows for addition.
        """

        self.categorized_data.loc[mask, f"{category}_{response_column}"] = 1
        self.categorized_dict[category].update(responses)

    def remove_responses_from_category(
        self, responses: set[str], category: str, response_column: str, mask: pd.Series
    ):
        """
        Removes specified responses from a category in a given response column based on a mask.

        Args:
            responses (set[str]): A set of responses to be removed from the category.
            category (str): The category from which the responses will be removed.
            response_column (str): The response column where the responses are located.
            mask (pd.Series): A boolean series used as a mask to identify rows for removal.
        """

        self.categorized_data.loc[mask, f"{category}_{response_column}"] = 0
        self.categorized_dict[category] -= responses

    def create_category(self, new_category: str):
        """
        Creates a new category for categorizing responses.

        Args:
            new_category (str): The name of the new category to be created.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        logger.info('Creating new category: "%s"', new_category)

        if new_category in self.categorized_dict.keys():
            message = "Category already exists"
            logger.warning(message)
            logger.debug(f"categorized_dict.keys:\n{self.categorized_dict.keys()}")
            return False, message

        self.categorized_dict[new_category] = set()
        number_of_categories = len(self.categorized_dict.keys())

        # Start insert after uuid column + response columns
        insert_index_start = 1 + len(self.response_columns)
        number_of_categories = len(self.categorized_dict.keys())
        # Bring index behind uncategorized column(s)/in front of previous new category column(s)
        offset = number_of_categories - 2

        for i, response_column in enumerate(self.response_columns):
            col_name = f"{new_category}_{response_column}"
            # keep category columns grouped by response column
            # New categories come after previous ones, but before uncategorized
            insert_index = insert_index_start + i * number_of_categories + offset
            # Give all rows a value of 0 to start
            self.categorized_data.insert(insert_index, col_name, 0)

        self.handle_missing_data()

        message = "Category created successfully"
        logger.info(message)
        return True, message

    def rename_category(self, old_category: str, new_category: str):
        """
        Renames an existing category to a new name.

        Args:
            old_category (str): The current name of the category to be renamed.
            new_category (str): The new name for the category.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        logger.info(
            f'Renaming category. old_category: "{old_category}", new_category: "{new_category}"'
        )

        if new_category in self.categorized_dict.keys():
            message = "A category with this name already exists."
            logger.warning(message)
            logger.debug(f"categorized_dict.keys:\n{self.categorized_dict.keys()}")
            return False, message

        for response_column in self.response_columns:
            self.categorized_data.rename(
                columns={f"{old_category}_{response_column}": f"{new_category}_{response_column}"},
                inplace=True,
            )
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)

        message = "Category renamed successfully"
        logger.info(message)
        return True, message

    def delete_categories(self, categories_to_delete: set[str], categorization_type: str) -> None:
        """
        Deletes selected categories and handles associated data cleanup based on the categorization type.

        Args:
            categories_to_delete (set[str]): A set of categories to be deleted.
            categorization_type (str): The type of categorization that determines how to handle associated responses ('Single' or 'Multi').
        """

        logger.info("Deleting categories: %s", categories_to_delete)

        for category in categories_to_delete:
            for response_column in self.response_columns:
                # In single mode, return the responses from this category to 'Uncategorized'
                if categorization_type == "Single":
                    responses_to_recategorize = self.categorized_data[
                        self.categorized_data[f"{category}_{response_column}"] == 1
                    ].index
                    for response in responses_to_recategorize:
                        self.categorized_data.loc[response, f"Uncategorized_{response_column}"] = 1
                    self.categorized_dict["Uncategorized"].update(self.categorized_dict[category])

                self.categorized_data.drop(columns=f"{category}_{response_column}", inplace=True)
            del self.categorized_dict[category]

        logger.info("Categories deleted successfully")

    ### ----------------------- Project Management ----------------------- ###
    def file_import_on_new_project(self, file_path: str):
        """
        Handles importing data for a new project from a file.

        Args:
            file_path (str): The path to the file from which data is to be imported.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        logger.info("Calling file handler to import data")
        new_data = self.file_handler.read_csv_or_xlsx_to_dataframe(file_path)

        if new_data.empty:
            message = "Imported dataset is empty"
            logger.error(message)
            logger.debug(f"new_data:\n{new_data.head()}")
            return False, message

        if new_data.shape[1] < 2:
            logger.error("Imported dataset does not contain enough columns")
            logger.debug(f"new_data:\n{new_data.head()}")
            return (
                False,
                """Imported dataset does not contain enough columns.\n\n
                The dataset should contain uuids in the first column, and the subsequent columns should contian responses""",
            )

        self.raw_data = new_data
        message = "Data passed checks"
        logger.info(message)
        return True, message

    def populate_data_structures_on_new_project(self) -> None:
        """
        Populates data structures for a new project after data has been successfully imported.
        """

        logger.info("Populating data structures")

        self.preprocessed_responses = pd.DataFrame(
            self.raw_data.iloc[:, 1:].map(self.preprocess_text)  # , na_action="ignore"
        )  # type: ignore

        self.stacked_responses = self.preprocessed_responses.stack(dropna=False).reset_index(
            drop=True
        )
        self.categorized_dict = {"Uncategorized": set(self.stacked_responses.dropna())}  # default
        self.response_counts = self.stacked_responses.value_counts(dropna=False).to_dict()
        uuids = self.raw_data.iloc[:, 0]
        self.response_columns = list(self.preprocessed_responses.columns)
        # categorized_data has a column for uuids, all response columns, and will have a column for each category, which are repeated out for each response column
        # In categorized_data, the category columns associated with a response column contain values 1 or 0 for whether that response is in that category, or pd.NA if response is pd.NA
        self.categorized_data = pd.concat([uuids, self.preprocessed_responses], axis=1)
        for response_column in self.response_columns:
            # Everything starts uncategorized
            self.categorized_data[f"Uncategorized_{response_column}"] = 1
        self.handle_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        logging_utils.format_and_log_data_for_debug(logger, vars(self))
        logger.info("Data structures populated successfully")

    def file_import_on_load_project(self, file_path: str):
        """
        Handles importing data for loading an existing project from a file.

        Args:
            file_path (str): The path to the project file to be loaded.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        logger.info("Calling file handler to import project data")
        new_data = self.file_handler.load_json(file_path)
        success, message = self.validate_loaded_json(new_data, self.expected_json_structure)

        if not success:
            logger.error(message)
            return False, message

        self.data_loaded = new_data
        message = "Project data passed checks"
        logger.info(message)
        return True, message

    def populate_data_structures_on_load_project(self):
        """
        Populates data structures when loading a project from a file. This involves converting the loaded data back into the appropriate data structures used by the DataModel.

        Returns:
            Tuple[str, bool]: A tuple containing the categorization type and the boolean status of including missing data.
        """

        logger.info("Populating data structures")

        def _replace_none_with_pd_na(df):
            return df.map(lambda x: pd.NA if x is None else x)

        # Convert JSON back to data / set default variable values
        self.raw_data = _replace_none_with_pd_na(
            pd.read_json(StringIO(self.data_loaded["raw_data"]))
        )
        self.preprocessed_responses = _replace_none_with_pd_na(
            pd.read_json(StringIO(self.data_loaded["preprocessed_responses"]))
        )
        self.response_counts = {
            k if k != "null" else pd.NA: v for k, v in self.data_loaded["response_counts"].items()
        }
        self.categorized_data = _replace_none_with_pd_na(
            pd.read_json(StringIO(self.data_loaded["categorized_data"]))
        )
        self.categorized_dict = {k: set(v) for k, v in self.data_loaded["categorized_dict"].items()}
        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        # Tkinter variables
        categorization_type = self.data_loaded["categorization_type"]
        is_including_missing_data = self.data_loaded["is_including_missing_data"]

        logging_utils.format_and_log_data_for_debug(logger, vars(self))
        logger.info("Data structures populated successfully")
        # Return Tkinter variables back to the UI class
        return (categorization_type, is_including_missing_data)

    def file_import_on_append_data(self, file_path: str):
        """
        Handles importing data to append to the current project's dataset.

        Args:
            file_path (str): The path to the file from which data is to be appended.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure, and the second element is a message detailing the operation's outcome.
        """

        if self.raw_data.empty:
            logger.warning("There is no dataset in the current project to append to")
            logger.error(f"raw_data:\n{self.raw_data}")
            return (
                False,
                '''There is no dataset in the current project to append to.\n\n
                Click "Start New Project" or "Load project"''',
            )

        logger.info("Calling file handler to import data to append")
        new_data = self.file_handler.read_csv_or_xlsx_to_dataframe(file_path)

        if new_data.empty:
            message = "Imported dataset is empty"
            logger.error(message)
            logger.debug(f"new_data:\n{new_data}")
            return False, message

        # using self.raw_data as it should have the same columns as self.categorized_data without the category columns.
        if new_data.shape[1] != self.raw_data.shape[1]:
            logger.error(
                "Imported dataset does not have the same number of columns as the dataset in the current project"
            )
            logger.debug(
                f"""new_data:\n{new_data.head()}\n
                raw_data:\n{self.raw_data.head()}"""
            )
            return (
                False,
                """Imported dataset does not have the same number of columns as the dataset in the current project.\n\n
                The dataset should contain UUIDs in the first column, and the subsequent columns should contain
                the same number of response columns as the currently loaded data.""",
            )

        self.data_to_append = new_data
        message = "Data passed checks"
        logger.info(message)
        return True, message

    def populate_data_structures_on_append_data(self, categorization_type) -> None:
        """
        Populates data structures when appending new data to the current project, considering the current categorization type.

        Args:
            categorization_type (str): The categorization type ('Single' or 'Multi') which affects how new data is appended and categorized.
        """

        logger.info("Populating data structures")

        self.raw_data = pd.concat([self.raw_data, self.data_to_append], ignore_index=True)
        old_data_size = len(self.preprocessed_responses)

        new_preprocessed_responses = pd.DataFrame(
            self.raw_data.iloc[old_data_size:, 1:].map(self.preprocess_text)  # type: ignore
        )
        self.preprocessed_responses = pd.concat(
            [self.preprocessed_responses, new_preprocessed_responses]
        )

        new_stacked_responses = new_preprocessed_responses.stack(dropna=False).reset_index(
            drop=True
        )
        self.stacked_responses = self.preprocessed_responses.stack(dropna=False).reset_index(
            drop=True
        )
        self.response_counts = self.stacked_responses.value_counts(dropna=False).to_dict()

        ### Categorize new responses
        # This section is probably more bulky and inefficient than it needs to be
        old_categorized_responses_set = set().union(
            *[
                responses
                for category, responses in self.categorized_dict.items()
                if category != "Uncategorized"
            ]
        )
        # using categrized_dict values here since we've already changed self.preprocessed_responses
        new_responses_set = set(new_stacked_responses.dropna())
        new_uncategorized_responses_set = new_responses_set - old_categorized_responses_set
        new_already_categorized_responses_set = new_responses_set.intersection(
            old_categorized_responses_set
        )

        self.categorized_dict["Uncategorized"].update(new_uncategorized_responses_set)
        new_categorized_data = pd.concat(
            [self.raw_data.iloc[old_data_size:, 0], new_preprocessed_responses], axis=1
        )  # Why isn't this axis=0?
        self.categorized_data = pd.concat([self.categorized_data, new_categorized_data], axis=0)

        # Everything starts uncategorized (this removes NAs but we handle it again after)
        for response_column in self.response_columns:
            for category in self.categorized_dict.keys():
                self.categorized_data.loc[old_data_size:, f"Uncategorized_{response_column}"] = 1
                self.categorized_data.loc[old_data_size:, f"{category}_{response_column}"] = 0

        for new_response in new_already_categorized_responses_set:
            categories_for_response = {
                category
                for category, responses in self.categorized_dict.items()
                if new_response in responses
            }
            self.categorize_responses(
                {str(new_response)}, categories_for_response, categorization_type
            )

        self.handle_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        logging_utils.format_and_log_data_for_debug(logger, vars(self))
        logger.info("Data structures populated successfully")

    def save_project(self, file_path: str, user_interface_variables_to_add: dict[str, Any]) -> None:
        """
        Saves the current project's data to a file, including additional variables from the user interface.

        Args:
            file_path (str): The path where the project file will be saved.
            user_interface_variables_to_add (dict[str, Any]): Additional variables from the user interface to be included in the saved project data.
        """

        logger.info("Preparing to save project data")

        data_to_save = {
            "raw_data": self.raw_data.to_json(),
            "preprocessed_responses": self.preprocessed_responses.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": {
                k if k is not pd.NA else None: v for k, v in self.response_counts.items()
            },
            "categorized_dict": {k: list(v) for k, v in self.categorized_dict.items()},
        }
        data_to_save.update(user_interface_variables_to_add)

        # Pandas NAType is not JSON serializable
        def _none_handler(o):
            if pd.isna(o):
                return None

        logger.info("Calling file handler to save project data")
        self.file_handler.save_data_to_json(file_path, data_to_save, handler=_none_handler)

    def export_data_to_csv(self, file_path: str, categorization_type: str) -> None:
        """
        Exports categorized data to a CSV file, considering the current categorization type.

        Args:
            file_path (str): The path where the exported CSV file will be saved.
            categorization_type (str): The categorization type ('Single' or 'Multi') which affects how data is exported.
        """

        logger.info("Preparing to export categorized data to csv")

        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        self.export_df = self.categorized_data.drop(columns=self.response_columns)
        if categorization_type == "Multi":
            self.export_df.drop("Uncategorized", axis=1, inplace=True)

        logger.info("Calling file handler  export categorized data to csv")
        self.file_handler.export_dataframe_to_csv(file_path, self.export_df)

    ### ----------------------- Helper functions ----------------------- ###
    def preprocess_text(self, text: Any) -> str | NAType:
        """
        Preprocesses text data (e.g., response text) by converting to lowercase, removing special characters, and normalizing whitespace.

        Args:
            text (Any): The text to be preprocessed.

        Returns:
            str | NAType: The preprocessed text, or pd.NA if the input is missing.
        """

        if pd.isna(text):
            return pd.NA

        text = str(text).lower()
        # Convert one or more of any kind of space to single space
        text = re.sub(r"\s+", " ", text)
        # Remove special characters
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = text.strip()
        return text

    def process_fuzzy_match_results(self, threshold_value: float) -> pd.DataFrame:
        """
        Processes and filters the fuzzy match results based on the provided threshold value.

        Args:
            threshold_value (float): The threshold value for filtering the fuzzy match results.

        Returns:
            pd.DataFrame: A DataFrame containing the processed fuzzy match results.
        """

        # Filter the fuzzy match results based on the threshold
        filtered_results = self.fuzzy_match_results[
            self.fuzzy_match_results["score"] >= threshold_value
        ]

        aggregated_results = (
            filtered_results.groupby("response")
            .agg(
                score=pd.NamedAgg(column="score", aggfunc="max"),
                count=pd.NamedAgg(column="response", aggfunc="count"),
            )
            .reset_index()
        )

        return aggregated_results.sort_values(by=["score", "count"], ascending=[False, False])

    def handle_missing_data(self) -> None:
        """
        Handles missing data in the model's data structures by setting corresponding values to pd.NA.
        """

        def _is_missing(value) -> bool:
            return pd.isna(value)

        logger.debug(
            f"""Handling missing data\n
            categorized_data (before):\n{self.categorized_data.head()}\n"""
        )

        for response_column in self.response_columns:
            # Boolean mask where each row is True if all elements are missing
            missing_data_mask = self.preprocessed_responses[response_column].map(_is_missing)  # type: ignore

            for category in self.categorized_dict:
                col_name = f"{category}_{response_column}"
                self.categorized_data.loc[missing_data_mask, col_name] = pd.NA
            logger.debug(f"categorized_data (after):\n{self.categorized_data.head()}\n" "")

    def validate_loaded_json(
        self, loaded_json_data: dict[str, Any], expected_data: dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validates the structure of loaded JSON data against the expected structure.

        Args:
            loaded_json_data (dict[str, Any]): The loaded JSON data to be validated.
            expected_data (dict[str, Any]): The expected structure of the JSON data.

        Returns:
            Tuple[bool, str]: A tuple where the first element is a boolean indicating success or failure of the validation, and the second element is a message detailing the operation's outcome.
        """

        # NOTE: self.expected_json_structure is passed in. This needs to be updated when the data structure changes.
        logger.debug("Validating project data")

        if not loaded_json_data:
            logger.debug(f"loaded_json_data:\n{loaded_json_data}")
            return False, "Loaded project data is empty"

        # Unexpected variabes
        if unexpected_keys := set(loaded_json_data.keys()) - set(expected_data.keys()):
            logger.debug(
                f"""loaded_json_data.keys:\n{loaded_json_data.keys()}\n
                expected_data.keys:\n{expected_data.keys()}"""
            )
            return False, f"Unexpected variables loaded: {', '.join(unexpected_keys)}"

        for expected_key, expected_type in expected_data.items():
            # Missing variables
            if expected_key not in loaded_json_data:
                logger.debug(
                    f"""expected_key:\n{expected_key}\n
                    loaded_json_data.keys:\n{loaded_json_data.keys()}"""
                )
                return False, f"Variable '{expected_key}' is missing from loaded project data"

            # Wrong variable type
            # skip the bool case (e.g. `is_including_missing_data`) since its value would be evaluated in the if statement
            if expected_type is not bool and not loaded_json_data[expected_key]:
                logger.debug(f"{expected_key}:\n{loaded_json_data[expected_key]}")
                return False, f"Variable '{expected_key}' is empty in loaded project data"

            if not isinstance(loaded_json_data[expected_key], expected_type):
                logger.debug(
                    f"""Expected {expected_key}:{expected_type}\n
                    Received {expected_key}:{type(loaded_json_data[expected_key])}"""
                )
                return (
                    False,
                    f"Variable '{expected_key}' in loaded project data contains values that are not of expected type {expected_type.__name__}.",
                )

        logger.debug("Project data validated successfully")
        return True, "Loaded JSON validated successfully"

    def get_responses_and_counts(self, category: str) -> list[Tuple[str, int]]:
        """
        Retrieves responses and their counts for a specific category.

        Args:
            category (str): The category for which responses and counts are retrieved.

        Returns:
            list[Tuple[str, int]]: A list of tuples, each containing a response and its count.
        """

        responses_and_counts = [
            (str(response), self.sum_response_counts({response}))
            for response in self.categorized_dict[category]
        ]

        # Sort first by score and then alphabetically
        return sorted(responses_and_counts, key=lambda x: (-x[1], x[0]))

    def format_categories_metrics(
        self, is_including_missing_data: bool
    ) -> list[Tuple[str, int, str]]:
        """
        Formats metrics for categories to be displayed, including the count of responses and their percentage.

        Args:
            is_including_missing_data (bool): Whether to include missing data in percentage calculations.

        Returns:
            list[Tuple[str, int, str]]: A list of tuples, each containing a category name, count of responses, and percentage of total responses.
        """

        formatted_categories_metrics = []

        for category, responses in self.categorized_dict.items():
            count = self.sum_response_counts(responses)
            percentage = self.calculate_percentage(responses, is_including_missing_data)
            percentage_str = f"{percentage:.2f}%"
            formatted_categories_metrics.append((category, count, percentage_str))

        return formatted_categories_metrics

    def sum_response_counts(self, responses: set) -> int:
        """
        Sums the response counts for a set of responses.

        Args:
            responses (set): A set of responses whose counts are to be summed.

        Returns:
            int: The total count of the specified responses.
        """

        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(self, responses: set, is_including_missing_data: bool) -> float:
        """
        Calculates the percentage of responses for a category relative to the total number of responses, optionally including or excluding missing data.

        Args:
            responses (set): A set of responses for which the percentage is calculated.
            is_including_missing_data (bool): Whether to include missing data in the total responses count.

        Returns:
            float: The calculated percentage.
        """

        count = self.sum_response_counts(responses)

        if is_including_missing_data:
            total_responses = sum(self.response_counts.values())
        else:
            missing_data_count = self.sum_response_counts({pd.NA})
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0
