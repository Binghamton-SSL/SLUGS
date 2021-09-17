### In Progress
* Allow managers to see inattentive employees via admin
* Add access for SA Employees
* Import and Export employees
* Send an email when a training request is received
* Track rate shift was paid at irrespective of changes to wages
<br><br>
BUG FIXES: 
    * Show "Signed Reservation" instead of "Signed Estimate"
    * Get rid of duplicate shifts showing on timesheet when shift started at midnight

#### V2.1.1 - 9/5/2021
* Add "available for signup" field - denotes at what date the gig will show on the signup page. Automatically set to 7 days prior to event
<br><br>
BUG FIXES: 
    * Show "ticket" no longer has issue where text overflows ticket

<hr>

### V2.1.0 - 9/5/2021
* Order gigs on show list page by most recent / furthest in future
* Order employees on payroll summary by last name
* Add CSV Export to Payroll Summary
* Add total hours & pay to Payroll Summary
* Add last login time to employee page
* Ability to create addons that are only charged during load in/out (Techs)
* Override description of line item in estimate/invoice
* Add signed estimate link to ShowView page
* Search for estimate by: Gig Name, Organization booking event, Organization SA Account #, Billing Contact
* Add version # to bottom of page for debugging purposes
<br><br>
BUG FIXES:
    * Admin now has consistent coloring across light/dark mode (force dark mode)
    * Search for gig in estimate admin no longer showing "Cannot show results"
    * Calendar no longer shows tentative gigs

<hr>

### 8/28/2021 - Security Update 
* Bump dependencies for security updates
* Push new requirements.txt and pipfile
* Black formatting for all files

### 8/28/2021
* Added Changelog
* Added setupdevenv command
* Added `requested` field to admin for paperwork
* Don't allow for a form to be changed by the employee once it's been processed. Instead, allow to download copy
* Concept of an overridden pay-period
    * A shift can be assigned to a pay period which the work falls outside of
    * Overridden shifts will be removed from the pay period to which they naturally fall
    * Overriden shifts will appear on timesheet in their own section
* Concept of an estimate payment
    * Payments on estimates decrease from the total due
    * Payments appear on invoices
* `Outstanding balance` added to estimate
* `Payments made` added to esimate
* Estimate or invoice link will show based on estimate status
* Invoices added
* Add ability for superuser to track admin log interactions globally
* Training requests can be sorted by `answered` status
* Training locations can be searchably selected
* Display on admin panel if training request has been answered
