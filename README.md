FJBot
========================================================================
[![status](https://img.shields.io/badge/Project%20Status-work--in--progress-green.svg)](#)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=jesus_andrade45%40yahoo%2ecom&lc=US&item_name=GitHub%20Projects&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)

A Discord bot with focus on WWE Matches and includes Chatango and Twitter integration

**Discord Server:** [WatchWrestling](https://discord.gg/Q9mX5hQ)


Introduction
------------------------------------------------------------------------
This Discord Bot was originally created for a Discord Server in 2017 that focuses on all-things wrestling. It was made with the focus to integrate [WWE Matches](https://fancyjesse.com/projects/wwe) into the Server. This allows Discord Users to bet and rate matches, look up Superstar biographies and birthdays, share gifs, and be alerted on events. In short, enhance the user experience. 

Integration with Twitter and Chatango was later added onto the bot. 

Originally, the bot existed on a single Python file. I had no idea I would be supporting this bot for close to a year or even begin scaling it to include additonal features. With all these additional featues, I decided to transition this Discord Bot project to use COGs.

Prerequisites
------------------------------------------------------------------------
Python3


Installation
------------------------------------------------------------------------
TODO


Usage
------------------------------------------------------------------------
TODO


Release History
------------------------------------------------------------------------
2018.10.14
* Added User class
* Updated COGs to use new User class
* Added direct PM to Discord Server owner function
* Updated admin COG checks
* Updated ch library with alterations (bugs found)
* Updated chatango COG to include match listings and betting
* Modifications to dbhandler to explicitly call queries
* Updated credentials to include Discord invite link
* Text fixes

2018.09.06
* Database redesign (to be included in repository)
* Various database optimization within dbhandler
* Created Class module for readability
* Removed \_\_obosolete__ directory
* Updated logging between COGs - all use main fjbot function now
* Added admin commands
* Heavily updated chatango COG
* Updated tweet log within twitter COG to use async functions
* Started progress on twitter COG to accept PMs
* Added additional checks
* Renamed COG wwe to matches
* Bug fixes

2018.06.24
* Updated database reference between COGs
* Added ch.py library used for the chatango.py COG
* Bug fixes

2018.06.10
* Bug fixes with COG communication

2018.06.09
* Transition to COG model

2018.06.08
* Initial introduction to GitHub


License
------------------------------------------------------------------------
See the file "LICENSE" for license information.


Authors
------------------------------------------------------------------------
FancyJesse
