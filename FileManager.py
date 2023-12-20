import chardet
import pandas as pd
import json
from typing import Any


class FileManager:
    def read_csv_to_dataframe(self, file_path: str) -> pd.DataFrame:
        with open(file_path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
        return pd.read_csv(file_path, encoding=encoding)

    def load_json(self, file_path: str) -> dict[str, Any]:
        with open(file_path, "r") as f:
            return json.load(f)

    def save_data_to_json(
        self, file_path: str, data_to_save: dict[str, Any], handler=None
    ) -> None:
        with open(file_path, "w") as f:
            json.dump(data_to_save, f, default=handler)

    def export_dataframe_to_csv(self, file_path: str, export_df: pd.DataFrame) -> None:
        export_df.to_csv(file_path, index=False)
