# Getting Started
## Getting the repo setup
* Clone Repo
* `$ cd SLUGS`
* `$ python3 manage.py makemigrations client employee equipment finance gig location SLUGS theme training unicorn utils`
* `$ python3 manage.py migrate`

## Before Committing
* Make sure no sensitive files are to be committed 
* `$ pip3 freeze > requirements.txt`
* 

## Deploying
* Pull latest changes
* `$ python3 manage.py makemigrations`
* `$ python3 manage.py  migrate`
* `$ python3 manage.py collectstatic`
* navigate to wherever the tmp dir is and `$ touch restart.txt`


## Creating a manual backup of data
`$ python3 manage.py dumpdata -a -o data.json`

## Hard reset the deployment
TBD


# Troubleshooting


# Features
See `FEATURES.md`
