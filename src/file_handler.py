"""
This module provides functionality for handling file operations, specifically focusing on reading from and writing to CSV, XLSX, and JSON files. It includes the FileHandler class which encompasses methods for:

- Reading data from CSV or XLSX files and returning it as a pandas DataFrame.
- Loading data from JSON files and returning it as a dictionary.
- Exporting pandas DataFrames to CSV files.
- Saving data to JSON files.

The FileHandler class utilizes the pandas library for DataFrame manipulation, the chardet library for character encoding detection in CSV files, and the json library for JSON file interactions. Exception handling and logging are integral parts of the file operations to ensure reliability and traceability of the operations performed.

External Libraries Used:
- pandas: For data manipulation and analysis.
- chardet: For detecting the character encoding of CSV files.
- json: For parsing and saving JSON files.
- logging: For logging information, warnings, and errors during file operations.

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
import chardet
import pandas as pd
import json
from typing import Any

logger = logging.getLogger(__name__)


class FileHandler:
    """
    A class for handling file operations including reading from and writing to CSV, XLSX, and JSON files.

    Methods:
        __init__: Initializes the FileHandler object.
        read_csv_or_xlsx_to_dataframe: Reads data from a CSV or XLSX file and returns it as a pandas DataFrame.
        load_json: Loads data from a JSON file and returns it as a dictionary.
        export_dataframe_to_csv: Exports a pandas DataFrame to a CSV file.
        save_data_to_json: Saves data to a JSON file.
    """

    def __init__(self) -> None:
        logger.info("Initializing file handler")

    def read_csv_or_xlsx_to_dataframe(self, file_path: str) -> pd.DataFrame:
        """
        Reads data from a CSV or XLSX file and returns it as a pandas DataFrame.

        Args:
            file_path (str): The path of the CSV or XLSX file to be read.

        Returns:
            pd.DataFrame: The DataFrame containing data read from the file.

        Raises:
            ValueError: If the file format is not supported (.csv or .xlsx).
            Exception: If any other error occurs during file reading.
        """

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
            logger.exception("")
            raise

    def load_json(self, file_path: str) -> dict[str, Any]:
        """
        Loads data from a JSON file and returns it as a dictionary.

        Args:
            file_path (str): The path of the JSON file to be read.

        Returns:
            dict[str, Any]: The dictionary containing data read from the file.

        Raises:
            ValueError: If the file format is not .json.
            Exception: If any other error occurs during file reading.
        """

        try:
            if not file_path.endswith(".json"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .json")

            logger.info('Loading json file: "%s"', file_path)
            with open(file_path, "r") as f:
                data = json.load(f) or {}  # Return empty dict if empty json

            logger.info("File loaded successfully")
            return data

        except Exception:
            logger.exception("")
            raise

    def export_dataframe_to_csv(self, file_path: str, export_df: pd.DataFrame) -> None:
        """
        Exports a pandas DataFrame to a CSV file.

        Args:
            file_path (str): The path where the CSV file will be saved.
            export_df (pd.DataFrame): The DataFrame to be exported to a CSV file.

        Raises:
            pd.errors.EmptyDataError: If the DataFrame is empty.
            ValueError: If the file format is not .csv.
            Exception: If any other error occurs during file writing.
        """

        try:
            if export_df.empty:
                logger.error("Dataframe is empty")
                logger.debug(f"export_df:\n{export_df}")
                raise pd.errors.EmptyDataError("Dataframe is empty")

            if not file_path.endswith(".csv"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .csv")

            logger.info('Exporting data to csv: "%s"', file_path)
            export_df.to_csv(file_path, index=False)
            logger.info("Data exported to csv successfully")

        except Exception:
            logger.exception("")
            raise

    def save_data_to_json(self, file_path: str, data_to_save: dict[str, Any], handler=None) -> None:
        """
        Saves data to a JSON file.

        Args:
            file_path (str): The path where the JSON file will be saved.
            data_to_save (dict[str, Any]): The data to be saved to a JSON file.
            handler (optional): A function to handle encoding of complex objects.

        Raises:
            ValueError: If the data to save is empty or the file format is not .json.
            Exception: If any other error occurs during file writing.
        """

        try:
            logger.info('Saving data to json: "%s"', file_path)

            if not data_to_save:
                logger.error("Project data is empty")
                logger.debug(f"data_to_save:{data_to_save}")
                raise ValueError("Project data is empty")

            if not file_path.endswith(".json"):
                raise ValueError("Unsupported file format.\n\nFile must be of type .json")

            with open(file_path, "w") as f:
                json.dump(data_to_save, f, default=handler)

            logger.info("Data saved successfully")

        except Exception:
            logger.exception("")
            raise
