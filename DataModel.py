import re
from thefuzz import fuzz
import pandas as pd
from typing import Any


class DataModel:
    def __init__(self) -> None:
        self.initialize_data_structures()  # Empty/default variables.

    def initialize_data_structures(self):
        # Empty variables which will be populated during new project/load project
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

        # categorized_data will contain a column for each, with a 1 or 0 for each response

    def perform_fuzzy_match(self, string_to_match):
        if self.categorized_data.empty or self.categorized_data is None:
            message = "No dataset loaded"
            return False, message

        uncategorized_responses = self.categorized_dict["Uncategorized"]
        uncategorized_df = self.df_preprocessed[
            self.df_preprocessed.isin(uncategorized_responses)
        ].dropna(how="all")

        # Perform fuzzy matching on these uncategorized responses
        self.fuzzy_match_results = self.fuzzy_matching(
            uncategorized_df, string_to_match
        )
        message = "Successfully performed fuzzy match"
        return True, message

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
            message = "A category with this name already exists."
            return False, message

        if old_category == "Missing data":
            message = 'You cannot rename "Missing data".'
            return False, message

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)
        message = "Category renamed successfully"
        return True, message

    def delete_categories(self, categories_to_delete: set[str], categorization_type):
        for category in categories_to_delete:
            if (
                categorization_type == "Single"
            ):  # In single mode, return the responses from this category to 'Uncategorized'
                responses_to_reclassify = self.categorized_data[
                    self.categorized_data[category] == 1
                ].index
                for response_index in responses_to_reclassify:
                    self.categorized_data.loc[response_index, "Uncategorized"] = 1
                self.categorized_dict["Uncategorized"].update(
                    self.categorized_dict[category]
                )

            del self.categorized_dict[category]
            self.categorized_data.drop(columns=category, inplace=True)

    def preprocess_text(self, text: Any) -> str:
        text = str(text).lower()
        text = re.sub(
            r"\s+", " ", text
        )  # Convert one or more of any kind of space to single space
        text = re.sub(r"[^a-z0-9\s]", "", text)  # Remove special characters
        text = text.strip()
        return text

    def fuzzy_matching(self, df_preprocessed, match_string):
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

        df_result = pd.DataFrame(results)

        return df_result
