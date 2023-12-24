import re
from thefuzz import fuzz
import pandas as pd
from io import StringIO
from typing import Any
from file_manager import FileManager


class DataModel:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager
        self.initialize_data_structures()  # Empty/default variables.

    def initialize_data_structures(self):
        # Empty variables which will be populated during new project/load project
        # categorized_data will contain a uuids, responses, and column for each category, with a 1 or 0 for each response
        self.df = pd.DataFrame()
        self.df_preprocessed = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categorized_dict = {
            "Uncategorized": set(),
            "Missing data": {"nan", "missing data"},
        }
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])
        self.currently_displayed_category = "Uncategorized"

        # For validation on load project.
        # NOTE: Update this when the data structure changes.
        # TODO: Need to update this to be more specific (e.g. dict[str, set[str]) and handle stringified json too
        self.expected_json_structure = {
            "df": str,
            "df_preprocessed": str,
            "response_columns": list,
            "categorized_data": str,
            "response_counts": dict,
            "categories_display": dict,
            "categorization_type": str,
            "is_including_missing_data": bool,
        }

    ### ----------------------- Main functionality ----------------------- ###
    def perform_fuzzy_match(self, string_to_match):
        if self.categorized_data.empty or self.categorized_data is None:
            return False, "No dataset loaded"

        uncategorized_responses = self.categorized_dict["Uncategorized"]
        uncategorized_df = self.df_preprocessed[
            self.df_preprocessed.isin(uncategorized_responses)
        ].dropna(how="all")

        # Perform fuzzy matching on these uncategorized responses
        self.fuzzy_match_results = self.fuzzy_matching(uncategorized_df, string_to_match)
        return True, "Successfully performed fuzzy match"

    def categorize_responses(
        self, responses: set[str], categories: set[str], categorization_type: str
    ):
        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        if categorization_type == "Single":
            self.categorized_data.loc[mask, "Uncategorized"] = 0
            self.categorized_dict["Uncategorized"] -= responses

        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categorized_dict[category].update(responses)

    def recategorize_responses(self, responses: set[str], categories: set[str]):
        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        self.categorized_data.loc[mask, self.currently_displayed_category] = 0
        self.categorized_dict[self.currently_displayed_category] -= responses

        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categorized_dict[category].update(responses)

    def categorize_missing_data(self):
        def is_missing(value):
            return pd.isna(value) or value is None or value == "missing data" or value == "nan"

        all_missing_mask = self.df_preprocessed.map(is_missing).all(  # type: ignore
            axis=1
        )  # Boolean mask where each row is True if all elements are missing
        self.categorized_data.loc[all_missing_mask, "Missing data"] = 1
        self.categorized_data.loc[all_missing_mask, "Uncategorized"] = 0

    def create_category(self, new_category: str):
        if not new_category:
            return False, "Category name cannot be empty"

        if new_category in self.categorized_data.columns:
            return False, "Category already exists"

        self.categorized_data[new_category] = 0
        self.categorized_dict[new_category] = set()
        return True, "Category created successfully"

    def rename_category(self, old_category: str, new_category: str):
        if new_category in self.categorized_dict:
            return False, "A category with this name already exists."

        if old_category == "Missing data":
            return False, 'You cannot rename "Missing data".'

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)
        return True, "Category renamed successfully"

    def delete_categories(self, categories_to_delete: set[str], categorization_type: str):
        for category in categories_to_delete:
            if (
                categorization_type == "Single"
            ):  # In single mode, return the responses from this category to 'Uncategorized'
                responses_to_reclassify = self.categorized_data[
                    self.categorized_data[category] == 1
                ].index
                for response_index in responses_to_reclassify:
                    self.categorized_data.loc[response_index, "Uncategorized"] = 1
                self.categorized_dict["Uncategorized"].update(self.categorized_dict[category])

            del self.categorized_dict[category]
            self.categorized_data.drop(columns=category, inplace=True)

    ### ----------------------- Project Management ----------------------- ###
    def file_import_on_new_project(self, file_path: str):
        self.df = self.file_manager.read_csv_or_xlsx_to_dataframe(file_path)
        if self.df.empty:
            return False, "Dataset is empty"
        if self.df.shape[1] < 2:
            return (
                False,
                "Dataset does not contain enough columns.\n\nThe dataset should contain uuids in the first column, and the subsequent columns should contian responses",
            )
        return True, "File imported successfully"

    def populate_data_structures_on_new_project(self):
        self.df_preprocessed = pd.DataFrame(
            self.df.iloc[:, 1:].map(
                self.preprocess_text  # , na_action="ignore"
            )  # type: ignore
        )

        # categories_display is dict of categories containig the deduplicated set of all responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.categorized_dict = {
            "Uncategorized": set(df_series) - {"nan", "missing data"},
            "Missing data": {"nan", "missing data"},  # default
        }
        self.response_counts = df_series.value_counts().to_dict()
        uuids = self.df.iloc[:, 0]
        self.response_columns = list(self.df_preprocessed.columns)
        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        self.categorized_data = pd.concat([uuids, self.df_preprocessed], axis=1)
        self.categorized_data["Uncategorized"] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

    def file_import_on_load_project(self, file_path: str):
        new_data = self.file_manager.load_json(file_path)
        success, message = self.validate_loaded_json(new_data, self.expected_json_structure)
        if not success:
            return False, message

        self.data_loaded = new_data
        return True, "Project data loaded successfully"

    def validate_loaded_json(self, loaded_json_data, expected_data):
        # NOTE: self.expected_json_structure is passed in. This needs to be updated when the data structure changes.
        if not loaded_json_data:
            return False, "Loaded project data is empty"
        if unexpected_keys := set(loaded_json_data.keys()) - set(expected_data.keys()):
            return False, f"Unexpected variables loaded: {', '.join(unexpected_keys)}"

        for expected_key, expected_type in expected_data.items():
            if expected_key not in loaded_json_data:
                return False, f"Variable '{expected_key}' is missing"
            if (
                expected_type is not bool and not loaded_json_data[expected_key]
            ):  # skip the bool case (e.g. `is_including_missing_data`) since its false value can cause not(data) to evaluate true
                return False, f"Variable '{expected_key}' has no data"
            if not isinstance(loaded_json_data[expected_key], expected_type):
                return (
                    False,
                    f"Variable '{expected_key}' contains values that are not of expected type {expected_type.__name__}.",
                )

        return True, "Loaded JSON validated successfully"

    def populate_data_structures_on_load_project(self):
        # Convert JSON back to data / set default variable values
        self.df = pd.read_json(StringIO(self.data_loaded["df"]))
        self.df_preprocessed = pd.read_json(StringIO(self.data_loaded["df_preprocessed"]))
        self.response_columns = self.data_loaded["response_columns"]
        self.categorized_data = pd.read_json(StringIO(self.data_loaded["categorized_data"]))
        self.response_counts = self.data_loaded["response_counts"]
        self.categorized_dict = {
            k: set(v) for k, v in self.data_loaded["categories_display"].items()
        }
        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

        categorization_type = self.data_loaded["categorization_type"]  # Tkinter variable
        is_including_missing_data = self.data_loaded[
            "is_including_missing_data"
        ]  # Tkinter variable

        return (
            categorization_type,
            is_including_missing_data,
        )  # Return Tkinter variables back to the UI class

    def file_import_on_append_data(self, file_path):
        if self.df.empty:
            return False, "No dataset loaded.\n\nClick 'Start New Project'"
        new_data = self.file_manager.read_csv_or_xlsx_to_dataframe(file_path)
        if new_data.empty:
            return False, "Imported dataset is empty."
        if (
            new_data.shape[1] != self.df.shape[1]
        ):  # using self.df as it should have the same columns as self.categorized_data without the category columns.
            return (
                False,
                "Dataset does not have the same number of columns.\n\nThe dataset should contain UUIDs in the first column, and the subsequent columns should contain the same number of response columns as the currently loaded data.",
            )
        self.data_to_append = new_data
        return True, "File imported successfully"

    def populate_data_structures_on_append_data(self):
        self.df = pd.concat([self.df, self.data_to_append], ignore_index=True)
        old_data_size = len(self.df_preprocessed)
        new_df_preprocessed = pd.DataFrame(
            self.df.iloc[old_data_size:, 1:].map(self.preprocess_text)  # type: ignore
        )
        self.df_preprocessed = pd.concat([self.df_preprocessed, new_df_preprocessed])

        # categories_display is dict of categories to the deduplicated set of all responses
        new_df_series = new_df_preprocessed.stack().reset_index(drop=True)
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.response_counts = df_series.value_counts().to_dict()
        self.categorized_dict["Uncategorized"].update(set(new_df_series) - {"nan", "missing data"})

        new_categorized_data = pd.concat(
            [self.df.iloc[old_data_size:, 0], new_df_preprocessed], axis=1
        )
        self.categorized_data = pd.concat([self.categorized_data, new_categorized_data], axis=0)

        self.categorized_data.loc[
            old_data_size:, "Uncategorized"
        ] = 1  # Everything new starts uncategorized
        self.categorized_data.loc[old_data_size:, "Missing data"] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default
        self.fuzzy_match_results = pd.DataFrame(columns=["response", "score"])  # Default

    def save_project(self, file_path: str, user_interface_variables_to_add: dict[str, Any]):
        data_to_save = {
            "df": self.df.to_json(),
            "df_preprocessed": self.df_preprocessed.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": self.response_counts,
            "categories_display": {k: list(v) for k, v in self.categorized_dict.items()},
        }
        data_to_save.update(user_interface_variables_to_add)

        # Pandas NAType is not JSON serializable
        def _none_handler(o):
            if pd.isna(o):
                return None

        self.file_manager.save_data_to_json(file_path, data_to_save, handler=_none_handler)

    def export_data_to_csv(self, file_path, categorization_type):
        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        self.export_df = self.categorized_data.drop(columns=self.response_columns)
        if categorization_type == "Multi":
            self.export_df.drop("Uncategorized", axis=1, inplace=True)

        self.file_manager.export_dataframe_to_csv(file_path, self.export_df)

    ### ----------------------- Helper functions ----------------------- ###
    def get_responses_and_counts(self, category: str):
        responses_and_counts = [
            (response, self.response_counts.get(response, 0))
            for response in self.categorized_dict[category]
        ]
        return sorted(
            responses_and_counts, key=lambda x: (pd.isna(x[0]), -x[1], x[0])
        )  # Sort first by score and then alphabetically

    def format_categories_metrics(
        self, is_including_missing_data: bool
    ) -> list[tuple[str, str, str]]:
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

    def preprocess_text(self, text: Any) -> str:
        text = str(text).lower()
        text = re.sub(r"\s+", " ", text)  # Convert one or more of any kind of space to single space
        text = re.sub(r"[^a-z0-9\s]", "", text)  # Remove special characters
        text = text.strip()
        return text

    def fuzzy_matching(self, df_preprocessed, match_string) -> pd.DataFrame:
        def _fuzzy_match(element):
            return fuzz.WRatio(
                match_string, str(element)
            )  # Weighted ratio of several fuzzy matching protocols

        # Get fuzzy matching scores and format result: {response: score}
        results = []
        for row in df_preprocessed.itertuples(index=True, name=None):
            for response in row[1:]:
                score = _fuzzy_match(response)
                results.append({"response": response, "score": score})

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
