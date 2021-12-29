from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz # for name comparisons.


# DESCRIPTION:
  # this file contains basic functions and constants that will be used by both dense_parse and sparse_parse. 

# CONSTANTS: tweak these to change behavior of program. Warning: choosing invalid values will cause undefined behavior. As a whole, these values must be carefully chosen.

MIN_NAME_LENGTH = 2 # min word length of a string to be considered a name
MAX_NAME_LENGTH = 4 # similar.

WHITELIST = ["dr", "phd", "md", "ma", "ms", "mr", "mrs", "ba", "bs"] # words that ARE allowed in names (will not be accounted for in the name check, will instead be removed). 

BLACKLIST = ["prof", "scholar", "student", "theory", "univ", "coll", "department", "office", "phone", "email", "number", "no.", "contact", "site", "page"] # blacklist for names. Add lower case words ONLY to this. If a name contains this string, it is no longer considered as a name.


# the following is what determines whether a given string is an email.
def is_email(word: str):
  # if word is not a str, immediately return false.
  if not isinstance(word, str):
    return False

  # check for an @ symbol, and one of the common endings in emails (.edu, .com, etc.)
  return (('@' in word) and (".edu" in word or ".org" in word or ".com" in word or ".net" in word or ".us" in word))

# this extracts the email text from a node (which is a BeautifulSoup element)
def get_email_text_from(email_node):
  #first, we check that this node contains an email. If not, we just return None
  if not contains_email(email_node):
    return None
  
  try:
    email_text = email_node.text
    #this email text is probably just one word (the email), but we have to check if it is not.
    email_text = email_text.split()
  except:
    return None #this indicates that this is not a valid BeautifulSoup element, which means we should just return None.

  #for the following, we use the fact that we already checked if this node contained an email. So, we know that it will contain an email in one of the words. 
  if len(email_text) == 1:
    #the list has length 1, so we just return the word (which again, as noted, will be the email)
    return email_text[0]
  else:
    #there are multiple words (cannot be no words since we already checked if this contained an email)
    for word in email_text:
      if is_email(word):
        return word #the helper method indicates this is an actual email address.
    
  return None #we should never get here, but if we did, it would indicate an invalid email node somehow

# this returns true if there is an email in the element, false otherwise.
def contains_email(element):
  #this will check if the element contains an email, and will return True if it does, false otherwise.
  # will only check for clickable emails. This is because it is otherwise pretty difficult to distinguish an email from the html (@ is used frequently, but "mailto:" is not)
  try:
    href = element.attrs["href"]
    text = ''.join(element.text.split())
    
    #we want the email to be clickable (indicated by "mailto" being in href) and we want the href and text to have emails (use helper method).
    return (("mailto:" in href) and is_email(href) and is_email(text))
  except:
    pass # this would indicate that element was not an element from beautiful soup (most likely None)

  return False #default is that it does not contain an email.

# this recursively counts the number of emails in an element and its children. NOTE: this is somewhat inefficient, as extra calls are made. However, it simplifies the code to do it this way.
def count_emails(element):
  #this will recursively count the number of emails contained in element and all children of element.
  # for the following line, note that the contains_email method is Exception safe, and returns True if an email is contained, false otherwise.
  output = int(contains_email(element)) # this is 1 or 0, depending on whether an email was contained.

  #we try to go through the children of element and add their email counts to the output
  try:
    output += sum(count_emails(child) for child in element.children) 
  except:
    pass #no children, either have reached the end, or the element was not of the correct type.

  return output

# this method returns whether an element is in the footer. This is so we do not include elements in the footer as valid emails.
def is_in_footer(element):
  #we do not want to store emails found in the footer, as they will not be associated with a professor.
  #not sure that the element will have an id.
  try:
    id = element.attrs["id"]
    if ("footer" in id):
      return True # this was in the footer.
  except:
    pass # this will either trigger an exception later, or not. So, no action is needed.
  
  #we now recursively call this method on the parent. We put it in a try block, in case there is no parent.
  try:
    return is_in_footer(element.parent)
  except:
    pass # indicates no Parent, which means we have reached the end of checking.
  
  return False # if we get here, we reached an element without a parent, which means that the original was not in the footer. 

#NOTE: the following method should NOT get called directly!
def _get_email_nodes_recurs(element, output: list):
  #this will recursively add all subnodes that contain one email in themselves.
  #this is a naive approach and can greatly be improved. It will result in lots of unecessary calls.
  #NOTE: this will be weird for nested emails. For now, we add an element with an email with children with emails. These get dealt with later in get_name_nodes_dict (dense parser). 
  
  count = count_emails(element)
  if (contains_email(element)):
    output.append(element) #this specific element contains an email in that layer.
    #since the count will include this email we have found, we subtract 1, so we only enter children if there are more emails than just the one in this element.
    count -= 1
  
  if (count > 0):
    #we now know that we need to go through the children of this element.
    #we know that there will be children because there is an email in one of them, so no need for a try/except block.
    for child in element.children:
      _get_email_nodes_recurs(child, output) #this will append to the same output parameter

