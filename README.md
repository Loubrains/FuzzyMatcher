# Intro

This is a desktop app that allows the user to import a dataset, fuzzy match strings against that dataset, categorizing the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses to questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

**NOTE: THIS PROGRAM ASSUMES THAT THE FIRST COLUMN OF THE IMPORTED DATA CONTAINS UUIDS AND THE SUBSEQUENT COLUMNS CONTAIN RESPONSES.**

# Running the app

To run the app, make sure the latest version of python and all the required libraries are installed, and then run main.py with a python interpreter of your choice.

# Requirements

- tkinter
- ctypes
- pandas
- re
- chardet
- thefuzz
- json
- io

# To do

### Functionality:

- Ability to switch back to multi from single (spit warning "can't go back").
- Ability to sort results by other dimensions
- Pass in a list of category names?
- Might need to handle different formattings of missing data coming from different sources (Q, excel, SPSS, etc), ideally seperate from people responding with things like "N/A" etc.

### UI:

- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Tooltips (for what exactly?)
- Make buttons size properly (all the same rectangles)

### Comments and documentation

### Future:

- Separate logic from UI.
- Unit tests.
- Maybe an auto mode? i.e. auto-match and categorize for each category in the list, for a pre-defined threshold.
