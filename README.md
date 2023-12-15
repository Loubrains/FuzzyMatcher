# Intro

This is a desktop app that allows the user to import a dataset, fuzzy match strings against that dataset, categorizing the results, and export the categorized data.

The context for this is specifically for speeding up the categorization of open-ended text responses to questionnaires. This effectively replaces the broken/slow fuzzy matching functionality in Q Research Software.

**NOTE: THIS PROGRAM ASSUMES THAT THE FIRST COLUMN OF THE IMPORTED DATA CONTAINS UUIDS AND THE SUBSEQUENT COLUMNS CONTAIN RESPONSES.**

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

- Ability to append more data? (i.e. new cases)
- Remove ability to match again for responses already categorized in single mode
- Ability to switch back to multi from single (spit warning "can't go back").
- Ability to sort results by other dimensions
- Pass in a list of category names?
- Might need to handle different formattings of missing data coming from different sources (Q, excel, SPSS, etc), ideally seperate from people responding with things like "N/A" etc.
- ~~Need to fix 'New Project' behaviour when a project is already loaded (redisplay 'Uncategorized', remove match results)~~
- ~~Handle missing data (checkbox button to change how percentages are calculated)~~
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

- Maybe a box that always shows uncategorized (or remove current match and put them in there?)
- Tooltips (for what exactly?)
- Make buttons size properly (all the same rectangles)
- ~~Align tops and bottoms of display boxes.~~
- ~~Sort category results display first by count and second alphabetically.~~
- ~~Set initial column sizes and text wrapping and have them scale with the window size.~~
- ~~Show percentages next to category counts~~
- ~~Text wrapping (it's cuttong off 'y' to look like 'v').~~
- ~~All display boxes should stretch to the bottom of the window.~~

### Comments and documentation

### Future:

- Separate logic from UI.
- Unit tests.
- Maybe an auto mode? i.e. auto-match and categorize for each category in the list, for a pre-defined threshold.
