#
# TODO: repeat out category columns for each response column and categorize each response column seperately

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
        self.categorized_dict = {"Uncategorized": set()}
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

    def categorize_responses(
        self, responses: set[str], categories: set[str], categorization_type: str
    ):
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

    def recategorize_responses(self, responses: set[str], categories: set[str]):
        logger.info("Recategorizing responses")
        for response_column in self.response_columns:
            mask = self.categorized_data[response_column].isin(responses)
            self.remove_responses_from_category(
                responses, self.currently_displayed_category, response_column, mask
            )
            for category in categories:
                self.add_responses_to_category(responses, category, response_column, mask)
        logger.info("Responses recategorized")

    def create_category(self, new_category: str):
        logger.info('Creating new category: "%s"', new_category)

        if new_category in self.categorized_dict.keys():
            message = "Category already exists"
            logger.warning(message)
            logger.debug(f"categorized_dict.keys:\n{self.categorized_dict.keys()}")
            return False, message

        for response_column in self.response_columns:
            col_name = f"{new_category}_{response_column}"
            self.categorized_data[col_name] = 0
        self.categorized_dict[new_category] = set()

        message = "Category created successfully"
        logger.info(message)
        return True, message

    def rename_category(self, old_category: str, new_category: str):
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

    def delete_categories(self, categories_to_delete: set[str], categorization_type: str):
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

                del self.categorized_dict[category]
                self.categorized_data.drop(columns=f"{category}_{response_column}", inplace=True)

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

        new_stacked_responses = new_preprocessed_responses.stack(dropna=False).reset_index(
            drop=True
        )
        self.stacked_responses = self.preprocessed_responses.stack(dropna=False).reset_index(
            drop=True
        )
        self.response_counts = self.stacked_responses.value_counts(dropna=False).to_dict()
        # categorized_dict is dict of categories to the deduplicated set of all responses
        self.categorized_dict["Uncategorized"].update(set(new_stacked_responses.dropna()))

        new_categorized_data = pd.concat(
            [self.raw_data.iloc[old_data_size:, 0], new_preprocessed_responses], axis=1
        )
        self.categorized_data = pd.concat([self.categorized_data, new_categorized_data], axis=0)

        for response_column in self.response_columns:
            # Everything starts uncategorized
            self.categorized_data.loc[old_data_size:, f"Uncategorized_{response_column}"] = 1
        self.handle_missing_data()

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

    def remove_responses_from_category(
        self, responses: set[str], category: str, response_column: str, mask: pd.Series
    ):
        self.categorized_data.loc[mask, f"{category}_{response_column}"] = 0
        self.categorized_dict[category] -= responses

    def add_responses_to_category(
        self, responses: set[str], category: str, response_column: str, mask: pd.Series
    ):
        self.categorized_data.loc[mask, f"{category}_{response_column}"] = 1
        self.categorized_dict[category].update(responses)

    def preprocess_text(self, text: Any) -> str | NAType:
        if pd.isna(text):
            return pd.NA

        text = str(text).lower()
        # Convert one or more of any kind of space to single space
        text = re.sub(r"\s+", " ", text)
        # Remove special characters
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = text.strip()
        return text

    def handle_missing_data(self) -> None:
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
            (str(response), self.sum_response_counts({response}))
            for response in self.categorized_dict[category]
        ]

        # Sort first by score and then alphabetically
        return sorted(responses_and_counts, key=lambda x: (-x[1], x[0]))

    def format_categories_metrics(
        self, is_including_missing_data: bool
    ) -> list[Tuple[str, int, str]]:
        formatted_categories_metrics = []

        for category, responses in self.categorized_dict.items():
            count = self.sum_response_counts(responses)
            percentage = self.calculate_percentage(responses, is_including_missing_data)
            percentage_str = f"{percentage:.2f}%"
            formatted_categories_metrics.append((category, count, percentage_str))

        return formatted_categories_metrics

    def sum_response_counts(self, responses: set) -> int:
        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(self, responses: set, is_including_missing_data: bool) -> float:
        count = self.sum_response_counts(responses)

        if is_including_missing_data:
            total_responses = sum(self.response_counts.values())
        else:
            missing_data_count = self.sum_response_counts({pd.NA})
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0
