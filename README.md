
Github Data Mirror!
==================

This project aims to mirror all Github issues, PR and release data of a given organization into a local MongoDB for analytics purposes.

The goal is to perform an initial sync using Github REST APIs and then update the DB everytime Github WebHooks send an event.


MongoDB Schema
--------------

The local MongoDB is called `github` and have one collection for each synced object.

The Collections are:

* github.issues
* github.pulls
* github.releases

Each collection stores the exact return from the Github API for that object (with the exception of `issues` that have and extra attribute called `events` which stores all events related to that issue – like label, unlabeled, opened, reopened, etc).


Running using Docker Compose (usually local)
------------------------------------------------
Note: This method requires that docker and docker-compose were previously installed on your machine.


To run Github-data-mirror using Docker Compose you need to first set your environment variables in the file `webhook.env`. We currently have an example file named `webhook.env.example` that could be copied and changed.


Running using Gunicorn (usually production)
--------------------------------------------

Enter the directory `src/`.

Set the environment variables from the file `webhook.env`. Set the server and port of your MongoDB using the variables `GHMIRROR_MONGO_HOST` and `GHMIRROR_MONGO_PORT`.

Now just run the command `gunicorn ghmirror.wsgi:application`.

If your Linux distro curretly runs using systemd here is an example of an unitfile you could use:
```
[Unit]
Description=Github Data Mirror

[Service]
User=githubmirror
Group=githubmirror
EnvironmentFile=-/etc/default/github-data-mirror
WorkingDirectory=/usr/local/github-data-mirror/src/
ExecStart=/usr/local/bin/gunicorn ghmirror.wsgi:application --access-logfile - -b 0.0.0.0:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Performing the initial Sync
---------------------------

To sync all data from all repos from a given organization you need to run the command 
`python src/manage.py ghsync --organization=<orgname>`

Make sure to set the proper environment variables before running the ghsync command.


Configuring the organization Webhook
-------------------------------------

Access Github webhook settings page for the organization and then click in the `Webhooks` option (the link should be something like `https://github.com/organizations/<orgname>/settings/hooks`).

Click on `Add webhook`. In the Payload URL field add the URL of your service; in Content type choose `application/json` and in Secret, add the Random string you previously set in your environment variables. Enable SSL verifications, select the option `Send me everything` and that's it.

You can also send a test payload to make sure your service is working.

From now on, your local MongoDB should be receiving every updates from the currently synced objects. 
