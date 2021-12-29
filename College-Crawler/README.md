# College-Crawler
A web crawler for contact information from colleges.
## Dependencies
* Python - 3.7.2
* beautifulsoup4 - 4.7.1
* fuzzywuzzy - 0.18.0
* pyppeteer - 0.0.25
* openpyxl - 3.0.3

### Licenses
* beautifulsoup4 - MIT
* fuzzywuzzy - GPLv2
* pyppeteer - MIT
* openpyxl - MIT

## Setup
First, create a properly formatted excel spreadsheet (*.xlsx) with the input (university names, department names, and links to those departments). 
The spreadsheet must have exactly one page. The first row is free to use for titles to make the input easy to understand for a user.
The computer will start reading from the second line onwards, until it encounters an empty space where there should not be one. See the following example table for the input format:
| Institution   | Department    | Link    |
|:-------------:|:-------------:|:-------:|
| Stanford      |               |         |
|               | Math          |_math link_|
| Harvard       |               |         |
|               | Biology       |_bio link_ |
|               | Physics       |_phys link_|
|               | Chemistry     |_chem link_|
| UCLA          |               |         |
|               | Economics     |_econ link_|
|               | Comp Sci      |_cs link_|

As you can see, university names appear in the leftmost column, then departments, then links. University names appear on their own line.
Assuming the input is at /Desktop/input.xlsx and the user desires the output to be at /Desktop/output.xlsx, call the program with:
**Python3 main.py /Desktop/input.xlsx /Desktop/output.xlsx**.
This will scrape the content (offering status updates through terminal) and save the content to the output spreadsheet (NOTE: this will create a new spreadsheet, or will override an existing spreadsheet with the same name!). The program will save the spreadsheet after every department scraped, so that if the program fails, most of the data will still be stored. The output has a pretty intuitive format. There is a *Master Sheet* which contains a list of departments that were successfully scraped, and ones that were not. The failed retrievals, as they are called, are listed with their urls so that if desired, one can manually scrape them, since the scraper was not able to. After the master sheet, there is a sheet for every university (that was able to be scraped). Each sheet has all the emails and names for all the departments. These will have to be checked manually at some point, because the program does make mistakes.
## Customization
Web scraping is a pretty rough-approach activity, so much of the program relies on somewhat arbitrary constants. These can be changed if the need arises. 
The constants in main.py mainly have to do with timeouts (and the excel input/output, but that is less important). The timeout constants must strike a balance between being short enough to be efficient, but not too short as to cause timeouts that require another whole attempt (which would be even slower). In addition, if the timeout is too long, the library pypepeteer can raise a NetworkError. This is handled in the program and is discussed in depth in the comments.
The constants in shared_parse.py and dense_parse.py are more straightforward and easy to understand. For DENSE_EMAILS_THRESHOLD, one might be tempted to lower the number so pages with a lower number of emails (say, 5) could be parsed. However, as the threshold gets lower, the risk of random emails (like ones for unrelated contacts on the page)
could be enough to identify the page as dense, even if it were sparse (described in next section). This would cause a large issue. Also, pay special attention to BLACKLIST and WHITELIST. Both of these lists are used for determining whether a string is a valid name. If a name has any words in BLACKLIST in it (all the words in BLACKLIST should be lowercase), it is immediately ruled to be an invalid name. If the scraper keeps hitting some phrase it thinks is a name, like "Scholar Award" for example, add the word to the blacklist. The WHITELIST is words that will not be considered as part of a name. It consists of titles and degrees. This is so a name like "John M. Smith PHD MD MA" is still considered a name, despite being too long (PHD, MD, MA would not be counted). 
The constants in sparse_parse.py are more confusing. The proportion constants were chosen to just get the job done, and not much tinkering should really be required. The real issue is the VALID_INDICATORS list. The problem is detailed in the code, but adding too many words to this (or having too few) could potentially wreck the way the parsing works. For now, however, it seems pretty stable.
If extensive customization (which would require some not-insignificant editing of code) is desired, there are a few functions with optional parameters that do not get used. These could be implemented, but they are not because it was not critical.
## Program Structure / Notes
The program is split into four files. There are two main types of faculty webpages: dense ones, and sparse ones. Dense ones are the simpler ones (with all the emails in one or two list(s)), while sparse pages are more of a pain (containing only links to a separate page with the emails). 
Both parse files use shared_parse.py, which contains common functions. Some of these functions are not terribly efficient, calling recursively too many times; however, the code is significantly easier to read and maintain with this structure, and the time lost is nothing compared to the time spent on fetching links. 
The dense parse algorithm basically looks for emails, and steps back in the html until it encounters too many emails (which would indicate a list of emails). It uses this to get a group of text that likely contains the name for the email, and finds the best match using a function from shared_parse.
The sparse parse algorithm is more confusing. Basically, it looks for pages with certain indicators present (which would *indicate* that the link is to a profile page), and requests all of them. It culls any pages that are outliers, since profile pages would likely have mostly the same HTML (this proportion can be changed via a constant). It then feeds unique text for each link to the name finding algorithm. Notably, this type of parsing is slower: the requests take time, and the program must sleep to avoid rate limiting.
The main file pulls the whole thing together, and is the most tempermental. The file contains a function for grabbing the complete html of a site by 'scrolling' to the bottom of the page, forcing a navigation if there is one. This will grab sites that have scrolling mechanisms. This uses the asynchronous library pyppeteer, and can be messy to deal with and debug. If there are no issues, changing this is not recommended for the faint of heart. Because of the flaws of the library, many measures are taken to ensure that the program does not time out during this part.
Also, the file contains the input and output functions (reading from/writing to excel), which are messy, but get the job done.

Overall, this webscraper operates on a pretty simple principle: if an Exception or something unexpected is encountered, just keep going on to the next name, the next department, and the next link. This scraper will not work for everything but it should keep itself from shutting down from a simple Exception, so it will still retrieve as much data as possible. In keeping with this, the program will save the output file repeatedly--so in the case of an accidental crash, the output is kept. 

