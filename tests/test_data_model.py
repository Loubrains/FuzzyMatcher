import pytest
import pandas as pd
import uuid
from src.file_handler import FileHandler
from src.data_model import DataModel


### ----------------------- Setup data_model with mock data ----------------------- ###
@pytest.fixture(scope="function", autouse=True)
def mock_data_model():
    file_handler = FileHandler()
    data_model = DataModel(file_handler)

    mock_data = pd.DataFrame(
        {
            "uuid": [str(uuid.uuid4()) for _ in range(5)],
            "response_1": ["Test1", pd.NA, "First response for third person", pd.NA, "Hello"],
            "response_2": [pd.NA, pd.NA, "Second response for third person", pd.NA, "Goodbye"],
            "response_3": ["Test3", pd.NA, "Third response for third person", pd.NA, pd.NA],
        }
    )

    data_model.raw_data = mock_data
    data_model.populate_data_structures_on_new_project()

    return data_model


### ----------------------- Tests ----------------------- ###
@pytest.mark.parametrize(
    "new_category, expected_result",
    [
        ("NewCategory", (True, "Category created successfully")),
        ("Uncategorized", (False, "Category already exists")),
        ("CategoryToDelete", (True, "Category created successfully")),  # additional test case
    ],
)
def test_create_category(mock_data_model, new_category, expected_result):
    assert mock_data_model.create_category(new_category) == expected_result
    if expected_result[0]:
        # Verify the new category is in categorized_dict
        assert new_category in mock_data_model.categorized_dict


@pytest.mark.parametrize(
    "setup_category, old_category, new_category, expected_result",
    [
        (
            "ExistingCategory",
            "ExistingCategory",
            "NewCategoryName",
            (True, "Category renamed successfully"),
        ),
        (
            "ExistingCategory",
            "NonExistingCategory",
            "NewCategoryName",
            (False, "A category with this name already exists."),
        ),
        (
            "NewCategoryName",
            "ExistingCategory",
            "NewCategoryName",
            (False, "A category with this name already exists."),
        ),
    ],
)
def test_rename_category(
    mock_data_model, setup_category, old_category, new_category, expected_result
):
    # Setup
    mock_data_model.create_category(setup_category)
    assert mock_data_model.rename_category(old_category, new_category) == expected_result


@pytest.mark.parametrize(
    "setup_category, category_to_delete, categorization_type, expected_uncategorized_count",
    [
        (
            "CategoryToDelete",
            "CategoryToDelete",
            "Single",
            5,
        )  # Assuming all uncategorized at the start
    ],
)
def test_delete_categories(
    mock_data_model,
    setup_category,
    category_to_delete,
    categorization_type,
    expected_uncategorized_count,
):
    # Setup
    mock_data_model.create_category(setup_category)
    mock_data_model.categorize_responses(
        set(mock_data_model.categorized_dict["Uncategorized"]),
        {setup_category},
        categorization_type,
    )
    mock_data_model.delete_categories({category_to_delete}, categorization_type)

    uncategorized_count = len(mock_data_model.categorized_dict["Uncategorized"])
    assert uncategorized_count == expected_uncategorized_count


@pytest.mark.parametrize(
    "responses, category, categorization_type, expected_category_count",
    [
        ({"Test1", "Hello"}, "Category1", "Single", 2),  # Assuming responses match the mock data
        (
            {"First response for third person", "Second response for third person"},
            "Category2",
            "Single",
            2,
        ),
    ],
)
def test_categorize_responses(
    mock_data_model, responses, category, categorization_type, expected_category_count
):
    # Setup
    mock_data_model.create_category(category)
    mock_data_model.categorize_responses(responses, {category}, categorization_type)
    category_count = len(mock_data_model.categorized_dict[category])
    assert category_count == expected_category_count


@pytest.mark.parametrize(
    "setup_categories, response, from_category, to_category, expected_counts",
    [
        (
            {"OldCategory", "NewCategory"},
            "Test1",
            "OldCategory",
            "NewCategory",
            {"OldCategory": 0, "NewCategory": 1},
        ),  # Assuming 'Test1' is a response in mock data
    ],
)
def test_recategorize_responses(
    mock_data_model, setup_categories, response, from_category, to_category, expected_counts
):
    # Setup
    for category in setup_categories:
        mock_data_model.create_category(category)
    mock_data_model.categorize_responses({response}, {from_category}, "Single")

    mock_data_model.recategorize_responses({response}, {to_category})

    from_category_count = len(mock_data_model.categorized_dict[from_category])
    to_category_count = len(mock_data_model.categorized_dict[to_category])
    assert from_category_count == expected_counts[from_category]
    assert to_category_count == expected_counts[to_category]
