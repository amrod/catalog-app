# Recipe Catalog App

This Flask application provides a means to cataloging recipes, grouped by cuisine. It integrates third party user 
registration and authentication, provided by Google. Authenticated users have the ability to post, edit, and 
delete their own items.

## Setup

1. If using Vagrant:
  1. Install Vagrant and VirtualBox.
  2. Launch the Vagrant VM. A Vagrantfile and accompanying shell script are provided to setup all necessary software.
2. If not using Vagrant, you can just run the provided `pg_config.sh` script to setup all necessary software.

Optional: Run the `db_init_test_data.py` script to populate the database with some test data 

3. Run `run.py` to start the local Flask development server. By default, the application is available on port 5000.

## Using the Recipe Catalog

To make any changes (adding and removing recipes) you must first login. The application automatically creates your 
local user profile upon authorizing with Google the first time. 

To sign-in, click on the link on the top-right corner of the page.
 

#### Adding Recipes

After you sign-in, two new buttons appear on the navigation bar: Add Recipe and Add Cuisine.
At least one cuisine type must be added before adding a recipe. 

#### API Endpoints

To access the recipe data in JSON format, use the following URLs:

* **/recipe/JSON**
	* Returns all recipies in the catalog. 
	
*  **/recipe/\<recipe_id>/JSON**
	* Returns the recipe with ID <recipe_id>.

*  **/cuisine/JSON**
	* Returns all the cuisine types known to the catalog.

*  **/cuisine/\<cuisine_id>/JSON**
	* Returns all the recipes of corresponding to the cuisine with ID <cuisine_id>.

#### RSS Feed	

The RSS feed only lists the 15 recipes most recently added to the catalog.

*  **/recipe/recent.atom**


