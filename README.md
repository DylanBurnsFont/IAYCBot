# IAYCBot
## Bot for WG assignments 
### Setting up the env file. 
Modify the .env file by adding the bot token to BOT_TOKEN, can be found on How To Discord file. And the guild id to GUILD_ID. This can be found by setting your discord account to be in Developer mode (**User Settings -> Developer -> Activate Developer Mode**). You can now right click the server icon and copy the **Server ID**. This is the GUILD_ID. 

The DELAY_SECONDS is the delay between each command the bot will execute. Discord has a max rate on their end so even if setting it to a low number it will probably hover around 2/s. 

### Setting up the wgAllocation.csv file. 
This file contains three columns.
- name -> Does nothing just for readability to see who you're assigning what. 
- userid -> userid of the user, can be got by right clicking over them and copying User ID. 
- roleid -> roleid of the role you want to assign. Can be got by going into **Server Settings -> Roles** and then right clicking over the role and copying Role ID. 

### Running the bot
Make sure the Bot's role is **above** the wg roles if not it won't be able to assign them. Afterwards you can just run the python file. You will need to
```Python
pip install discord
```
in your environment before running it.

There is a role dictionary (roleDict) in [bot.py](bot.py) where you can assign the name of the WG to the role for better readability to the log file that gets created as roles get assigned to check if all is correct. 

Beware if you find any errors correct them asap as participants will see the wg allocations seconds after the email is sent (they speedy) and don't want issues to arise because of that.

