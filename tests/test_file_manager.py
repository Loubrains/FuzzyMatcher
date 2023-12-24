import pytest
import pandas as pd
import os
import json
from src.file_manager import FileManager

file_manager = FileManager()


### ----------------------- Fixtures ----------------------- ###
@pytest.fixture
def example_csv_file(tmpdir):
    path = os.path.join(tmpdir, "data.csv")
    pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}).to_csv(path, index=False)
    return str(path)


@pytest.fixture
def empty_csv_file(tmpdir):
    path = os.path.join(tmpdir, "empty.csv")
    pd.DataFrame().to_csv(path, index=False)
    return str(path)


@pytest.fixture
def example_dataframe():
    return pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})


@pytest.fixture
def empty_dataframe():
    return pd.DataFrame()


@pytest.fixture
def example_dict():
    return {"key1": "value1", "key2": "value2"}


@pytest.fixture
def empty_dict():
    return {}


@pytest.fixture
def example_json_file(tmpdir, example_dict):
    path = os.path.join(tmpdir, "data.json")
    with open(path, "w") as f:
        json.dump(example_dict, f)
    return str(path)


@pytest.fixture
def empty_json_file(tmpdir):
    path = os.path.join(tmpdir, "empty.json")
    with open(path, "w") as f:
        json.dump({}, f)
    return str(path)


### ----------------------- Tests ----------------------- ###
@pytest.mark.parametrize("file_path", ["example_csv_file", "empty_csv_file"])
def test_read_csv_to_dataframe(file_path, request):
    file_path = request.getfixturevalue(file_path)
    df = file_manager.read_csv_or_xlsx_to_dataframe(file_path)
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize(
    "file_path, dataframe",
    [("example_csv_file", "example_dataframe"), ("empty_csv_file", "empty_dataframe")],
)
def test_export_dataframe_to_csv(file_path, dataframe, request, tmpdir):
    file_path = os.path.join(tmpdir, request.getfixturevalue(file_path))
    dataframe = request.getfixturevalue(dataframe)
    file_manager.export_dataframe_to_csv(str(file_path), dataframe)
    assert os.path.exists(file_path)


@pytest.mark.parametrize("file_path", ["example_json_file", "empty_json_file"])
def test_load_json(file_path, request):
    file_path = request.getfixturevalue(file_path)
    data = file_manager.load_json(file_path)
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "file_path, example_dict",
    [("example_json_file", "example_dict"), ("empty_json_file", "empty_dict")],
)
def test_save_example_to_json(file_path, example_dict, request, tmpdir):
    file_path = os.path.join(tmpdir, request.getfixturevalue(file_path))
    example_dict = request.getfixturevalue(example_dict)
    file_manager.save_data_to_json(str(file_path), example_dict)
    with open(file_path, "r") as f:
        data = json.load(f)
    assert data == example_dict
