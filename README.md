# Intro

This is a desktop app that allows the user to import a dataset, fuzzy match strings against that dataset, categorize the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses to questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

**NOTE: THIS PROGRAM ASSUMES THAT THE FIRST COLUMN OF THE IMPORTED DATA CONTAINS UUIDS AND THE SUBSEQUENT COLUMNS CONTAIN RESPONSES.**

## Installing Required Packages

Open your command line tool and navigate to the project directory. Run the following command to install the required packages:

```sh
pip install pandas chardet thefuzz
```

Or simply:

```sh
pip install -r requirements.txt
```

## Updating Packages

To ensure all the packages are up to date, run the following command:

```sh
pip install --upgrade pandas thefuzz chardet pytest
```

## Running the Application

Once all packages are installed and updated, you can run the application by executing `main.py` from the `src` directory:

```sh
python src/main.py
```


# Requirements

- pandas
- thefuzz
- chardet
- pytest

# To do

### Functionality:

- Ability to switch back to multi from single (spit warning "can't go back")
- Ability to sort results by other dimensions
- Ability to pass in a list of category names?
- Might need to handle different formattings of missing data coming from different sources (Q, excel, SPSS, etc), ideally separate from people responding with things like "N/A" etc.

### UI:

- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Tooltips (for what exactly?)
- Make buttons size properly (all the same rectangles).

### Future:

- Maybe an auto mode? i.e., auto-match and categorize for each category in the list, for a pre-defined threshold.
- Documentation (e.g. docstrings).
- User guide for the end user.
- Environment Setup Script.
- Unit tests.
- Logging.
- GUI tests?
- Dependency update tool?
- Dockerfile?

