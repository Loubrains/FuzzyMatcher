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

- Ability to switch back to multi from single (spit warning "can't go back").
- Ability to sort match results by other dimensions
- Handle NaNs/Missing data
- Make an executable that includes the python script (for future editing).
- Pass in a list of category names?
- Ability to append more data? (i.e. new cases)
- ~~When typing string, press enter to press associated button/do associated action.~~
- ~~Exiting file import should keep you in the application~~
- ~~Ability to delete categories. (right click or button?)~~
- ~~Ability to rename categories. (right click or button?)~~
- ~~Remove startup dialog, have it start up with empty data structures, new project/load project will populate the data~~
- ~~Ability to recategorize results.~~
- ~~Start program with New Project / Load Project dialogue box, and setup program accordingly~~
- ~~Ability to save current state. (The framework is there, just need to select the appropriate variables to save)~~
- ~~Ability to load previously saved state. (Same note as above)~~
- ~~Redisplay category results upon category updates. (for currently displayed category, which may not be the one we're categorizing responses into)~~

### UI:

- Sort category results display first by count and second alphabetically.
- Show percentages next to category counts
- Set column sizes to minimum required to display results.
- Align tops and bottoms of display boxes.
- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Tooltips ti display treeview entries that run off the frame.
- ~~Text wrapping (it's cuttong off 'y' to look like 'v').~~
- ~~All display boxes should stretch to the bottom of the window.~~

### Comments and documentation

### Future:

- Separate logic from UI.
- Unit tests.
- Maybe an auto mode? i.e. auto-match and categorize for each category in the list, for a pre-defined threshold.

### For the lols:

- Play CODEX installer 8-bit music
- Closing the program reopens it again
- Donation popup box
