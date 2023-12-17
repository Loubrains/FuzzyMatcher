import chardet
import pandas as pd


class FileManager:
    def file_import(self, file_path):
        with open(file_path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
        return pd.read_csv(file_path, encoding=encoding)
