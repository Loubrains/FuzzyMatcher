# Intro

This is a desktop app that allows the user to import a dataset, fuzzy match strings against that dataset, categorizing the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses to questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

**NOTE: THIS PROGRAM ASSUMES THAT THE FIRST COLUMN OF THE IMPORTED DATA CONTAINS UUIDS AND THE SUBSEQUENT COLUMNS CONTAIN RESPONSES.**

# Running the app

To run the app, make sure the latest version of python is installed and all the required libraries are installed, and then run main.py

# Requirements

- pandas
- chardet
- thefuzz

# To do

### Functionality:

- Ability to switch back to multi from single (spit warning "can't go back")
- Ability to sort results by other dimensions
- Ability to pass in a list of category names?
- Might need to handle different formattings of missing data coming from different sources (Q, excel, SPSS, etc), ideally seperate from people responding with things like "N/A" etc

### UI:

- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Tooltips (for what exactly?)
- Make buttons size properly (all the same rectangles)

### Future:

- Maybe an auto mode? i.e. auto-match and categorize for each category in the list, for a pre-defined threshold
- Documentation (e.g. docstrings)
- User guide for the end user
- Environment Setup Script
- Unit tests
- Logging
- GUI tests?
- Dependancy update tool?
- Dockerfile?