# this gets all the email nodes, calling the above function. This is where the inefficiency from using count_emails comes into play. 
def get_all_email_nodes(soup):
  # this method takes in the whole soup parameter.
  output = []
  _get_email_nodes_recurs(soup, output) # this gets all the actual nodes.

  #Now, for the cleaning. We want to remove email nodes that are in the footer
  #TODO: there is a better way to do this, checking if the node is the footer, then not continuing it in the get_email_nodes_recurs method.
  #since the method to get all the email nodes is depth first, all the nodes in the footer will be at the end of the list. So, we can do this.
  while ((len(output) > 1) and is_in_footer(output[-1])):
    output.pop() # remove the last element.

  return output

# brute / simple check for names. the possible name must be a str, of proper length, contain the right characters, etc.
# also, the items in BLACKLIST cannot appear in the name. 
# NOTE: if there is some case that the program repeatedly messes up, add that word to the blacklist.
def prelim_check_name(poss_name: str):
  # we are going to be using a lot of str specific functions, so just get type checking out of the way.
  try:
    poss_name = str(poss_name)
  except:
    return False # indicates not a str or NavigableString

  # trim the string. While we do this, we can check the other case: name length must be between two to four words. (these are stored as MIN_NAME_LENGTH and MAX_NAME_LENGTH at the top of this program)
  poss_name = poss_name.split()
  # however, we need to not count whitelisted words! (do not want someone with a bunch of titles after their name to have too 'long' a name...)
  poss_name = [word for word in poss_name if not(word.lower().replace('.','') in WHITELIST)]# replace dots since they will be in titles, eg M.D.
  
  if (len(poss_name) < MIN_NAME_LENGTH) or (len(poss_name) > MAX_NAME_LENGTH):
    return False

  poss_name = ' '.join(poss_name)

  # next simplest scenario is if the poss_name does not consist of letters. First, we temporarily remove spaces, '.', '-', and ',' (these could all be included in names. ',' would be when the names are reversed)
  if not poss_name.replace(' ','').replace('.','').replace('-','').replace(',','').isalpha():
    return False

  # the next step is where this algorithm gets inprecise. We just check for words that we want to ignore. Some of them are obvious, some less obvious. 
  # TODO: to tweak this, add or modify words in BLACKLIST defined above all functions.
  
  # first we change poss_name to lower case to make checking easier.
  poss_name = poss_name.lower()
  for word in BLACKLIST:
    if word in poss_name:
      return False # prohibited word found!
  
  return True # passed preliminary check.
  
# this looks through the a list of text to find (possibly) the name that matches best to the email.
def get_name_for(all_text: list, email_text: str):
  #email_text really should be an email str.
  if not is_email(email_text):
    return None

  # all_text should be a list of all text elements (possibly str or NavigableStrings.)
  if not isinstance(all_text, list):
    return None
  
  considered_names = []
  

  # we now go through all the nodes in considered node and maybe add the text to poss_names.
  for text in all_text:
    try:
      text = str(text)
    except:
      continue # if this does not work, keep on trying.
    
    # NOTE: the text will get split and formatted in the preliminary check. So, we avoid splitting the actual text until we know it passes the test.
    if prelim_check_name(text):
      considered_names.append(' '.join(text.split()))

  # at this point, we want to return the best of the considered_names. However, there are two special cases before we prepare to compare how close each considered name is to the email text.
  if len(considered_names) == 0:
    return None # there was no name found
  elif len(considered_names) == 1:
    return considered_names[0] # there was only one name found.

  # before we start weighing names, we need to extract the text we want to compare the names to.
  # we want the alpha text from the email, coming before the @ symbol. We also make it lower case.
  email_alpha_text = ""
  try:
    for letter in email_text[0: email_text.index('@')]:
      if letter.isalpha():
        email_alpha_text += letter
  except:
    pass # this would happen if there is no '@' in the str, which really should not happen.

  email_alpha_text = email_alpha_text.lower()

  # SPECIAL EXCEPTION: if the email alpha text is the empty string at this point, something has gone wrong! that means that there is no letters in the email. Since there are multiple names, we just return None in this case.
  if email_alpha_text == "":
    return None

  # we can now begin comparing
  # store the best weight and best name. best weight starts as 0, because that is the minimum matching score (100 is max).
  best_weight = 0
  best_name = None

  for name in considered_names:
    # want lname to be lower case to compare to email_alpha_text
    lname = name.lower()
    weight = (fuzz.partial_ratio(email_alpha_text, lname) + fuzz.token_sort_ratio(email_alpha_text, lname))/2 # first does partial strings, second does out of order strings (in case last, first).
    if weight > best_weight:
      best_weight = weight
      best_name = name # want the original name, not the lower case one.

  return best_name

