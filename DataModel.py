import re
from typing import Any
from thefuzz import fuzz
import pandas as pd


class DataModel:
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
