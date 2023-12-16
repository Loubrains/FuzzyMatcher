from typing import Any
import re
from thefuzz import fuzz
import pandas as pd
from io import StringIO

class MultipleCategorySelectionError(Exception):
    pass

class DataProcessor:
    def __init__(self):
        self.initialize_data_structures()

    def initialize_data_structures(self):
        # Empty variables which will be populated during new project/load project
        self.is_single_categorization = True #UI MUST TALK TO YOU
        self.df_preprocessed = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categories_display = {
            "Uncategorized": set(),
            "Missing data": {"nan", "missing data"},
        }
        self.match_results = pd.DataFrame(columns=["response", "score"])
        self.currently_displayed_category = "Uncategorized"


    def populate_data_structures_new_project(self, df):
        self.df_preprocessed = pd.DataFrame(
            df.iloc[:, 1:].map(
                self.preprocess_text  # , na_action="ignore"
            )
        )

        # categories_display is dict of categories to the deduplicated set of all responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.categories_display = {
            "Uncategorized": set(df_series) - {"nan", "missing data"},
            "Missing data": {"nan", "missing data"},  # default
        }

        self.response_counts = df_series.value_counts().to_dict()

        uuids = df.iloc[:, 0]
        self.response_columns = list(self.df_preprocessed.columns)

        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        self.categorized_data = pd.concat([uuids, self.df_preprocessed], axis=1)
        self.categorized_data["Uncategorized"] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"] = 0
        self.categorized_data = self.categorize_missing_data(self.categorized_data)

        self.currently_displayed_category = "Uncategorized"  # Default (this must come before calling self.categorize_responses below)

        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default

    def populate_data_structures_load_project(self, data_loaded):
        # Convert JSON back to data / set default variable values
        self.categorization_var.set(data_loaded["categorization_var"])
        self.df_preprocessed = pd.read_json(StringIO(data_loaded["df_preprocessed"]))
        self.response_columns = data_loaded["response_columns"]
        self.categorized_data = pd.read_json(StringIO(data_loaded["categorized_data"]))
        self.response_counts = data_loaded["response_counts"]
        self.categories_display = {
            k: set(v) for k, v in data_loaded["categories_display"].items()
        }
        self.currently_displayed_category = "Uncategorized"  # Default
        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default
        self.include_missing_data_bool.set(data_loaded["include_missing_data_bool"])
    
    def populate_data_structures_append_data(self, df):
        old_data_size = len(self.df_preprocessed)
        new_df_preprocessed = pd.DataFrame(
            df.iloc[old_data_size:, 1:].map(self.preprocess_text)
        )
        self.df_preprocessed = pd.concat([self.df_preprocessed, new_df_preprocessed])

        # categories_display is dict of categories to the deduplicated set of all responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)

        self.response_counts = df_series.value_counts().to_dict()

        uuids = self.df.iloc[:, 0]
        self.response_columns = list(self.df_preprocessed.columns)

        new_categorized_data = pd.concat(
            [df.iloc[old_data_size:, 0], new_df_preprocessed], axis=1
        )

        self.categorized_data = pd.concat(
            [self.categorized_data, new_categorized_data], axis=0
        )
        self.categorized_data["Uncategorized"].iloc[
            old_data_size:
        ] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"].iloc[old_data_size:] = 0
        self.categorized_data = self.categorize_missing_data(self.categorized_data)

        self.categorized_data = pd.concat([self.categorized_data, new_categorized_data])

        self.currently_displayed_category = "Uncategorized"  # Default (this must come before calling self.categorize_responses below)
        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default

    def categorize_missing_data(self, categorized_data):
        def is_missing(value):
            return (
                pd.isna(value)
                or value is None
                or value == "missing data"
                or value == "nan"
            )

        all_missing_mask = self.df_preprocessed.map(is_missing).all(
            axis=1
        )  # Boolean mask where each row is True if all elements are missing
        categorized_data.loc[all_missing_mask, "Missing data"] = 1
        categorized_data.loc[all_missing_mask, "Uncategorized"] = 0
        return categorized_data
    


    def preprocess_text(self, text: Any) -> str:
        text = str(text).lower()
        text = re.sub(
            r"\s+", " ", text
        )  # Convert one or more of any kind of space to single space
        text = re.sub(r"[^a-z0-9\s]", "", text)  # Remove special characters
        text = text.strip()
        return text

    def fuzzy_matching(self, df_preprocessed, match_string):
        def fuzzy_match(element):
            return fuzz.WRatio(
                match_string, str(element)
            )  # Weighted ratio of several fuzzy matching protocols

        # Get fuzzy matching scores and format result: {response: score}
        results = []
        for row in df_preprocessed.itertuples(index=True, name=None):
            for response in row[1:]:
                score = fuzzy_match(response)
                results.append({"response": response, "score": score})

        df_result = pd.DataFrame(results)

        return df_result

    def make_dict_to_save(self, include_missing_data_bool):
         return {
            "is_single_categorization": self.is_single_categorization,
            "df_preprocessed": self.df_preprocessed.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": self.response_counts,
            "categories_display": {
                k: list(v) for k, v in self.categories_display.items()
            },
            "including_missing_data_bool": include_missing_data_bool,
        }
    def get_match_results(self, match_string):
        if self.df_preprocessed is not None:
            self.match_results = self.fuzzy_matching(
                self.df_preprocessed, match_string
            )
        else:
            raise TypeError("Data not found")
        
    
    def preprocess_df_for_csv_export(self):
        export_df = self.categorized_data.drop(columns=self.response_columns)

        if not self.is_single_categorization:
            export_df.drop("Uncategorized", axis=1, inplace=True)
        
        return export_df
    
    def categorize_responses(self, responses, categories):
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        if self.is_single_categorization:
            if len(categories) > 1:
                raise MultipleCategorySelectionError("ONLY ONE CATEGORY CAN BE SELECTED!!!!!!")
            
            self.categorized_data.loc[mask, "Uncategorized"] = 0
            self.categories_display["Uncategorized"] -= responses
            # Remove responses from match results because they can't be categorized anymore in single mode
            self.match_results = self.match_results[
                ~self.match_results["response"].isin(self.selected_match_responses())
            ]
        
        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categories_display[category].update(responses)
        
    
    def recategorize_responses(self, responses, categories):
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        if self.is_single_categorization and len(categories) > 1:
            raise MultipleCategorySelectionError

        self.categorized_data.loc[mask, self.currently_displayed_category] = 0
        self.categories_display[self.currently_displayed_category] -= responses

        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categories_display[category].update(responses)

    
    def create_category(self, new_category):
        if new_category and new_category not in self.categorized_data.columns:
            self.categorized_data[new_category] = 0
            self.categories_display[new_category] = set()

    def rename(self, old_category, new_category):
        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categories_display[new_category] = self.categories_display.pop(
            old_category
        )
    
    def delete_categories(self, to_delete):
        for category in to_delete:
            del self.categories_display[category]
            self.categorized_data.drop(columns=category, inplace=True)
    
    def calculate_count(self, responses):
        return sum(self.response_counts.get(response, 0) for response in responses)

# TODO: make two seperate percentage methods based off the bool idk
    def calculate_percentage(self, responses, include_missing_data_bool):
        count = self.calculate_count(responses)

        total_responses = sum(self.response_counts.values())

        if not include_missing_data_bool:
            missing_data_count = self.calculate_count(
                self.categories_display["Missing data"]
            )
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0
    
    def set_is_single_categorization(self,value):
        self.is_single_categorization = value