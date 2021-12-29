# this file is for the parsing of a sparse page (one with links instead of direct emails.)
# this is a first attempt. In the future, it will need to be merged with the other parser, along with some other stuff that decides which parser to implement.
import time as time_  # for sleeping.
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

import shared_parse

# DESCRIPTION:
  # these parsing methods basically: 
    # find all the links, and narrow down which ones are likely profiles.
    # grab the soup and all text for these links, being careful of rate limiting.
    # cull out links that are exceptions (profile pages should contain most of the html).
    # separate out the text that is unique for each page.
    # find the least common email on each page (ie an email on one page that appears in the least number of others)
    # get the name matching the email from the unique text for each page (use method from shared_parse for this)
    # return the dictionary of all names to emails.

  # to get the output, call scrape_all_info(hub_link: str, full_hub_soup).


# CONSTANTS: tweak these to change behavior of program. Warning: choosing invalid values will cause undefined behavior. As a whole, these values must be carefully chosen.

DEFAULT_COMMON_THRESHOLD = 0.80 # a piece of text must appear in 80% of other pages for it to be considered 'common'.

DEFAULT_PROPORTION_ERROR_TOLERANCE = 0.05 # the tolerance for how much a proportion must be within the average proportion (for culling links).

DEFAULT_WAIT_TIME = 0.5 # time in seconds to begin waiting between requests to get the pages.

DEFAULT_MAX_TRIES = 10 # number of times to try the request before giving up (each try, wait time gets increased.)

VALID_LINK_INDICATORS = ["profile", "person", "people", "staff", "faculty"] # these should be lower case. These are the indicators that a link should be considered as a possible profile page.
# NOTE: adding words to this will increase the number of sites that can be scraped, but will cause slowdowns. If you add too many words, the program might break. If you add too few, you might get less pages. For now, this list seems to work well. If there are issues, try removing staff and faculty.


# want a namedtuple for SoupText, which will contain soup and all_text.
SoupText = namedtuple("SoupText", ["soup", "all_text"])

# first, from a soup element, we want to get all links on the page (that conform to certain standards)
# the standard is that some word from VALID_LINK_INDICATORS is found in the link (and that it is a link, of course).
# see notes near VALID_LINK_INDICATORS definition.
# input is the element, and possible_links: a dictionary from strs (the individual indicators) to sets containing the links that match with those indicators.
def get_all_links(element, possible_links: dict):
  # possible_links is a dictionary from strs (VALID_LINK_INDICATORS) to sets. We add a link to the corresponding set if it contains that indicator. we do this recursively.

  # check if a link in the element can be added to one of the sets.
  try:
    link = element.attrs["href"]
    lower_link = link.lower() # indicators will be lower case, so we compare the lower case.
    for indicator, link_set in possible_links.items():
      if indicator in lower_link:
        link_set.add(link)
  except:
    pass # could not add the link (probably was no such link).


  # we now call recursively to all the links to children. (we 'try' this, since there may not be children!)
  try:
    for child in element.children:
      get_all_links(child, possible_links)
  except:
    pass

# this function will clean the links in the link set once we get it.
# namely, it will append the hub_link to the beginning if the link is just a relative path.
def clean_links(hub_link: str, links: set):
  output = set()
  if not isinstance(hub_link, str):
    return output
  if not isinstance(links, set):
    return output

  for link in links:
    # the link should have length at least 1, but we use a try block just in case.
    try:
      c = link[0]
      added = ""
      
      if c == '/':
        # IMPORTANT: we cannot just append the link to the hub link. Sometimes, sites will repeat parts of it. So, we have to split the link by '/'
        link_split = []
        for word in link.split('/'):
          # we do not want to add words included in hublink. 
          # HOWEVER, the first str will be "" (since it starts with a '/' before we split it). We still want this to be there, even though the empty string is trivially in every str. 
          # so, we add the word if it is the empty str or if it is NOT in hub_link.
          if (word == "") or not(word in hub_link):
            link_split.append(word)

        link = '/'.join(link_split)
        added = hub_link + link
      elif c == '.':
        added = hub_link + link[1:]
      else:
        added = link
    
      output.add(added)
    except:
      continue # empty link, or not str.
  
  return output



