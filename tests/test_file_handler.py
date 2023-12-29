import pytest
import pandas as pd
import os
import chardet
import json
from src.file_handler import FileHandler

file_handler = FileHandler()


### ----------------------- Fixtures ----------------------- ###
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
def example_csv_file(tmpdir, example_dataframe):
    path = os.path.join(tmpdir, "data.csv")
    example_dataframe.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def example_xlsx_file(tmpdir, example_dataframe):
    path = os.path.join(tmpdir, "data.xlsx")
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
        ("example_csv_file", "example_dataframe", False),
        ("empty_csv_file", None, True),
        ("example_xlsx_file", "example_dataframe", False),
        ("empty_xlsx_file", "empty_dataframe", False),
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
        expected_data = request.getfixturevalue(expected_data)
        pd.testing.assert_frame_equal(data, expected_data, check_dtype=True)


@pytest.mark.parametrize(
    "test_file, expected_data, expect_exception",
    [
        ("example_json_file", "example_dict", False),
        ("empty_json_file", "empty_dict", False),
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
        expected_data = request.getfixturevalue(expected_data)
        assert data == expected_data


@pytest.mark.parametrize(
    "test_file, file_path, expected_data, expect_exception",
    [
        ("example_dataframe", "example_csv_file", "example_dataframe", False),
        ("empty_dataframe", "empty_csv_file", None, True),
        ("example_dataframe", "incorrect_format_file", None, True),
    ],
)
def test_export_dataframe_to_csv(
    test_file, file_path, expected_data, expect_exception, tmpdir, request
):
    data = request.getfixturevalue(test_file)
    file_path = str(os.path.join(tmpdir, request.getfixturevalue(file_path)))

    if expect_exception:
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            file_handler.export_dataframe_to_csv(file_path, data)

    else:
        file_handler.export_dataframe_to_csv(file_path, data)
        assert os.path.exists(file_path)

        with open(file_path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
        data = pd.read_csv(file_path, encoding=encoding)
        expected_data = request.getfixturevalue(expected_data)

        pd.testing.assert_frame_equal(data, expected_data, check_dtype=True)


@pytest.mark.parametrize(
    "test_file, file_path, expected_data, expect_exception",
    [
        ("example_dict", "example_json_file", "example_dict", False),
        ("empty_dict", "empty_json_file", None, True),
        ("example_dict", "incorrect_format_file", None, True),
    ],
)
def test_save_data_to_json(test_file, file_path, expected_data, expect_exception, tmpdir, request):
    data = request.getfixturevalue(test_file)
    file_path = os.path.join(tmpdir, request.getfixturevalue(file_path))

    if expect_exception:
        with pytest.raises(ValueError):
            file_handler.save_data_to_json(file_path, data)

    else:
        file_handler.save_data_to_json(file_path, data)
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            data = json.load(f)
        expected_data = request.getfixturevalue(expected_data)
        assert data == expected_data
