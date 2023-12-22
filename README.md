# Intro

This is a desktop app that allows the user to import a dataset, perform fuzzy matching of text against that dataset, categorize the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses for questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

## Prerequisites
Before running the application, ensure you have Python installed on your system. If not, download and install the latest version from [Python's official website](https://www.python.org/downloads/).

It's also recommended to have the latest version of pip. Update pip using the following command in your command line tool:

```sh
python -m pip install --upgrade pip
```

## Installing Required Packages

In your command line tool, navigate to the project directory. Run the following command to install the required packages:

```sh
pip install -r requirements.txt
```

## Running the Application

Once all packages are installed and updated, you can run the application by executing `main.py` from the `src` directory:

```sh
python src/main.py
```

# Using the Application
1. Start New Project or Append Data: Import your dataset.
2. Fuzzy Match: Input a string to match and adjust the fuzziness threshold as needed.
3. Create Category, Rename Category, Delete Category
4. Categorize Results: categorize the selected fuzzy match results into the selected category/categories.
5. Export Data: Once categorization is complete, export the data for further use.
6. Save Project and Load Project: save the app's current state so you can return to it later.

**NOTE:**
- **'New Project' or 'Append Data'**:
    - Accepts only `.csv` or `.xlsx` files.
    - Assumes the first column contains UUIDs.
    - Assumes subsequent columns contain open-ended text responses.
- **Loading a Project:**
    - Accepts only `.json` files.
    - These files must have been previously saved from this app.

# To do

### Functionality:

- Implement the ability to switch back to multi from single categorization mode - spit warning "can't go back"
- Enable sorting results by different dimensions.
- Enable passing in a list of category names
- Consider handling various formats of missing data (e.g., from Q, Excel, SPSS).
- Address UI enhancement ideas, such as a box that always shows 'Uncategorized' responses, tooltips and button sizing.

### Future:

- Explore the possibility of an auto mode for automated matching and categorization.
- Write user documentation and guides.
- Implement an environment setup script
- Implement unit tests and loggin
- Establish a routine for updating dependencies and consider containerization with Docker.