# the following function is what gets the links_soup_text, which is a dictionary from the links to the SoupText elements (which consist of the BeautifulSoup objects and all the text from those soups)
# this requires some rough-guesswork about if the program will get rate limitted for making too many requests.
# NOTE: these optional parameters do not link up to anything. But, you can change them for increased customizability, if needed. 
def get_links_soup_text(hub_link: str, full_hub_soup, wait_time=DEFAULT_WAIT_TIME, max_tries=DEFAULT_MAX_TRIES):
  # first, we verify the types
  try:
    wait_time = float(wait_time)
    if wait_time < 0:
      raise Exception # to get inside the except block.
  except:
    wait_time = DEFAULT_WAIT_TIME
  
  try:
    max_tries = int(max_tries)
    if max_tries <= 0: # (we should want to try at least once)
      raise Exception # to get inside except block 
  except:
    max_tries = DEFAULT_MAX_TRIES

  output = {}
  if not isinstance(hub_link, str):
    return output

  # we now want to get all of the links on this page, using the indicators. We then take the group with the most links.
  # initialize the dictionary...
  possible_links = {}
  for indicator in VALID_LINK_INDICATORS:
    possible_links[indicator] = set()
  
  get_all_links(full_hub_soup, possible_links)
  most_links = None
  best_links_indicator = ""
  for indicator, links_set in possible_links.items():
    if (most_links is None) or (len(links_set) > most_links):
      most_links = len(links_set)
      best_links_indicator = indicator

  if most_links is None:
    return output # this should not happen!

  links = clean_links(hub_link, possible_links[best_links_indicator]) # this function should deal with obnoxious link formatting issues.
    
  count = 1
  for link in links:
    print(f"  Fetching profile link ({count}/{len(links)})...")
    response = None
    successful_response = False # used for determining when we get a successful request...
    for attempt_num in range(1, max_tries + 1):
      # we sleep before we request, so we can avoid getting too many requests errors.
      time_.sleep(wait_time * attempt_num)
      try:
        response = requests.get(link)
      except:
        print("   Could not get response!")
        break # an exception here indicates that the link does not work, which means we should not attempt it further

      # we now check the status code.
      if (200 <= response.status_code) and (response.status_code < 300):
        successful_response = True # we did it!
        break # this would indicate a successful get request.
      elif response.status_code == 429:
        continue # this is the status code for too many requests, which would indicate that we need to wait longer.
      elif response.status_code == 404:
        break # a 404 error code indicates that we should stop trying.
      else:
        # some other status code that was not expected. We will still try again, but we should print it out.
        print(f"    When retrieving individual link content, encountered unexpected status code: {response.status_code} on attempt ({attempt_num}/{max_tries}).")
        continue

    # we can now grab the soup of the content if we were successful... (in a try/except block, of course.)
    if successful_response:
      try:
        soup = BeautifulSoup(response.content, "html.parser")
        all_text = soup.find_all(text=True)
      except:
        continue # something went wrong, just try the next link.
    
    output[link] = SoupText(soup, all_text)
    count += 1

  return output
      


# the following function returns the text that is common to most of the pages. It takes in a dictionary (from links) to SoupText elements (namedtuple defined above). It also takes in an optional common_thresh, which defaults to DEFAULT_COMMON_THRESHOLD (given above)
# the function will return a list of all 'common' text. Text is considered common if it appears in at least common_thresh (percentage) of all the links in the dictionary. Otherwise, it is not.
# again, the optional parameter is not used, but it can be implemented for extra customizabilitiby. 
def get_common_text(links_soup_text: dict, common_thresh=DEFAULT_COMMON_THRESHOLD):
  output = []
  if not isinstance(links_soup_text, dict):
    return output
  
  # verify that common_thresh is a valid float.
  try:
    common_thresh = float(common_thresh)
    if (common_thresh <= 0.0) or (common_thresh >= 1.0):
      raise Exception # do this to get in except block
  except:
    common_thresh = DEFAULT_COMMON_THRESHOLD

  # first, we need to keep track of the occurrences of all text in all links.
  text_occurrences = {} # a dictionary from str (text) to ints (number of occurrences).
  for link, soup_text in links_soup_text.items():
    for text in soup_text.all_text:
      if text in text_occurrences:
        continue # we have already counted this text, so no need to count it again.

      count = sum(
        1 if text in other_soup_text.all_text else 0 
        for _, other_soup_text in links_soup_text.items()
      ) # this will sum up the count of the text.

      # place the count in the dictionary
      text_occurrences[text] = count

  # we now go through all the text in the dictionary to see if they occurr enough to be placed in the output.
  for text, occurrences in text_occurrences.items():
    if occurrences/(len(links_soup_text)) >= common_thresh:
      output.append(text) # it occurs enough to consider it common.

  return output


