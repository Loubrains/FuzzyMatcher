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
            logger.info('Reading csv or xlsx file: "%s"', file_path)

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

        except Exception:
            logger.exception("Failed to read file")
            raise

    def load_json(self, file_path: str) -> dict[str, Any]:
        try:
            if not file_path.endswith(".json"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .json")

            logger.info('Loading json file: "%s"', file_path)
            with open(file_path, "r") as f:
                data = json.load(f) or {}  # Return empty dict if empty json

            logger.info("File loaded successfully")
            return data

        except Exception:
            logger.exception("Failed to load file")
            raise

    def export_dataframe_to_csv(self, file_path: str, export_df: pd.DataFrame) -> None:
        try:
            if export_df.empty:
                logger.error("Dataframe is empty")
                logger.debug(f"export_df:\n{export_df}")
                return

            if not file_path.endswith(".csv"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .csv")

            logger.info('Exporting data to csv: "%s"', file_path)
            export_df.to_csv(file_path, index=False)
            logger.info("Data exported to csv successfully")

        except Exception:
            logger.exception("Failed to export data")
            raise

    def save_data_to_json(self, file_path: str, data_to_save: dict[str, Any], handler=None) -> None:
        try:
            logger.info('Saving data to json: "%s"', file_path)

            if not data_to_save:
                logger.error("No data to save")
                logger.debug(f"data_to_save:{data_to_save}")
                return

            if not file_path.endswith(".json"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .json")

            with open(file_path, "w") as f:
                json.dump(data_to_save, f, default=handler)

            logger.info("Data saved successfully")

        except Exception:
            logger.exception("Failed to save data")
            raise
