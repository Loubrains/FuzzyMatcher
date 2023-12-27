import logging
import chardet
import pandas as pd
import json
from typing import Any

# Setup logging
logger = logging.getLogger(__name__)


class FileManager:
    def read_csv_or_xlsx_to_dataframe(self, file_path: str) -> pd.DataFrame:
        try:
            logger.info("Reading file: %s", file_path)
            if file_path.endswith(".csv"):
                with open(file_path, "rb") as file:
                    encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
                df = pd.read_csv(file_path, encoding=encoding)
            elif file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path, engine="openpyxl")
            else:
                raise ValueError("Unsupported file format.\n\nFile must be of type .csv or .xlsx")

            logger.info("File read successfully")
            return df

        except Exception as e:
            logger.exception("Failed to read file: %s", e)
            raise

    def load_json(self, file_path: str) -> dict[str, Any]:
        try:
            if file_path.endswith(".json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                return data or {}
            else:
                raise ValueError("Unsupported file format.\n\nFile must be of type .json")
        except Exception as e:
            raise e

    def export_dataframe_to_csv(self, file_path: str, export_df: pd.DataFrame) -> None:
        try:
            if export_df.empty:
                return
            export_df.to_csv(file_path, index=False)
        except Exception as e:
            raise e

    def save_data_to_json(self, file_path: str, data_to_save: dict[str, Any], handler=None) -> None:
        try:
            if not data_to_save:
                return
            with open(file_path, "w") as f:
                json.dump(data_to_save, f, default=handler)
        except Exception as e:
            raise e
