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
Generating an estimate
Estimate will not save -> Check if gig has a valid load in/out for every Dept represented in the gig. An estimate cannot be generated if there is not at least one load in/out for every department working the event.

# Features
* Sign up for upcoming shows
    * Click to sign up if has group
    * Click to test if not has group and not probie
    * Don't show positions a user cannot sign up for
    * Show a message with all jobs for gig if user cannot sign up at all
* Send company or group wide notifications
    * Use HTML in notification
    * Set status (color) of message
* Show shows that an employee has been assigned to
    [*] Show 5 most recent shows
    [ ] Paginate through shows
* List all shows BSSL has done
    * Show 50 most recent shows
    [ ] Paginate through shows
* ShowView
    * See name, date, start-end, location and org of show
    * See notes left for engineering
    * See loadin for each dept
        * See shop time
        * See load in time
        * See load out time
    * See systems rented 
        * See addons for a system
        * Report a system as broken
            * Submit notes for a broken system
            * Allow Shop Tech to monitor broken equipment with a ticketing system
            [ ] Shop tech receives email when broken system is reported
    * See employees working a show
        * Sorted by dept
        * Contact an employee (phone or email)
    * Day of Show
        * Allow an engineer to write show notes
        * Allow an engineer to add/edit/remove shifts from an employee
            [ ] Fix bug (same as office hours)
        * Allow an employee to view their shifts for a show and clock in/out
* Training
    * Allow an employee to sign up for training if there is available space
    * Allow an employee to request training for a specific system(s)
    * Allow employees to view static training resources
* Allow employees to view and change their personal information in SLUGS (with the exception of bnum)
* Allow employees to change their password
* Allow employees to view and upload paperwork
    * Download a blank form
    * Upload a completed form
    * Delete/Change submitted form
* Allow employees to view the last 100 shifts they've worked + any contested or unprocessed shifts.
* Allow managers to submit office hours
    [ ] Fix bug
* Allow GM and FD to access Financial Overview
    * See and act upon all shifts for a given pay period
    * See previous shifts in a previous pay period
    * Print out a timesheet for an employee
    * Print out a summary for a pay period
    * Override a shift from one pay-period to another
* Allow admins to access quick actions
    * Change the status of onboarding
    * Change the status of signup
* Allow admins to view groups
* Allow admins to upload and assign paperwork to be filled out
* Allow admins to create estimates
    * Print out estimates generated
* Allow admins to create invoices
    * Print out invoices generated
* Create Shows (gigs)
    * Staff shows
    * Send a staffing email