# the following function will 'cull' the links that are fed in. It takes in links_soup_text, a dictionary from links to SoupText namedtuples. It also takes in common_text, a list of common text already fetched. Finally, it takes in prop_error_tol, which defaults to DEFAULT_PROPORTION_ERROR_TOLERANCE.
# the function returns False if no culling was done (ie no elements deleted) and True if some links were culled.
# again, the optional parameter is not used, but it can be implemented for extra customizabilitiby. 
def cull_links(links_soup_text: dict, common_text: list, prop_error_tol=DEFAULT_PROPORTION_ERROR_TOLERANCE):
  # first, we must verify the types of all the input.
  if not isinstance(links_soup_text, dict):
    return False
  if not isinstance(common_text, list):
    return False
    
  try:
    prop_error_tol = float(prop_error_tol)
    if (prop_error_tol <= 0.0) or (prop_error_tol >= 1.0):
      raise Exception # do this to get inside except block.
  except:
    prop_error_tol = DEFAULT_PROPORTION_ERROR_TOLERANCE

  if len(links_soup_text) == 0:
    return False # do this to avoid a division by 0 later.
  
  # we want to store a dictionary from links (the keys in links_soup_text) to proportions. The proportion for a link is the proportion of its text that is in the common_text. 
  link_proportions = {}
  # we also want to keep track of the average proportion while we calculate these proportions.
  avg_proportion = 0.0
  for link, soup_text in links_soup_text.items():
    count_common = sum(1 if text in common_text else 0 for text in soup_text.all_text)
    try:
      proportion = count_common / (len(soup_text.all_text) + 0.0) # the proportion is the words in common divided by the total words.
    except:
      continue # in case there is a page with no text for some reason, causing a divide by 0 error.

    link_proportions[link] = proportion
    avg_proportion += proportion

  avg_proportion /= len(links_soup_text)

  # we now cull the links (possibly) and keep track if we culled any.
  have_culled_any = False
  for link, proportion in link_proportions.items():
    # if more common than avg, we do not cull.
    if proportion >= avg_proportion:
      continue

    # we know that proportion is less than avg_proportion. It must be within prop_error_tol of the avg_proportion. Otherwise, we cull it!
    if (abs(proportion - avg_proportion)/avg_proportion) >= prop_error_tol:
      # uhoh, we have to cull this link!
      have_culled_any = True
      del links_soup_text[link]
  
  # return whether we have culled any.
  return have_culled_any

# the following function returns a dictionary from the links to the best emails in that page's soup. culled_LST is the links_soup_text that should have been culled before using this function.
def get_emails_dict(culled_LST: dict):
  output = {}
  if not isinstance(culled_LST, dict):
    return output
  
  # we want to grab the email for each link.
  # however, there will very likely be multiple emails on each individual page.
  # the way to deal with this is to choose the email that occurs the least in other pages (pages are in culled_LST).
  # to do this, we first need to get a dictionary from the email's to the number of times they occur.

  #NOTE: we use methods defined in shared_parse.py to find the emails and text, since we need to traverse through the soup instead of just the text!
  email_occurrences = {}
  for link, soup_text in culled_LST.items():
    for email_node in shared_parse.get_all_email_nodes(soup_text.soup):
      email_text = shared_parse.get_email_text_from(email_node)
      if email_text is None:
        continue # in case something goes wrong...

      if email_text in email_occurrences:
        email_occurrences[email_text] += 1
      else:
        email_occurrences[email_text] = 1

  # now, we can begin to look through link by link. For each link, we want to choose the email in that page with the lowest number of occurrences (indicating that it is in the least other pages!)
  for link, soup_text in culled_LST.items():
    best_email = ""
    min_occurrences = None
    for email_node in shared_parse.get_all_email_nodes(soup_text.soup):
      email_text = shared_parse.get_email_text_from(email_node)
      if email_text is None:
        continue # in case something goes wrong...

      try:
        num_occurrences = email_occurrences[email_text]
      except:
        continue # just in case of a key exception, which really should not happen.

      if (min_occurrences is None) or (num_occurrences < min_occurrences):
        min_occurrences = num_occurrences
        best_email = email_text
      
    if shared_parse.is_email(best_email):
      output[link] = best_email # this if is a final safety check to make sure that we only get emails!
    
  return output

# the following returns a dictionary from links (str) to a list of unique text (navigable string). Unique text is text in that url that is not in common_text. again, culled_LST should already have been culled.
def get_unique_text_dict(culled_LST: dict, common_text: list):
  output = {}
  if not isinstance(culled_LST, dict):
    return output
  if not isinstance(common_text, list):
    return output

  for link, soup_text in culled_LST.items():
    uq_text = []
    for text in soup_text.all_text:
      if not (text in common_text):
        uq_text.append(text)
      
    output[link] = uq_text

  return output


# the following will return the names and emails dictionary from culled_LST. This is the main meat of the scrape_all_info function later. again, culled_LST should already have been culled.
def get_names_and_emails(culled_LST: dict, common_text: list):
  output = {}
  if not isinstance(culled_LST, dict):
    return output
  if not isinstance(common_text, list):
    return output

  emails = get_emails_dict(culled_LST)
  uq_text = get_unique_text_dict(culled_LST, common_text)

  # the name should be contained in the unique text associated with each link, which is associated with an email.
  
  for link, soup_text in culled_LST.items():
    try:
      email = emails[link]
      name = shared_parse.get_name_for(uq_text[link], email)
    except:
      continue # in case something wrong occurred earlier.

    if not (name is None):
      output[name] = email # only want to store valid names.

  return output




# the following function just combines all other functions. It takes in the full soup of the site and returns a dictionary from names to emails.
def scrape_all_info(hub_link: str, full_hub_soup):
  output = {}
  if not isinstance(hub_link, str):
    return output

  links_soup_text = get_links_soup_text(hub_link, full_hub_soup)
  common_text = get_common_text(links_soup_text)
  if cull_links(links_soup_text, common_text):
    # since we did cull some links, we need to recalculate the common_text
    common_text = get_common_text(links_soup_text)

  output = get_names_and_emails(links_soup_text, common_text)
  return output

