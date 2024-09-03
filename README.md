# Intro

This is a desktop app that allows the user to import a dataset, perform fuzzy matching of text against that dataset, categorize the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses for questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

# Prerequisites

**Python**: Ensure Python is installed on your system. Download and install the latest version from [Python's official website](https://www.python.org/downloads/). During installation, ensure you select the option to 'Add Python to PATH'.

**Pip**: It's recommended to use the latest version of pip. Update pip using the following command in your command line tool _(such as Windows PowerShell)_:

```powershell
python -m pip install --upgrade pip
```

# Installation

1. Make a copy of the project folder on your local system.

2. In your command line tool, navigate to the copied project root directory:

```powershell
cd 'C:\Users\[user]\path\to\project'
```

3. Run the following command to install the required packages:

```powershell
pip install -r requirements.txt
```

# Running the Application

Once all packages are installed and updated, you can run the application by executing `main.py` from the `src` directory:

```powershell
python src/main.py
```

# Using the Application

1. `Start New Project` or `Append Data`: Import your dataset.
2. `Fuzzy Match`: Perform the match against the inputted string. Adjust the `Fuzzy threshold` as needed.
3. `Create Category`, `Rename Category`, and `Delete Category`: Self explanatory.
4. `Categorize Results`: Categorize the selected fuzzy match results into the selected category/categories.
5. `Display category results`: Displays the responses contained within the selected category
6. `Recategorize Results`: Recategorize the responses from the category results into the selected category/categories.
7. `Export Data`: Once categorization is complete, export the data to CSV for further use.
8. `Save Project` and `Load Project`: Save the app's current state so you can return to it later.

**NOTE:**

- **'New Project' or 'Append Data'**:
  - Accepts only `.csv` or `.xlsx` files.
  - Assumes the first column contains UUIDs.
  - Assumes subsequent columns contain open-ended text responses.
- **Loading a Project:**
  - Accepts only `.json` files.
  - These files must have been previously saved from this app.

# Documentation

The HTML documentation for this project is generated with `pdoc3`.
You can view it by opening the files located in the `docs` directory with your web browser.

To generate the docs, first set the Python path to include this project directory and the scripts directory:

```powershell
$env:PYTHONPATH = "path\to\project\directory"
$env:PYTHONPATH += "path\to\project\directory\src"
```

Then generate the docs with the following command:

```powershell
pdoc --html --output-dir docs --force src
```

# Tests

To run the test suite, enter the following command in the project root directory:

```powershell
pytest
```

You can run tests in a specific file or directory by providing the path:

```powershell
pytest tests/test_specific_module.py
```

For more verbose output, use the -v flag:

```powershell
pytest -v
```

# Future developments

- Implement the ability to switch back to multi from single categorization mode - spit warning "can't go back"
- Enable sorting results by different dimensions.
- Enable passing in a list of category names
- Enhance UI, such as creating a box that always shows 'Uncategorized' responses, as well as tooltips and button sizing.
- Explore the possibility of an auto mode for automated matching and categorization.
- Implement better exception handling, write more unit tests and more in-depth debug logging

# Author

Louie Atkins-Turkish
Email: louie.atk@gmail.com
Created on: November 30, 2023
