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
- All display boxes should go to the bottom of the window.
- Widen display boxes.
- Set column sizes to minimum required to display results.
- Align tops and bottoms of display boxes.
- Sort category results display first by count and second alphabetically.

### Functionality:
- Redisplay category results upon category updates (only relevant in single categorization mode).
- Ability to recategorize results.
- Save current state (json?)
- Load previously saved state.
- Pass in a list of categories.

### Comments and documentation

### Future:
- More modularization.
- Unit testst.
- Maybe an auto mode? i.e. take a list of categories, auto-match and categorize for each category in the list, for a pre-defined threshold.
