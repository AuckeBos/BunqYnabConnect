# BunqYnabConnect

Connect your Bunq and Ynab accounts! Run this app as a
[Flask](https://flask.palletsprojects.com) server, and any payment you make with Bunq, is
synced to Ynab automatically!

## Setup
The server runs within a docker container, the docker-compose and Docker file are 
included in the repo. A manual setup has to be ran once, on the host. This setup does 
not require installation of any package, although python 3.X should be installed. 
Perform the following steps to get up and running:

1. Create a Personal access token in Ynab. This token is needed in the setup script. Take
   a look at the [Documentation](https://api.youneedabudget.com/).
2. Create an Api key for Bunq. This key is used once to register this app to your Bunq
   account. Bunq will respond with a configuration file, which is then used for login
   purposes. This token is needed in the setup script. Take a look at the 
   [Documentation](https://doc.bunq.com/#/authentication).
3. The other steps include providing login credentials for Bunq and Ynab.
   (setup.py)[setup.py] guides you through this process. Run `python setup.py` in the 
   scripts folder. This will run the one-time configuration steps, it asks for user input during the
   process.
4. To connect your Bunq ibans with your Ynab accounts, make sure that for each Ynab
   account that belongs to one of your Bunq accounts, set the description of the Ynab
   account equal to the Iban of the Bunq account. The script will now book each payment
   on the Bunq account to the corresponding Ynab account.
5. Now build the docker image, and start it, using `docker-compose up --build`.
6. The container starts, and restarts on boot. It automatically starts the following 
   processes:
   - The `mlflow` client on port 10000. The port is forwarded to your host, hence 
     you can reach it at `http://127.0.0.1:10000`.
   - The server that receives Bunq transactions, and forwards them to Ynab. It is ran 
     on the port which is defined during setup.
   - Supervisor, which makes sure that above server is always running. It can be 
     accessed at `http://127.0.0.1:10001`, to check its status.
   - Every sunday morning, at `06:00`, the container will re-select, -configure, -train, 
     -deploy, and -serve the best model on the newest data. The server is restarted, 
     such that it uses the new model. 