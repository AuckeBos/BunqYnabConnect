# BunqYnabConnect

Connect your Bunq and Ynab accounts! Run this app as a
[Flask](https://flask.palletsprojects.com) server, and any payment you make with Bunq, is
synced to Ynab automatically!

## Setup

There are several configuration steps to be made, some of them require user input.
Execute the following step once, to setup the server:

1. If [Poetry](https://python-poetry.org) is not yet install, install it using pip:
   `pip install poetry`.
2. Create a virtual environment, and install dependencies, using `poetry install`.
3. Create a Personal access token in Ynab. This token is needed in the setup script. Take
   a look at the [Documentation](https://api.youneedabudget.com/).
4. Create an Api key for Bunq. This key is used once to register this app to your Bunq
   account. Bunq will respond with a configuration file, which is then used for login
   purposes. This token is needed in the setup script. Take a look at the 
   [Documentation](https://doc.bunq.com/#/authentication) .
5. The other steps include providing login credentials for Bunq and Ynab.
   (setup.py)[setup.py] guides you through this process. Run `poetry run python setup.py`
   . This will run the one-time configuration steps, it asks for user input during the
   process.
6. To connect your Bunq ibans with your Ynab accounts, make sure that for each Ynab
   account that belongs to one of your Bunq accounts, set the description of the Ynab
   account equal to the Iban of the Bunq account. The script will now book each payment
   on the Bunq account to the corresponding Ynab account
7. To run the server, use [Supervisor](http://supervisord.org/). Install it using 
   `sudo apt install supervisor`
8. Restart supervisor via `sudo systemctl restart supervisor`
9. Add an item for the server to the supervisor config. this config file is located 
   at `etc/supervisor/supervisord.conf`. Add the following lines:
   ```
       [program:BunqYnabConnect]
       autostart=true
       autorestart=true
       directory={REPO_DIR}
       logfile={REPO_DIR}/log.log
       user={YOUR_USER}
       command=poetry run python app.py
   ```
   
# Todos
Use an ML orchestratin tool, like [Kubeflow](https://www.kubeflow.org/)