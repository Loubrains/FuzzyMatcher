# Intro
This is a desktop app that allows the user to import a dataset, fuzzy match strings against that dataset, categorizing the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses to questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

**NOTE: THIS PROGRAM ASSUMES THAT THE FIRST COLUMN OF THE DATASET CONTAINS UUIDS AND THE SUBSEQUENT COLUMNS CONTAIN RESPONSES.**

# Requirements
- tkinter
- ctypes
- pandas
- re
- chardet
- thefuzz

# To do
### UI:
- all boxes go to bottom of window
- widen boxes
- set column sizes
- align tops and bottoms of displays
- sort category results display by count and then alphabetically

### FUNCTIONALITY:
- redisplay category results upon category updates (consider single vs multi)
- Recategorize results
- save current state (json?)
- load previously saved state
- pass in a list of categoires

### Comments and documentation

### FUTURE:
- more modularization
- unit tests
- maybe auto mode? (i.e. take a list of categories, auto-match and categorize for each category in the list, for a pre-defined threshold).
