# A Telegram Bot for Reddit Scraping
##### Just a handy little worker app that finds new saved reddit posts and uploads a copy of the media onto a desired telegram channel.
##### Please open a issue if you have any requests.

### Instructions for Chat ID
#### Begin by setting channel to public and create a invite link.
#### Invite link: t.me/xyz -> Chat ID: @xyz
#### Replace {bot_token} and {chat_id} with bot token and channel name (prefixed with @) respectively.
##### https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text="Sample_Message"
#### Inspect the obtained response for the integer chat id. It should be a negative integer. The channel can now be taken private if needed.


### PS - Any S3 Compatible object storage can be implemented if needed, filebase experienced outages so removed it. Suggest me a good option that is free like filebase if you know one at u/ElucidatorZ T_T