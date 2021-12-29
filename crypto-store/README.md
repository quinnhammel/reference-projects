(Note: some commits erroneously list "Ubuntu" as the author. These were actually committed by quinnhammel `<quinnhammel@gmail.com>`)
# **crypto-store**
This is the backend and infrastructure for a shopify store that accepts payment through crypto. It is advised to read through this whole document before attempting to work with the store. But in summary you will need to use an email address, zinc API, coinbase commerce API, shopify API, and AWS. The actual code executed is in `src/shopify_order_processing.py` (see [**Shopify: Basic Shopify Backend**](#basic-shopify-backend)).

## **Logging**
Since this is an actual store, logging of orders is critical. These local records are not the *only* records; records can be found in shopify, zinc, coinbase, and the processing email account (see [**Email: Order Flow**](#order-flow)). The main benefit for keeping a physical record is speed. The other records all require API calls and requests. This means that using those records exclusively results in unreasonable execution times. 
The file responsible for logging is `src/logger.py` which contains the single class `Logger`. This is in some senses a pseudo-class as all the methods are static. It is kept in a class for organization (there are too many free floating methods already). 
The `Logger` class keeps records in two ways: text files and json files. 
### **Text Logging**
The text logging is more for testing, and is not required for the actual order flow; the philosophy of the text logging is to never overwrite a file and always just append to it. Call `Logger.log_txt_file(tx_code: str, text: str, newlines=1)` to log to a text file (more on tx_code [**later**](#transaction-codes)). The parameter `newlines` is the number of new lines (*'\n'*) to append onto the text file before adding the new text. The directory path for text logs is a class variable `Logger.TEXT_TX_REC_PATH` which you can set near the top of the class (currently it uses `REPO_PATH` from `src/const.py`; see [**Constants**](#constants)). 
### **Json Logging**
The json logging is what actually logs records for orders placed through the store. The directory path for json logs is a class variable `Logger.JSON_ORDER_PATH` which you can set (currently it uses `REPO_PATH` from `src/const.py`; see [**Constants**](#constants)). To read an existing record call `Logger.read_json(order_num: str)` which returns a dict object; if the record is not found it returns `{}`. To write to a json file call `Logger.write_json(order_num: str, data: dict)`. Inside of this method, `read_json` is called to ensure no data is deleted. The method reads a json file (if it exists), and then adds all the new key/val pairs from data. This way no data is ever eliminated from a record (althought it *can* be overwritten). 
### **Logging Path Generation**
The paths for actual log files are generated using the static methods `Logger.gen_json_path(order_num: str)` and `Logger.gen_tx_rec_path(tx_code: str)`. These use the class variables `Logger.TEXT_TX_REC_PATH` and `Logger.JSON_ORDER_PATH` mentioned earlier. These methods should really not need to be edited or called manually (all path work is done internally in other `Logger` methods). 
### **Transaction Codes**
A transaction code, or tx_code for short, is a 16 character string generated from a hash (sha256) function (seed is current time in epoch format). The main use of these codes is as idempotency keys for the zinc api. This prevents an order from erroneously being resubmitted multiple times. To generate one call the static method `Logger.gen_tx_code()`. This should be done sparingly. Currently it is only done in `src/shopify_order_processing.py` when an order is entered into the zinc system. After that, the code is logged, and used from the record (i.e. not re-generated). In summary: only generate these when you are sure you need to, and when generating make **absolutely** sure the code is recorded. 
**Note:** currently there is no check for overlapping transaction codes, i.e. a new transaction code could be one that has already been used. This is very implementation specific, but you may want to change this.

## **Email**
### **Order Flow**
When a new order is submitted on shopify, an email will automatically be sent to a specified email address (set the address and password in AWS's Secrets Manager; see [**AWS: Credentials**](#credentials); this address is referred to as the "processing email account" throughout this document). The state of the order is kept track based on what mailbox the email is moved to, within the processing email account. The actual flow is complex and detailed extensively in `src/shopify_order_processing.py`. There are two main principles to keep in mind: keeping the inbox empty and never fully deleting an email. Every cycle of the backend the inbox is purged and emails are moved to the appropriate places. Before the purging, however, **all** emails are copied to the box *"all email history"*. **NEVER DELETE ANY MESSAGE FROM THIS MAILBOX**. As a failsafe to ensure nothing is deleted from this box, the method for moving emails (see [**Email: Emailer**](#emailer)) does not allow mail to be deleted from the *"all email history"* box. 
One other important thing to keep in mind on the shopify end: originally, the email sent from shopify for a new order has a subject of the form *Order #123456...*. This must be changed to *Orderx #123456...* in the templates on shopify. This is because searching for a literal '#' in email subjects causes unreliable behavior. See step 5 of [**Shopify: Setting up the Store**](#setting-up-the-store).
### **Error Emails**
Since the system is fairly unstable, if a critical error occurs (mostly on the zinc side) an email will be sent to a specified email address with the order number, saying to manually fix the order. To specify this email, set the address in AWS's Secrets Manager; see [**AWS: Credentials**](#credentials). 
### **Emailer**
The actual processing of emails is handled in the `Emailer` class, in `crypto-store/src/emailer.py`. An instance of `Emailer` can 
* read emails
* move emails between mailboxes
* send emails
from the order processing email account specified in AWS's Secrets Manager. The address is fetched using the `CredsManager` (in file `src/secrets.py`) class in the `get_testing_name_pw()` method at the top of the file. See [**secrets: CredsManager**](#credsmanager).
`Emailer` is an actual class that must be instantiated (as opposed to a pseudo-class). This is because an instance of `Emailer` keeps an `imaplib.IMAP4_SSL` instance as `self.__read_server` (for reading and moving emails between mailboxes) and a `smtplib.SMTP_SSL` instance as `self.__send_server` (for sending emails). These both take significant amounts of time to instantiate and log in, so it is best to do it as little as possible by using an instance of `Emailer`. 
#### **Intended Usage**
There are three `Emailer` methods that should be enough for all intended usage. 
1. `Emailer.fetch_all_emails(self, mb: str)`. This is the simplest method. It returns a list of `email.message.EmailMessage` objects from a single mailbox `mb` (returns all emails in that mailbox). This method can raise exceptions if the mailbox cannot be selected (usually indicates it does not exist) or if the fetch call fails (less straight forward error). This method uses `self.__read_server` to read the emails. In the beginning of this method, `self._open_read()` is called to open the read server in case it is closed (see this method [**later**](#other-usage)). 
2. `Emailer.send_email(self, to: str, subj: str, body: str, attached=None, force_attach=False)`. This is the method for sending an email. The parameter `to` should be an email address as a string (for multiple recipients, separate them by a ',' in the string; e.g. "bob​@gmail.com,cindy@gmail.com"). The parameters `subj` and `body` are the subject and body, fairly self explanatory with one thing to keep in mind: if emails seem not to be appearing in the recipient's mailbox, play around with the subject and body. If these are short they can get flagged as spam. For example, using "hi there" as a subject would trigger the spam filter. The parameter `attached` should be None or a path to a file to be attached, as a string. This is intimately related to `force_attach`. If `force_attach` is False, then the method will ignore an attachment that fails. So if the path does not exist, or the attachment fails for some other reason, it will just send the email without an attachment. If `force_attach` is True then a failed attachment will raise an Exception. After verification of parameters, an email is sent. This uses `self.__send_server` to send the email. In the beginning, `self._open_send()` is called to open the send server in case it is closed (see this method [**later**](#other-usage)).
3. `Emailer.move_emails(self, from_mb: str, to_mb: str, white_list: list, black_list: list, delete=False)`. This is the most complex method and is used to manage where order emails are located (i.e. in what mailboxes). This method returns the number of emails moved (-1 if a basic issue). This method also raises Exceptions. The parameters `from_mb` and `to_mb` are the mailboxes to move emails from and to. The parameters `white_list` and `black_list` are how emails are selected to be moved. These should be lists, but if a string is provided it will turn this into a list containing only that string (in case the list is only one element). At least one of `white_list` or `black_list` must be an empty list (`[]`). If they are both non-empty lists, an Exception is raised. If a white list is provided, every email in `from_mb` that has a subject containing **any** string in `white_list` as a substring is moved to `to_mb`. If a black list is provided, every email in `from_mb` that has a subject not containing **any** string in `black_list` as a substring is moved to `to_mb`. Finally the `delete` parameter. When `delete` is False, emails that are moved are not deleted, so that they are now in `to_mb` *and* in `from_mb`, essentially copying the emails to another mailbox. If `delete` is True, then the emails *are* deleted, so that they will only be in `to_mb`; they are deleted after they are moved, so if there is an issue moving to `to_mb` no emails should be deleted. As detailed earlier, there is a failsafe. If `from_mb` is *"all email history"*, then delete is forced to be False. This ensures there is always a record of orders (which are moved to *"all email history"* at the beginning of processing. 

**Examples** of basic usage. In most cases, there will be a separate method that takes in an `Emailer` instance as a parameter (most such methods are in `src/shopify_order_processing.py`; see [**Shopify: Shopify Order Processing**](#shopify-order-processing)). For example consider a basic method that sends an error email: 
```python
def send_error(emailer: Emailer):
	to = "bob@gmail.com"
	subj = "Uh Oh"
	body = "There has been a terrible error!"
	emailer.send_email(to, subj, body)
```
The above requires an instance of `Emailer` be provided. Outside of the method, there are three ways to do this. First:
```python
def main():
	with Emailer() as e:
  		send_error(e)
```
This first way is best practice. The `with` context manager ensures server connections are closed neatly (using `Emailer.__enter__` and `Emailer.__exit__`). The second way is to close connections manually:
```python
def main():
	e = Emailer()
	send_error(e)
	e._close_both()
 ```
This is less preferable. This does exactly what the `with` statement does, but is less organized and more liable to cause issues (in general underscore methods of `Emailer` should not be used, see [**Email: Emailer: Other Usage**](#other-usage)) The third way:
```python
def main():
	e = Emailer()
	send_error(e)
```
This is the least preferable. The garbage collection (which deletes `e` eventually) should call `e._close_both()` in the `Emailer.__del__` method, but more things can go wrong. It is not advised to rely on the `__del__` behavior as garbage collection is complex. **Never** rely on this on purpose; the `Emailer.__del__` method is implemented exclusively in case of human error. 

#### **Other Usage**
All the other methods of `Emailer` should not be necessary to call manually. These mostly have to do with opening and closing the server instances (`self.__read_server` and `self.__send_server`). There are a few basic principles these employ:
* If a server is ever closed, the instance variable will be set to None. This allows for easy checking if a server is opened or closed. 
* In a method where a server is required (e.g. `self.__read_server` for `Emailer.fetch_all_emails(self, ...)`) the class checks if that server is open, and if it is not, opens it. This checking and opening is done in `Emailer._open_read(self)`, `Emailer._open_send(self)`, `Emailer._open_both(self)`. There are other methods for checking if a server is open, but the actual methods to open them double check internally to avoid uneccessarily opening a connection. 
* Whenever the class instance is done with, both server connections must be closed. (There are similar methods to the *`_open`* ones for closing. These also check if a server connection is already closed before closing it.) This means that `Emailer._close_both(self)` is called when a `with` statement is exited, or the class is garbage collected (see above in **Intended Usage**). 
Most of the underscore methods (starting with an underscore) are *technically* safe to call. However, using a `with` statement takes care of all of this, and is much more organized. 

## **Shopify**
This project is fundamentally the backend to a shopify store, so a large portion of it has to do with shopify. There are two main files--`shopify.py` and `shopify_order_processing.py`--that will be discussed, as well as how to set up a shopify store. **Be warned**: the shopify API has spotty documentation. There is lots of it, but often times for specific issues the answer will lie on some hidden message board, not in the documentation. The API often returns opaque "bad request" errors which are not helpful. Good luck.
### **Setting up the Store**
This will detail the setup of a shopify store as it pertains to this project, but not the setup in general.
1. **Enable API access**. Using [this link](https://help.shopify.com/en/manual/apps/private-apps), set up a private app for your store. First enable private app development. Again using Then create a private app and generate credentials for said app. Add these credentials into AWS (see [**AWS: Credentials**](#credentials)). You want both the *api_key* and *api_secret* (labelled as *api_key* and *password* respectively under the private app section). 
2. **Assign API scopes**. Again use [this link](https://help.shopify.com/en/manual/apps/private-apps). This project will need read and write access for orders (Access scopes: *"read_orders"*, *"write_orders"*). If you wish to play around with fulfillment (not yet implemented, see [**What to do Next**](#what-to-do-next)) you will need scopes *"read_assigned_fulfillment_orders"*, *"write_assigned_fulfillment_orders"*. Save the changes after enabling these scopes (you should not need to click "Allow this app to access your storefront data using the Storefront API" near the bottom). 
3. **Attach Coinbase Commerce**. Follow [this link](https://commerce.coinbase.com/integrate/shopify) to attach coinbase commerce to accept crypto payments. See [**Coinbase Commerce**](#coinbase-commerce) for more info on the backend for accepting payments. If you want to use a different service (namely BitPay) this will obviously be different. You may want to disable most other credit cards, paypal, Amazon pay, and Shop pay under payment settings. 
4. **Add Amazon products**. This one should be pretty easy to figure out using the normal Shopify store manager. There are a few caveats to this. 
    * Choose Amazon products that are simple, preferably ones with a single supplier and that are unlikely to go out of stock. 
    * When adding a product, you must specify a SKU (stock-keeping unit); this is a code for keeping track of products. This code should be unique and map back to the Amazon product code for each good. To find the Amazon product code for a url, call `get_amzn_prod_code(url: str)` from the file `src/zinc.py` (see [**Zinc**](#zinc) for more info on zinc backend). Next you must record the mapping between the SKU you chose and the actual product code. This is done in the json file `crypto-store/data/products.json`. Simply add a key value pair to the dict with the SKU as the key and the product code as the value. Both should be strings. For example you might add the pair `"123456": "B071JM699B"`. **Note**: the simplest way to use SKUs is to just assign the SKU to be the product code itself. Then, for example, you would add the pair `"B071JM699B": "B071JM699B"` to the `products.json` file. This adding to the file **must** be done. This is how the program will know what product the user actually wants to buy. Be careful here; this is a ripe place for human error.
    * If you want official product images to put in your product page, use the following code with methods from `src/zinc.py`
    ```python
    #in below, prod_code is a specific product code. ZINC_TOKEN is fetched in the same way as other credentials.
  	data = get_prod_data(ZINC_TOKEN, prod_code)
	for img_url in data["images"]:
		print(img_url)
     ```
     You can then download these images through a browser and upload them to your product page. See [**Zinc**](#zinc) for more info on zinc backend. 
5. **Set up the order processing email account**. Edit the settings to send a notification on new orders to the desired email address. This email account will be accessed by the program (Note: the email address should have [access to less secure apps enabled](https://support.google.com/accounts/answer/6010255?hl=en)). Next edit the template of the order notification email to include an *'x'* following the word *"Order"* in the subject, e.g. instead of *Order #123456* in the subject it will be *Orderx #123456*. This is because searching for a literal '#' in email subjects causes unreliable behavior.
### **Basic Shopify Backend** 
Most basic methods for the shopify backend are in the file `src/shopify.py` (not to be confused with `src/shopify_order_processing.py`. See [**later section**](#shopify-order-processing) for this). 
At the beginning of the file, the Shopify API credentials are fetched using the `CredsManager` class (see [**secrets: CredsManager**](#credsmanager)). These should have been added to AWS when you set up the store in **Shopify: Setting up the Store**. 
This code can be a bit confusing because parts of the shopify API are quite messy. As of now, the methods relating to fulfillment are not yet fully functional. You may change these if you want to implement some fulfillment (currently, if an order is shipped, you must manually fulfill that order through shopify's site). 
The main functional code has to do with conversion between order numbers, order ids, and coinbase charge codes. Basically: when Shopify sends you an email (as is detailed in [**Email**](#email)) it lists an order number. This is a readable number like "#1012". In order to get actual info on the order, however, you need the order id which is different than the order number. This can be fetched using `order_num_to_id(order_num: str)` which will make a request; it is best practice to log this id in general. You also will need the coinbase charge code to check if a payment has been confirmed, cancelled, etc. To get this you can call `order_id_to_cb_chg_code(order_id: str)`. Notice that you already need the order id. You can also call `order_num_to_cb_chg_code(order_num: str)` which just calls the previous two methods in a row. You will most likely want to call `order_num_to_both(order_num: str)` and then log the results. This method will return a dict with the order id and coinbase charge code. The order id will have key `"order_id"` and the coinbase charge code will have keys `"cb_chg_code", "cb_chg", "chg_code"` (there are multiple keys storing the same value for convenience). Again this method should be called near the beginning of processing and then the output should be logged for easy access (this *is* currently done in `src/shopify_order_processing.py`. See [**next section**](#shopify-order-processing) for more info on this file. 

### **Shopify Order Processing**
The file `src/shopify_order_processing.py` contains most of code governing the ordering process. The code is fairly lengthy, and is best understood by reading it and the comments. **Important**: this file is what should be called by the lambda rule in AWS. See [**AWS: Lambda**](#lambda). In other words, one iteration of order management is achieved by running `'python3 shopify_order_processing.py'` from the terminal. 

**Overview** Most of this code processes orders at different stages. It does this by moving emails between mailboxes, and keeping extensive logs in json files using `Logger` (see [**Logging: Json Logging**](#json-logging)). Many methods require an `Emailer` instance as input. This file will also get email credentials and zinc credentials at the top using `CredsManager`. See [**secrets: CredsManager**](#credsmanager) and [**AWS: Credentials**](#credentials). Most methods in this file are labelled as `_process_...`; the leading `_` indicates that these methods should be called with care. Different process steps are done in different methods, which is detailed extensively in the file. One full iteration of processing is done in the `do_iteration(emailer: Emailer)` method. This is what will be called by the lambda rule. Most of these '_process' methods are similar in function. The one that stands out is `_process_new_in_inbox(emailer: Emailer, name=EMAIL_NM, pw=EMAIL_PW)`. This method reads the inbox, moves all emails to *"all email history"*, moves order emails to *"new pending payment"*, moves non-order emails to *"non-order"*, and then clears the inbox. This method is unique in that it governs the inbox which is the least regulated mailbox: the inbox. Any email can be in the inbox, which is why it is critical to separate out non-orders. Besides the rest of the '_process' methods there are a few outliers detailed below.
1.  The method `msg_to_dict(email_msg)` converts an email message object (`email.message.EmailMessage`) into a dict with keys `"subj", "subject", "sender", "body", "from"`. The keys `"subj", "subject"` hold the same value, as do the keys `"sender", "from"` for convenience. 
2.	The method `_check_msg_dict(md: dict)` verifies that a message dict (one returned from `msg_to_dict(email_msg)`) is in good form. In particular, it checks for the presence of all the keys. For the keys with identical values, if one key is present, the other is overwritten with the same value. This way both keys are always present and have the same value. This method does raise Exceptions if the input is misformatted. This should not be a large issue since this is (hopefully) only called right after a message dict is made. 
3.	The method `_parse_new_order_msg_dict(md: dict, max_quantity=MAX_QUANT)` is what actually processes an email message that contains an order notification (i.e. one delivered to the order processing email account). It takes in a message dict, but if an `EmailMessage` is provided, it converts it using `msg_to_dict(email_msg)`. The parameter `max_quantity` should be a positive integer. If it is non-positive, it defaults again to `MAX_QUANT` (which comes from the `src/const.py` file; see [**Constants**](#constants)). The method returns a dict with a shipping address, payment method (for now always "coinbase_commerce_"), shipping method (for now always "cheapest"), number of unique products ordered, and a list of products (list of dicts with SKU and quantity). Much of this output is designed to plug directly into the zinc API using `src/zinc.py` (see [**Zinc**](#zinc)). In particular the product list, the shipping address, and the shipping method can be directly plugged into a zinc request. This method is pretty messy since it is parsing lines of text. The only real way to debug it is to have it act on an actual order message.

**Not Implemented**. The main aspect that is not yet fully implemented is the shipping and fulfillment processing. The method `_process_zinc_confirmed_pending_shipping(emailer: Emailer, mb='"zinc confirmed pending shipping"')` does **not** work correctly. It is called in `do_iteration(emailer: Emailer)` but does nothing for now. For more information see [**What to do Next**](#what-to-do-next).

## **Zinc**
The most important key for working with the zinc API is to read [the docs](https://docs.zincapi.com/). After that there are some things to keep in mind. 
* Zinc credentials are fetched at the top of the file in a similar manner to others. See [**secrets: CredsManager**](#credsmanager) and [**AWS: Credentials**](#credentials)
*	Some of these methods are more vestigial and should not directly be used. In particular `_get_all_orders(...)` is now replaced by `get_order_statuses(...)`. 
NOTE: `get_order_statuses(...)` should not be confused with the method `get_order_status(...)` which fetches a singular status. Similarly `place_sing_amzn_order(...)` is now replaced by `place_orders_shopify(...)`. 
* The method `place_orders_shopify(...)` is expecting input formatted in the same way as it is in `_parse_new_order_msg_dict` (in `src/shopify_order_processing.py`). See #3 in [**Shopify Order Processing**](#shopify-order-processing).
* Zinc requests have a request id associated with them. This comes from zinc's end. This id should be logged as soon as possible to avoid losing track of an order.
* When adding a product to shopify store, call `get_amzn_prod_code(url: str)`.
* `_clean_address` cleans a shipping address to take the form that zinc is expecting. See the [zinc docs](https://docs.zincapi.com/#address-object) for an example. 
* The method `extract_shipping_from_status(status: dict)` is **not** implemented. It is a stub/start of a method **only**. See [**What to do Next**](#what-to-do-next).
* Lately, there have been an increasing number of orders that fail with a "zma_temporarily_overloaded" error. This happens when an order times out. The issue seems only persistent with dry run orders, i.e. orders with a max price of 1 cent. This might have to do with setting a discount in the ordere too; see the docs.
* Along with the above method (`extract_shipping_from_status`), this file is where much of future work should take place. You will spend time fetching shipping info. This has lots of possible edge cases with delays, out of stock products, missing shipments, refunds, partial deliveries, etc.
* **Default phone number**. One more little quirk: the zinc API requires that a phone number be provided when placing an order. Now on shopify you can require an email from the user, or an email *or* phone number. But you cannot force them to provid a phone number. For this reason, all of the orders have a default phone number filled in. This number is in AWS' Secrets Manager (see [**AWS: Credentials**](#credentials) and [**secrets: CredsManager**](#credsmanager)).

## **Coinbase Commerce**
Currently the payment is handled by Coinbase Commerce on the backend in the file `src/com_coinbase.py`. If the payment gateway is changed in the shopify store, then this section will not be applicable. 

As with zinc (see [**Zinc**](#zinc)) the best way to understand this part of the ordering process is to read [the docs](https://commerce.coinbase.com/docs/api/) (also similar to zinc, credentials for the API are fetched using `CredsManager`. See [**Secrets: CredsManager**](#credsmanager) and [**AWS: Credentials**](#credentials)) In essence: the shopify store will create a coinbase charge. This coinbase charge has a code associated with it (fetch it from an order number using methods in `src/shopify.py`; see [**Shopify: Basic Shopify Backend**](#basic-shopify-backend)). Using this charge code, order details can be fetched. Now, while all methods in the file are functional, only one is regularly called in the order process: `get_timeline(chg_code: str)`. This returns a list of timeline updates. Each item in the list is a dict with two keys: `"time", "status"`. The "time" contains when this update occurs, and the "status" is usually what you are interested in. A status can be one of the following: `"NEW", "PENDING", "COMPLETED", "EXPIRED", "UNRESOLVED", "RESOLVED", "CANCELED", "REFUND PENDING", "REFUNDED"`. Many of these are complicated and not worth dealing with directly in the file; when encountered the program simply redirects the order to a mailbox labelled *"unknown error coinbase charge"* in the order processing email account. The statuses that are uniquely dealt with are `"NEW", "PENDING", "COMPLETED", "EXPIRED"`. The program checks repeatedly for when a charge is completed. The charge will go from "NEW" to "PENDING" to "COMPLETED" (if everything has gone correctly). Once a charge is completed, it will be moved to another mailbox and the actual product will be ordered through zinc. If a payment expires, the order email will be moved to the mailbox *"payment expired"*. To get the last status of a coinbase charge (from the charge code) see the following example:
```python
# chg_code is some charge code already fetched
# get_timeline comes from com_coinbase.py
timeline = get_timeline(chg_code) # a list of updates
last_update = timeline[-1] # a single update; time and status.
last_status = last_update["status"]
```
Or, more concisely:
```python
# following throws away all data except last status
last_status = get_timeline(chg_code)[-1]["status"]
```
Once the last status is fetched, it can be compared to the possible values. 

**Where to continue**. If this store is used often, there should be careful monitoring of the email address receiving all the order-notification emails. If there are issues with edge case payment errors, or if refunds must be added, there should be more functionality added. This functionality will likely be in the file `shopify_order_processing.py` but it will pertain to the Coinbase Commerce system. 

## **Secrets**
The file `src/secrets.py` manages secret credentials. It does so through the `CredsManager` class. 

### **CredsManager**
This class is another pseudo-class in that all of its methods are static, and the class should never need to be instantiated. It is a class for organization purposes, as well as ease of adding credentials. This class will return credentials from AWS's Secrets Manager (see [**AWS: Credentials**](#credentials)). So the returned value is dictated by what is stored in AWS (`None` is returned if an Exception occurs). For a secret in AWS there will be a credential id (name specified for this secret, should be kept private) and a dict of secret values associated with that name. As an example, let's suppose that you have stored two credentials in the `CredsManager` class already: Xbox Live Credentials and Club Penguin Credentials, named "example/xbox-live-creds" and "example/club-penguin-creds" respectively in AWS. Then the class `CredsManager` would appear as follows: 
```python
class CredsManager(object):
	REGION_NAME = "us-east-2"

	# private static variables.
	__XBOX_LIVE_CREDS_ID = "example/xbox-live-creds"
	__CLUB_PENGUING_CREDS_ID = "example/club-penguin-creds"
	
	def __init__(self):
		pass # this class is not instantiated ever
	
	@staticmethod
	def get_creds(creds_req: str):
		# check if one of the creds we have access to. 
		# if it is we set the secret_id to it.
		# if this method fails it returns None
		try:
			creds_req = creds_req.lower() # for easier name detection. 
			if ("xbox" in creds_req):
				secret_id = CredsManager.__XBOX_LIVE_CREDS_ID
			elif  ("club" in creds_req) or ("penguin" in creds_req):
				secret_id = CredsManager.__CLUB_PENGUING_CREDS_ID
			else:
				raise Exception
		except:
			# phrase not found or failed .lower(), indicating not a str.
			return None
		
		# rest of method should not be touched
		...
		# end of method


	# following are just for convenience and simply call the more general get_creds method
	@staticmethod
	def get_xbox_live_creds():
		return CredsManager.get_creds("xbox")
	
	@staticmethod
	def get_club_penguin_creds():
		return CredsManager.get_creds("penguin")
```
The above example should show how to implement this class. It is a skeleton that can be edited in a few locations to allow for any number of credentials to be fetched. (Note that the class uses private variables to limit the scopes of the credential ids, which are really what should be kept secret.) If you wanted to add another credential to the example you would:

1. Add the credential name as a private static variable. Static variables are set above the `__init__` method in the class. To make it a private variable, start the variable name with "__" (two underscores).
2. Add an `elif` to the chain near the beginning of `CredsManager.get_creds(creds_req: str)`. Here you have lots of freedom. You choose what phrase you want to match to this credential, and then build the `if, elif` chain around that. This can be as complex or as simple as you want. 
3. Add a static method that just calls the `get_creds` method. This is not mandatory, but is convenient: it means you do not need to remember what key phrases you chose for each credential. 

With the above, any credential from AWS's Secrets Manager can be fetched from one class. The thing to keep in mind is that the return value is dictated by what you store in AWS. It is up to you to keep a convention so that when a credential is fetched you know what keys to use on that dict. 

### **Credential storage convention**
 The convention currently used is

* API credentials are stored with keys "api_key" and "api_secret" where "api_key" is usually the public credential, and "api_secret" the private one. If an API only has one, you can use only one key or preferably just set one blank to avoid key errors. 
* Username/password credentials are stored with keys "name" and "password". 
* Any single piece of info that is not an API credential is stored under the single key "name".

To see how this convention setting comes into play, let's continue considering our previous example. Say you want to use the `CredsManager` class from the previous example to fetch both the Club Penguin and Xbox Live credentials (assuming these are username/password pairs). If the above convention is followed it would be:
```python
from secrets import CredsManager

creds_xbox = CredsManager.get_xbox_live_creds() # a dict
creds_peng = CredsManager.get_club_penguin_creds() # also a dict

name_xbox = creds_xbox["name"]
password_xbox = creds_xbox["password"]

name_peng = creds_peng["name"]
password_peng = creds_peng["password"]
```
This is simple since the same keys are used for both credentials. Now suppose that the convention is not kept, and the club penguin username is stored under "username" instead of "name". Then the above code, which looks correct, would cause an Exception. Instead it would need to be 
```python
from secrets import CredsManager

creds_xbox = CredsManager.get_xbox_live_creds() # a dict
creds_peng = CredsManager.get_club_penguin_creds() # also a dict

name_xbox = creds_xbox["name"]
password_xbox = creds_xbox["password"]

name_peng = creds_peng["username"]
password_peng = creds_peng["password"]
```
The above is not ideal since the programmer has to remember the specific keys used for each credential pair stored. This is why it is important to maintain a convention across the project.

## **Constants**
The file `src/const.py` contains any non-sensitive constants used across the project (non-sensitive meaning they do not need to be kept secret). Currently there are only three: 
1. `ZINC_MAX_COST`, the maximum total cost of a zinc order in pennies. Currently it is set to $50.00, or 5,000 in pennies. This is a safegaurd to stop erroneous large orders. If you do not want a safegaurd, set it extremely high; the safegaurd happens on zinc's end so a max cost must be used. 
2. `MAX_QUANT` which is the maximum number of a single product that can be ordered. It is currently 100. This means that placing an order for 101 bottles of hot sauce, for example, will raise an Exception in `_parse_new_order_msg_dict(md: dict, max_quantity=MAX_QUANT)` (see [**Shopify: Shopify Order Processing**](#shopify-order-processing)). This is an internal safegaurd, so if you do not want to keep it, remove the code that checks the quantity of an order against this constant.
3. `REPO_PATH` which is the path to the repository on the local system. This directory should contain the `src` directory and the `data` directory. This is used across the project, so make sure to set it correctly.

## **AWS**
AWS is probably the most complicated thing to set up. This section will not explain how all of AWS works, instead just give the rundown of how to replicate the current setup. If you change the setup, or want more behavior, you will likely have to change the AWS system. Do this carefully. 
### **IAM Roles**
The IAM Roles are what gives different parts of the system permissions. The current roles and permissions associated with them are:
* **"shop-backend-ec2-role"** *(Role ARN: "arn:aws:iam::046098159410:role/shop-backend-ec2-role")*. This is the role that the EC2 instance will use (more on this later). It has the following permissions:
	* **"SecretsManagerReadWrite"** *(Policy ARN: "arn:aws:iam::aws:policy/SecretsManagerReadWrite")*. This is what allows the `CredsManager` class to access secrets. More on this later in [**AWS: Credentials**](#credentials) and above in [**secrets: CredsManager**](#credsmanager). If this AWS account is used for other projects, it would be wise to customize and limit the read acess for this permission policy. That way this project would not have access to sensitive credentials for other probjects.
	* **"AmazonSSMManagedInstanceCore"** *(Policy ARN: "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")*. This is a general policy that is needed for the EC2 instance.
* **"shop-backend-lambda-roll"** *(Role ARN: "arn:aws:iam::046098159410:role/shop-backend-lambda-roll")*. This is the role that the lambda function will use (more on this later). It has the following permissions:
	* **"AmazonEC2ReadOnlyAccess"** *(Policy ARN: "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess")*. This allows the lambda function to read information about the EC2 instance on which it operates. This is not really necessary for the current implementation, but if an instance needs to be opened, or checked if closed, it will be needed. Since this could likely be necessary in the future, the permission is included. 
	* **"AmazonSSMFullAccess"** *(Policy ARN: "arn:aws:iam::aws:policy/AmazonSSMFullAccess")*. This is a general policy that is needed for the lambda function.
	* **AWSLambdaExecute** *(Policy ARN: "arn:aws:iam::aws:policy/AWSLambdaExecute")*. This is what allows the lambda function to execute commands on the EC2 instance; in particular it allows it to execute `src/shopify_order_processing.py` which is where actual processing is done.
	* **NOTE**: Yes, there is a typo in the name. It is named "...roll" instead of "...role". This is easier to leave be if possible. 

### **EC2 Instance**
The current EC2 instance is of type "t2.micro". It is named "backend-for-store" with instance id "i-06ee575934b0c82eb", IPV4 public DNS "ec2-18-118-211-248.us-east-2.compute.amazonaws.​com", and public IPV4 IP "18.118.211.248". It uses the "shop-backend-ec2-roll" role.
It currently has security group "launch-wizard-1" with an inbound rule allowing SSH from the root user's home IP **and** inbound SSH from any IPV4 or IPV6 address (this may need to be changed or updated later), and outbound rules allowing all IPV4 outbound traffic.

The instance is where this repository should be cloned. The path should be specified in the lambda function (see **AWS: Lambda** below).

### **Credentials**
Credentials are managed using the "Secrets Manager" service. It is fairly easy to add a secret this way. Only a few things to remember:
* For secret type (selected at the very beginning), select "Other type of secrets".
* For name/key pairs (the actual secret), try to follow a naming convention as detailed in [**secrets: CredsManager: Credential storage convention**](#credential-storage-convention). 
* For the secret name, it is also best to follow some convention. Make sure to add this name as a private static variable to the `CredsManager` class (in `src/secrets.py`); see [**secrets: CredsManager**](#credsmanager)
* For this to work, the "SecretsManagerReadWrite" policy is required for the EC2 instance. It is currently there under the "shop-backend-ec2-role"; again you may want to limit permissions if you have lots of credentials stored.

### **Lambda**
The lambda function will call the command `'python3 shopify_order_processing.py'` when triggered. If you are setting it up from scratch, the function is a python lambda, and copy the code from `src/lambda_skeleton_.py` into the function; do not copy the file, but instead the *contents*. The skeleton file should **not** be used for anything else as the indenting is formatted differently than other files.

After copying in the code, you will need to specify a few things near the top of the file:
* **Region Name** is stored in `REGION_NAME`. As of now, it is "us-east-2". This region name should be consistent across all services in AWS, and may cause issues if it is not. See [**Troubleshooting and Tips**](#troubleshooting-and-tips) 
* **Working Directiory** is stored in `WORKING_DIRECTORY`. This should be the path to the `src` folder inside the cloned repository. I.e. it should be something like `/home/ubuntu/crypto-store/src` (which is what it is currently).
* **Comand** is stored in `COMMAND`. It is a multiline string that currently contains the line `python3 shopify_order_processing.py` (no inner quotation marks). Note that the `shopify_order_processing.py` file is located in the `src` folder, which **should** be the `WORKING_DIRECTORY` above. 
* **Instance Id** is stored in **INSTANCE_ID**. It is the id of the EC2 instance, currently "i-06ee575934b0c82e".

This lambda function will be triggered by a rule (not role) in [**AWS CloudWatch**](#cloudwatch) below.

### **CloudWatch**
CloudWatch is where the rule that triggers the lambda function will be located. The rule is currently named "backend-lambda-rule" *(ARN: "arn:aws:events:us-east-2:046098159410:rule/backend-lambda-rule")* and will trigger the lambda function every 5 minutes. This rule must be enabled for the system to run, and may be disabled when work is being done on the instance.

## **Troubleshooting and Tips**
There are a few quirks to this system that may come up. 

* **General tip**: keep careful track of the order emails when you are playing around with order flow. Currently if a zinc Exception occurs, an error email is sent detailing this (see **Email: Error Emails**); you can add similar error protocols throughout the program if an issue keeps coming up.

* **Shopify payment lag**. This is a glitch in the shopify system that can occur right after a new order has been placed. When a customer places a new order, a notification email is sent to the desired inbox (this is how the backend system becomes aware of the program). When this happens there is a brief lag in the shopify API: although the order has been placed and the notification sent, fetching order data from the API will return nothing. This appears as if the order does not exist. After about 30 seconds, the order information will be returned from API calls. Now the methods in `src/shopify.py` that return order data will raise Exceptions when no data is returned. Since this could indicate the lag issue, in the method `_process_new_pending_payment(...)` in `src/shopify_order_processing.py` if an Exception is raised when fetching order data, the program just continues onto the next order. This way if a order is lagging behind, the Exception will be ignored, the email will remain in the mailbox, and will be processed in the next iteration (by which time hopefully the order is not lagging). The one issue with this, of course, is that if an order is causing *actual* Exceptions, it will just remain in the mailbox permanantly. This has not been a large issue yet. 
* **Module not found error in AWS**. When importing a module in the AWS lambda function (see **AWS: Lambda**), sometimes a "Module not found" Exception will be raised, even when that module has been installed on the EC2 instance. This happens when a python package is installed locally, not globally, on the EC2 instance. For example when installing numpy the command `'pip3 install numpy'` could only install the package locally, not globally, causing issues if numpy were used in the lambda function. To also install this package globally run `'sudo -H pip3 install numpy'` which forces the package to be installed in the home folder.

* **Resetting an order**. When programming and debugging, an order might be processed incorrectly. This could be the order email skipping a mailbox, going to the wrong mailbox, etc. If this happens a good way to fix the order is: 
	* Stop the system from activating by either redirecting the program flow in `src/shopify_order_processing.py` or temporarily disabling the CloudWatch rule (see [**AWS: CloudWatch**](#cloudwatch)). 
	* Delete the json log file of the order in the `data/json_order_data` directory (the file will have the order number in the name); if you want to be careful, make a backup copy and move it elsewhere, just make sure the log file is not in the `data/json_order_data` directory.
	* Find the order email in the order processing email account (it should be in the *"all email history"* mailbox at the very least). 
	* Manually move this email to the inbox.
	* After it has been moved, remove all other labels from the email (i.e. delete it from all other mailboxes). If you want to be careful, you may want to not delete it from *"all email history"*; this caution should only be necessary if you are changing the `_process_new_in_inbox(...)` method in `src/shopify_order_processing.py`.
	* Once the email is in the mailbox and has been deleted from all other mailboxes (same as being stripped of all labels), you can start the system back up and observe what happens. You can either re-enable the CloudWatch rule (if you disabled it) or trigger the lambda function once manually. The latter is useful if you are debugging a persistent issue.
	* The order should now be processed correctly. If it is not, there is a larger bug that needs to be addressed. Look at the json log file and see what happened.
	* If you just manually triggered the lambda function make sure to re-enable the CloudWatch rule once the issue is fixed.
* **EC2 login issues, termination issues, and general troubleshooting**. 
	* If you terminate the EC2 instance, credentials for the instance will change. The public address *will* change. You will need to change your SSH hosts to reflect this if you want to be able to log into the instance. Double check that other credentials, in particular the instance id, are the same. If they change, update them across the program (for instance id, change it in the lambda function as detailed in [**AWS: Lambda**](#lambda)). 
	* Because of the above, it is not desirable to terminate an EC2 instance. Try to avoid this unless absolutely necessary. Instead do the below.
	* When in doubt, reboot the instance and wait a few minutes (takes time to reboot fully). This should not change credentials and can fix a lot of issues with logging in. If the issue persists play around with the instance.
	* Because there can be login issues with the instance, it may be worth it to invest in keeping another backup of order data. This is not strictly necessary, however, since lost orders can be reset using the above tip on resetting an order.

* **AWS Region**. The region selected from AWS *could* cause issues if not kept consistent. For now it is selected as "us-east-2". The region is specified in the top right of any AWS service page.


## **What to do Next**
This program is a work-in-progress. The most important TODO is to carefully monitor the system. Check for issues, errors, out of stock products, and shipping issues; also currently the owner of the store must manually fulfill products ordered by customers. In terms of programming tasks the next steps should be 
* **Shipping and fulfillment automation**. This is the largest non-implemented portion of the system. Currently there is no *working* automation for checking shipping status and issuing fulfillment orders through shopify. This step of the process also has lots of edge cases: shipments can be delayed, lost, or returned; some items may ship earlier than others, meaning multiple fulfillments must be done through shopify; it could even be that a single unit of a product could ship later, which means fulfillments would have to be issued unit by unit, not product by product; and fulfillment orders should contain shipment tracking urls, of which there can be several. Since this would involve lots of different zinc programming (parsing all the possible cases) and complex fulfilling through the shopify API, the effort to implement this could be significant. 
* **Roll/Role typo**. As specified earlier, there is a small typo in the AWS system. One role is named like "...role" and the other "...roll" erroneously.
* **Working on backups**. It may be desired to make an automatic backup of the order records. 
