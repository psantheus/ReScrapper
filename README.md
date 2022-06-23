# A Telegram Bot for Reddit Scraping
##### Just a handy little worker app that finds new saved reddit posts and uploads a copy of the media onto a desired telegram channel.
##### Please open a issue if you have any requests.
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/psantheus/ReScrapper)

### Instructions for Chat ID
#### Begin by setting channel to public and create a invite link.
#### Invite link: t.me/xyz -> Chat ID: @xyz
#### Replace {bot_token} and {chat_id} with bot token and channel name (prefixed with @) respectively.
##### https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text="Sample_Message"
#### Inspect the obtained response for the integer chat id. It should be a negative integer. The channel can now be taken private if needed.

#### If running on free Heroku, issues may arise due to restarts, wait for a "allow manual stopping without errors" log message before stopping and restarting the dyno to avoid potential errors. Do this preferably before 20 hours of run time is reached to be on the safe side. App may also be run locally to avoid restarts in which case a .env file with suitable values should be created.