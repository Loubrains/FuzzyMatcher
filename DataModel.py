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
            return (
                pd.isna(value)
                or value is None
                or value == "missing data"
                or value == "nan"
            )

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
            message = "A category with this name already exists."
            return False, message

        if old_category == "Missing data":
            message = 'You cannot rename "Missing data".'
            return False, message

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)
        message = "Category renamed successfully"
        return True, message

    def delete_categories(
        self, categories_to_delete: set[str], categorization_type: str
    ):
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
                percentage = self.calculate_percentage(
                    responses, is_including_missing_data
                )
                percentage_str = f"{percentage:.2f}%"
            formatted_categories_metrics.append((category, count, percentage_str))

        return formatted_categories_metrics

    def calculate_count(self, responses: set[str]) -> int:
        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(
        self, responses: set[str], is_including_missing_data: bool
    ) -> float:
        count = self.calculate_count(responses)

        total_responses = sum(self.response_counts.values())

        if not is_including_missing_data:
            missing_data_count = self.calculate_count(
                self.categorized_dict["Missing data"]
            )
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0

    def preprocess_text(self, text: Any) -> str:
        text = str(text).lower()
        text = re.sub(
            r"\s+", " ", text
        )  # Convert one or more of any kind of space to single space
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

        return aggregated_results.sort_values(
            by=["score", "count"], ascending=[False, False]
        )
