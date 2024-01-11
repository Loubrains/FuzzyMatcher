#
# TODO: need to handle missing data better, not just as "nan", so that people writing "nan" don't get miscoded

import logging
import logging_utils
import re
from thefuzz import fuzz
import pandas as pd
from io import StringIO
from typing import Any, Tuple
from file_handler import FileHandler

# Setup logging
logger = logging.getLogger(__name__)


class DataModel:
    def __init__(self, file_handler: FileHandler) -> None:
        logger.info("Initializing data model")
        self.file_handler = file_handler
        self.initialize_data_structures()  # Empty/default variables.

    def initialize_data_structures(self):
        logger.debug("Initializing data structures")
        # Empty variables which will be populated during new project/load project
        # categorized_data will contain a uuids, responses, and column for each category, with a 1 or 0 for each response
        # categorized_dict will be a dict of categories containig the deduplicated set of all responses
        self.raw_data = pd.DataFrame()
        self.preprocessed_responses = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categorized_dict = {
            "Uncategorized": set(),
            "Missing data": {"nan", "missing data"},
        }
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # default
        self.currently_displayed_category = "Uncategorized"  # default

        # For validation on load project.
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
    def fuzzy_match_logic(self, string_to_match: str):
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

    def categorize_responses(
        self, responses: set[str], categories: set[str], categorization_type: str
    ):
        logger.info("Categorizing responses")

        mask = self.create_bool_mask_for_responses_in_data(responses)

        if categorization_type == "Single":
            self.remove_responses_from_category(responses, "Uncategorized", mask)
            # Additionally, remove the responses from fuzzy_match_results
            fuzzy_mask = self.fuzzy_match_results["response"].isin(responses)
            self.fuzzy_match_results = self.fuzzy_match_results[~fuzzy_mask].reset_index(drop=True)

        self.add_responses_to_categories(responses, categories, mask)

        logger.info("Responses categorized")

    def recategorize_responses(self, responses: set[str], categories: set[str]):
        logger.info("Recategorizing responses")
        mask = self.create_bool_mask_for_responses_in_data(responses)
        self.remove_responses_from_category(responses, self.currently_displayed_category, mask)
        self.add_responses_to_categories(responses, categories, mask)
        logger.info("Responses recategorized")

    def create_category(self, new_category: str):
        logger.info('Creating new category: "%s"', new_category)

        if new_category in self.categorized_data.columns:
            message = "Category already exists"
            logger.warning(message)
            logger.debug(f"categorized_data.columns:\n{self.categorized_data.columns}")
            return False, message

        self.categorized_data[new_category] = 0
        self.categorized_dict[new_category] = set()

        message = "Category created successfully"
        logger.info(message)
        return True, message

    def rename_category(self, old_category: str, new_category: str):
        logger.info(
            f'Renaming category. old_category: "{old_category}", new_category: "{new_category}"'
        )

        if new_category in self.categorized_dict:
            message = "A category with this name already exists."
            logger.warning(message)
            logger.debug(f"categorized_dict.keys:\n{self.categorized_dict.keys()}")
            return False, message

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)

        message = "Category renamed successfully"
        logger.info(message)
        return True, message

    def delete_categories(self, categories_to_delete: set[str], categorization_type: str):
        logger.info("Deleting categories: %s", categories_to_delete)

        for category in categories_to_delete:
            # In single mode, return the responses from this category to 'Uncategorized'
            if categorization_type == "Single":
                responses_to_recategorize = self.categorized_data[
                    self.categorized_data[category] == 1
                ].index
                for response_index in responses_to_recategorize:
                    self.categorized_data.loc[response_index, "Uncategorized"] = 1
                self.categorized_dict["Uncategorized"].update(self.categorized_dict[category])

            del self.categorized_dict[category]
            self.categorized_data.drop(columns=category, inplace=True)

        logger.info("Categories deleted successfully")

    ### ----------------------- Project Management ----------------------- ###
    def file_import_on_new_project(self, file_path: str):
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

    def populate_data_structures_on_new_project(self):
        logger.info("Populating data structures")

        self.preprocessed_responses = pd.DataFrame(
            self.raw_data.iloc[:, 1:].map(
                self.preprocess_text  # , na_action="ignore"
            )  # type: ignore
        )

        df_series = self.preprocessed_responses.stack().reset_index(drop=True)
        self.categorized_dict = {
            "Uncategorized": set(df_series) - {"nan", "missing data"},
            "Missing data": {"nan", "missing data"},  # default
        }
        self.response_counts = df_series.value_counts().to_dict()
        uuids = self.raw_data.iloc[:, 0]
        self.response_columns = list(self.preprocessed_responses.columns)
        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        self.categorized_data = pd.concat([uuids, self.preprocessed_responses], axis=1)
        self.categorized_data["Uncategorized"] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        logging_utils.format_and_log_data_for_debug(logger, vars(self))
        logger.info("Data structures populated successfully")

    def file_import_on_load_project(self, file_path: str):
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
        logger.info("Populating data structures")

        # Convert JSON back to data / set default variable values
        self.raw_data = pd.read_json(StringIO(self.data_loaded["raw_data"]))
        self.preprocessed_responses = pd.read_json(
            StringIO(self.data_loaded["preprocessed_responses"])
        )
        self.response_columns = self.data_loaded["response_columns"]
        self.categorized_data = pd.read_json(StringIO(self.data_loaded["categorized_data"]))
        self.response_counts = self.data_loaded["response_counts"]
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

    def populate_data_structures_on_append_data(self):
        logger.info("Populating data structures")

        self.raw_data = pd.concat([self.raw_data, self.data_to_append], ignore_index=True)
        old_data_size = len(self.preprocessed_responses)
        new_preprocessed_responses = pd.DataFrame(
            self.raw_data.iloc[old_data_size:, 1:].map(self.preprocess_text)  # type: ignore
        )
        self.preprocessed_responses = pd.concat(
            [self.preprocessed_responses, new_preprocessed_responses]
        )

        # categories_display is dict of categories to the deduplicated set of all responses
        new_df_series = new_preprocessed_responses.stack().reset_index(drop=True)
        df_series = self.preprocessed_responses.stack().reset_index(drop=True)
        self.response_counts = df_series.value_counts().to_dict()
        self.categorized_dict["Uncategorized"].update(set(new_df_series) - {"nan", "missing data"})

        new_categorized_data = pd.concat(
            [self.raw_data.iloc[old_data_size:, 0], new_preprocessed_responses], axis=1
        )
        self.categorized_data = pd.concat([self.categorized_data, new_categorized_data], axis=0)

        self.categorized_data.loc[
            old_data_size:, "Uncategorized"
        ] = 1  # Everything new starts uncategorized
        self.categorized_data.loc[old_data_size:, "Missing data"] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        logging_utils.format_and_log_data_for_debug(logger, vars(self))
        logger.info("Data structures populated successfully")

    def save_project(self, file_path: str, user_interface_variables_to_add: dict[str, Any]):
        logger.info("Preparing to save project data")

        data_to_save = {
            "raw_data": self.raw_data.to_json(),
            "preprocessed_responses": self.preprocessed_responses.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": self.response_counts,
            "categorized_dict": {k: list(v) for k, v in self.categorized_dict.items()},
        }
        data_to_save.update(user_interface_variables_to_add)

        # Pandas NAType is not JSON serializable
        def _none_handler(o):
            if pd.isna(o):
                return None

        logger.info("Calling file handler to save project data")
        self.file_handler.save_data_to_json(file_path, data_to_save, handler=_none_handler)

    def export_data_to_csv(self, file_path: str, categorization_type: str):
        logger.info("Preparing to export categorized data to csv")

        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        self.export_df = self.categorized_data.drop(columns=self.response_columns)
        if categorization_type == "Multi":
            self.export_df.drop("Uncategorized", axis=1, inplace=True)

        logger.info("Calling file handler  export categorized data to csv")
        self.file_handler.export_dataframe_to_csv(file_path, self.export_df)

    ### ----------------------- Helper functions ----------------------- ###
    def fuzzy_match(self, preprocessed_responses: pd.DataFrame, match_string: str) -> pd.DataFrame:
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

    def process_fuzzy_match_results(self, threshold_value: float) -> pd.DataFrame:
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

    def create_bool_mask_for_responses_in_data(self, responses: set[str]) -> pd.Series:
        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        return mask

    def remove_responses_from_category(self, responses: set[str], category: str, mask: pd.Series):
        self.categorized_data.loc[mask, category] = 0
        self.categorized_dict[category] -= responses

    def add_responses_to_categories(
        self, responses: set[str], categories: set[str], mask: pd.Series
    ):
        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categorized_dict[category].update(responses)

    def preprocess_text(self, text: Any) -> str:
        if text is None:
            return "nan"

        text = str(text).lower()
        # Convert one or more of any kind of space to single space
        text = re.sub(r"\s+", " ", text)
        # Remove special characters
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = text.strip()
        return text

    def categorize_missing_data(self) -> None:
        def is_missing(value) -> bool:
            return pd.isna(value) or value is None or value == "missing data" or value == "nan"

        # Boolean mask where each row is True if all elements are missing
        all_missing_mask = self.preprocessed_responses.map(is_missing).all(axis=1)  # type: ignore

        logger.debug(
            f"""Categorizing missing data\n
            categorized_data (before):\n{self.categorized_data.head()}\n"""
        )
        self.categorized_data.loc[all_missing_mask, "Missing data"] = 1
        self.categorized_data.loc[all_missing_mask, "Uncategorized"] = 0
        logger.debug(f"categorized_data (after):\n{self.categorized_data.head()}\n" "")

    def validate_loaded_json(
        self, loaded_json_data: dict[str, Any], expected_data: dict[str, Any]
    ) -> Tuple[bool, str]:
        # NOTE: self.expected_json_structure is passed in. This needs to be updated when the data structure changes.
        logger.debug("Validating project data")

        if not loaded_json_data:
            logger.debug(f"loaded_json_data:\n{loaded_json_data}")
            return False, "Loaded project data is empty"

        if unexpected_keys := set(loaded_json_data.keys()) - set(expected_data.keys()):
            logger.debug(
                f"""loaded_json_data.keys:\n{loaded_json_data.keys()}\n
                expected_data.keys:\n{expected_data.keys()}"""
            )
            return False, f"Unexpected variables loaded: {', '.join(unexpected_keys)}"

        for expected_key, expected_type in expected_data.items():
            if expected_key not in loaded_json_data:
                logger.debug(
                    f"""expected_key:\n{expected_key}\n
                    loaded_json_data.keys:\n{loaded_json_data.keys()}"""
                )
                return False, f"Variable '{expected_key}' is missing from loaded project data"

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
        responses_and_counts = [
            (response, self.response_counts.get(response, 0))
            for response in self.categorized_dict[category]
        ]

        # Sort first by score and then alphabetically
        return sorted(responses_and_counts, key=lambda x: (pd.isna(x[0]), -x[1], x[0]))

    def format_categories_metrics(
        self, is_including_missing_data: bool
    ) -> list[Tuple[str, int, str]]:
        formatted_categories_metrics = []

        for category, responses in self.categorized_dict.items():
            count = self.calculate_count(responses)
            if not is_including_missing_data and category == "Missing data":
                percentage_str = ""
            else:
                percentage = self.calculate_percentage(responses, is_including_missing_data)
                percentage_str = f"{percentage:.2f}%"
            formatted_categories_metrics.append((category, count, percentage_str))

        return formatted_categories_metrics

    def calculate_count(self, responses: set[str]) -> int:
        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(self, responses: set[str], is_including_missing_data: bool) -> float:
        count = self.calculate_count(responses)

        total_responses = sum(self.response_counts.values())

        if not is_including_missing_data:
            missing_data_count = self.calculate_count(self.categorized_dict["Missing data"])
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0
