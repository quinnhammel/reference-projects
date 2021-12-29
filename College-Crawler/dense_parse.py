# this file will parse dense pages for names and emails. (dense means the page has actual emails, as opposed to links to emails).
from bs4 import BeautifulSoup
import shared_parse





# DESCRIPTION:
  # these parsing methods basically:
    # take in the full html and convert it to BeautifulSoup.
    # locate all emails in the page, and store the elements containing those emails.
    # for each email node, step 'back' in the tree (as in the parent element) until too many emails are contained within the node. This would indicate that we have hit the list of all emails, instead of the name/email element.
    # then, from that, get the name_node (node with email and name associated, hopefully). 
    # retrieve names for each email (using shared_parse functions).
    # return dictionary.

  # to get the output, call scrape_all_info(full_hub_soup).
  # NOTE: many of the functions used heavily in the dense parser are in the shared_parse file. This is because they are also used in the sparse parser.

# CONSTANTS: tweak these to change behavior of program. Warning: choosing invalid values will cause undefined behavior. As a whole, these values must be carefully chosen.

NAME_EMAIL_THRESHOLD = 5 #threshold for when a node is considered as containing a name vs the list


# this function takes in the list of email_nodes and returns a dictionary from email_text (the text in the email_nodes) to the name_nodes. The name node is the element (BeautifulSoup element) that we think contains the email and the name. It is what we will later search through for the name.
def get_name_nodes_dict(email_nodes: list):
  output = {}
  if not isinstance(email_nodes, list):
    return output #email_nodes was not a list.
  
  for email_node in email_nodes:
    #first, we want to get the actual email text associated with the node. We can use the helper method get_email_text_from for this.
    email_text = shared_parse.get_email_text_from(email_node)
    
    if email_text is None: 
      continue # this would indicate a bad node.

    #this part will be a bit ugly. We basically want to back track from the current email_node until we hit a parent with more than NAME_EMAIL_THRESHOLD emails (5 for now). Then, we choose the child of that node as the return value. 

    #the thinking is is that when we hit such a parent, that parent will really be the list with all the emails. When we hit such a node, we want to choose the child we just came from, as that contains a small number of emails, and a bunch of text, where the name probably is.
    
    #the reason this is messy is because we need to keep track of two nodes (bs4 elements), so we can rememer where we came from, and in case we go too far (in which case, one of the nodes becomes None).

    #so, 'added' is the node we will be adding, and 'probe' is the node we will use to probe further back in the tree.

    probe = email_node
    added = None # this will get updated in the while loop. if it does not, then that itself indicates an issue, which we will deal with later.

    # NOTE: in the below while loop, the count_emails call is inefficient. That function is recursive, so the work will be repeated. However, if this does not contain a MAJOR slowdown, it is worth it to keep this; keeping track of the number of emails as we go, and traversing through children, would be more complicated.
    
    while ((not probe is None) and (shared_parse.count_emails(probe) <= NAME_EMAIL_THRESHOLD)):
      #probe should be one layer ahead of added. since we are in the while loop, we know that probe is valid. so, we update added to probe (since we can still go further)
      added = probe
      #now, try to 'probe' back one more layer.
      try:
        probe = probe.parent
      except:
        break # this should not really happen, but it would indicate hitting a probe node without a parent, which means we are done probing back. 

    #when we get here, added should be the node right below the layer that has too many emails, which is exactly what we want. there is one exception, however: if added is none.
    if added is None:
      continue #TODO: think about how to handle this. This would only really come up in complicated nested emails, so it is probably just best to continue over it.

    #can finally add added to the dictionary, with key email_text of course.
    output[email_text] = added

  return output # return the dictionary, which has been populated with nodes.

# this function takes in the name_nodes_dict and returns a dictionary from the names to the emails.
def get_names_and_emails(name_nodes_dict: dict):
  output = {}
  if not isinstance(name_nodes_dict, dict):
    return output
  
  # iterate through the name_nodes_dict. Remember that the keys are emails and the values are the name nodes.
  for email_text, name_node in name_nodes_dict.items():
    # put the following in a try block just in case.
    try:
      all_text = name_node.find_all(text=True) # the get_name function takes in the text!
      name = shared_parse.get_name_for(all_text, email_text)
    except:
      continue # issue, probably not a BeautifulSoup element, just go onto next name.

    # only add the name to the dictionary if it is not None and it is not already in the dictionary (want to avoid duplicates).
    if (not name is None) and (not name in output):
      output[name] = email_text # maps from names to emails.
  
  return output

# the following function combines the others. It is what should be called from this file. (has twin in sparse_parse.py)
def scrape_all_info(full_hub_soup):
  output = {}
  
  # get the emails, then the name_nodes, then the names and emails.
  email_nodes = shared_parse.get_all_email_nodes(full_hub_soup)
  name_nodes_dict = get_name_nodes_dict(email_nodes)
  output = get_names_and_emails(name_nodes_dict)
  return output

