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

### Functionality:

- ~~Ability to recategorize results.~~
- ~~Start program with New Project / Load Project dialogue box, and setup program accordingly~~
- Ability to save current state. (The framework is there, just need to select the appropriate variables to save)
- Ability to load previously saved state. (Same note as above)
- Delete categories.
- Ability to switch back to multi from single (spit warning "can't go back").
- When typing string, press enter to press associated button/do associated action.
- Redisplay category results upon category updates (only relevant in single categorization mode).
- Make an executable that includes the python script (for future editing).
- Pass in a list of category names?

### UI:

- All display boxes should go to the bottom of the window.
- Widen display boxes.
- Set column sizes to minimum required to display results.
- Align tops and bottoms of display boxes.
- Sort category results display first by count and second alphabetically.
- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Ability to sort match results by other dimensions.
- Text wrapping (it's cuttong off 'y' to look like 'v').

### Comments and documentation

### Future:

- More modularization.
- Unit tests.
- Maybe an auto mode? i.e. auto-match and categorize for each category in the list, for a pre-defined threshold.
