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

    def create_category(self, new_category):
        if not new_category:
            return False, "Category name cannot be empty"

        if new_category in self.categorized_data.columns:
            return False, "Category already exists"

        self.categorized_data[new_category] = 0
        self.categorized_dict[new_category] = set()
        return True, "Category created successfully"

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
