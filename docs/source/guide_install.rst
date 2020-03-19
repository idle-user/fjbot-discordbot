.. Installing FJBot

================
Installing FJBot
================

These are the steps needed to run your own instance of **FJBot**.

.. important::

    If you're only looking to invite the bot to your Discord server.
    Use the following link: 
    https://discordapp.com/oauth2/authorize?&client_id=364938585675137035&scope=bot&permissions=199680

----------------
Clone Repository
----------------

This downloads a copy of the `FJBot GitHub repository <https://github.com/FancyJesse/fjbot>`_.
This is the source code for the bot. You can go in to read, update, or add your own code if you'd like
since you would be running your own instance.

.. code-block:: console
    
    $ git clone https://github.com/FancyJesse/fjbot.git

---------------------
Install Prerequisites
---------------------

This bot uses the following Python packages:

* discord.py
* mysqlclient
* youtube_dl
* tweepy

.. code-block:: console
    :caption: Installs all the above packages at once

    $ pip install discord.py[voice] mysqlclient tweepy tweepy

-------------
Setup Configs
-------------

The `Config <framework_config.html>`_ module contains the access tokens to Discord and credentials to your database.
It also has the list of `cogs <framework_cogs.html>`_ that should load upon startup.

See `Config <framework_config.html>`_ and just fill in the proper values.

.. important::

    * You must have a Discord Bot account.
    * The Twitter bot account is not required. 
    * The Chatango bot uses a regular account.

-------------------
Initialize Database
-------------------

This script creates the schema and tables required for saving user information.
Without this, a majority of the **FJBot**'s functionality would not work, or the bot 
won't start at all.

.. important::
    TODO: I haven't created this yet.. sorry.