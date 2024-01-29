import pytest
import pandas as pd
import os
import chardet
import json
from src.file_handler import FileHandler

file_handler = FileHandler()


### ----------------------- Fixtures ----------------------- ###
@pytest.fixture
def example_csv_file(tmpdir):
    path = os.path.join(tmpdir, "data.csv")
    example_dataframe = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    example_dataframe.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def example_xlsx_file(tmpdir):
    path = os.path.join(tmpdir, "data.xlsx")
    example_dataframe = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    example_dataframe.to_excel(path, index=False)
    return str(path)


@pytest.fixture
def empty_csv_file(tmpdir):
    path = os.path.join(tmpdir, "empty.csv")
    pd.DataFrame().to_csv(path, index=False)
    return str(path)


@pytest.fixture
def empty_xlsx_file(tmpdir):
    path = os.path.join(tmpdir, "empty.xlsx")
    pd.DataFrame().to_excel(path, index=False)
    return str(path)


@pytest.fixture
def example_json_file(tmpdir):
    path = os.path.join(tmpdir, "data.json")
    example_dict = {"key1": "value1", "key2": "value2"}
    with open(path, "w") as f:
        json.dump(example_dict, f)
    return str(path)


@pytest.fixture
def empty_json_file(tmpdir):
    path = os.path.join(tmpdir, "empty.json")
    with open(path, "w") as f:
        json.dump({}, f)
    return str(path)


@pytest.fixture
def incorrect_format_file(tmpdir):
    path = os.path.join(tmpdir, "data.txt")  # Incorrect file format
    # Create a dummy text file
    with open(path, "w") as f:
        f.write("Some content")
    return str(path)


### ----------------------- Tests ----------------------- ###
@pytest.mark.parametrize(
    "test_file, expected_data, expect_exception",
    [
        ("example_csv_file", pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}), False),
        ("empty_csv_file", None, True),
        ("example_xlsx_file", pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}), False),
        ("empty_xlsx_file", pd.DataFrame(), False),
        ("incorrect_format_file", None, True),
    ],
)
def test_read_csv_to_dataframe(test_file, expected_data, expect_exception, request):
    file_path = request.getfixturevalue(test_file)

    if expect_exception:
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            file_handler.read_csv_or_xlsx_to_dataframe(file_path)

    else:
        data = file_handler.read_csv_or_xlsx_to_dataframe(file_path)

        assert isinstance(data, pd.DataFrame)
        pd.testing.assert_frame_equal(data, expected_data, check_dtype=True)


@pytest.mark.parametrize(
    "test_file, expected_data, expect_exception",
    [
        ("example_json_file", {"key1": "value1", "key2": "value2"}, False),
        ("empty_json_file", {}, False),
        ("incorrect_format_file", None, True),
    ],
)
def test_load_json(test_file, expected_data, expect_exception, request):
    file_path = request.getfixturevalue(test_file)

    if expect_exception:
        with pytest.raises(ValueError):
            file_handler.load_json(file_path)

    else:
        data = file_handler.load_json(file_path)

        assert isinstance(data, dict)
        assert data == expected_data


@pytest.mark.parametrize(
    "test_dataframe, file_path, expected_data, expect_exception",
    [
        (
            pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}),
            "example_csv_file",
            pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}),
            False,
        ),
        (pd.DataFrame(), "empty_csv_file", None, True),
        (pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}), "incorrect_format_file", None, True),
    ],
)
def test_export_dataframe_to_csv(
    test_dataframe, file_path, expected_data, expect_exception, tmpdir, request
):
    file_path = str(os.path.join(tmpdir, request.getfixturevalue(file_path)))

    if expect_exception:
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            file_handler.export_dataframe_to_csv(file_path, test_dataframe)

    else:
        file_handler.export_dataframe_to_csv(file_path, test_dataframe)
        assert os.path.exists(file_path)

        with open(file_path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
        data = pd.read_csv(file_path, encoding=encoding)

        pd.testing.assert_frame_equal(data, expected_data, check_dtype=True)


@pytest.mark.parametrize(
    "test_data, file_path, expected_data, expect_exception",
    [
        (
            {"key1": "value1", "key2": "value2"},
            "example_json_file",
            {"key1": "value1", "key2": "value2"},
            False,
        ),
        ({}, "empty_json_file", None, True),
        ({"key1": "value1", "key2": "value2"}, "incorrect_format_file", None, True),
    ],
)
def test_save_data_to_json(test_data, file_path, expected_data, expect_exception, tmpdir, request):
    file_path = os.path.join(tmpdir, request.getfixturevalue(file_path))

    if expect_exception:
        with pytest.raises(ValueError):
            file_handler.save_data_to_json(file_path, test_data)

    else:
        file_handler.save_data_to_json(file_path, test_data)
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            data = json.load(f)
        assert data == expected_data
