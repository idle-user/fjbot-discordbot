.. Setting up auto-restart using screen (Unix)

===========================================
Setting up auto-restart using screen (Unix)
===========================================

This is a quick and ugly way of ensuring the bot is running and restarts if it is not.
I'm sure there are better ways of handling this out there, but this method has worked for me for
over a year already. 

.. Note::
    This method uses a cronjob and `screen <https://ss64.com/bash/screen.html>`_.
    
    .. code-block:: console
        :caption: How to install screen

        $ apt-get install screen
            
    .. code-block:: console
        :caption: How to access cronjob list

        $ crontab -e

------------
How it works
------------

#. A bash script is created that starts the bot in a named `screen`.
#. A cronjob is created to run the bash script every minute under the same name.

    * If the `screen` name exists, that means the bot is already running.

That's it.

-----------
Bash script
-----------

.. code-block:: sh
    :caption: discordbot.sh
    
    #!/bin/bash
    d=`date '+%Y-%m-%d %H:%M:%S'`
    if ! screen -ls | grep -q "fjbot"; then
        echo "$d: Restarting DiscordBot"
        screen -X -S fjbot quit
        screen -d -m -S fjbot python3 ./fjbot/bot.py
    else
        echo "$d: Already Running"
    fi

-------
Cronjob
-------

This creates the job that runs the script above every minute.
Temporary logs are made to ensure they are working.

.. code-block:: console
    :caption: crontab
    
    * * * * * /path/to/discordbot.sh >> /tmp/discordbot.log 2>&1 &