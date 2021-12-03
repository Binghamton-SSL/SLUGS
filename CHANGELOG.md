### In Progress
* Allow managers to see inattentive employees via admin
* Add access for SA Employees
* Import and Export employees
* Send an email when a training request is received
* Track rate shift was paid at irrespective of changes to wages
* Show all instances of paperwork form on form page in admin
* Add ability to mass add groups to employees
* Search employees by phone number
* Sort employees by active employee, then by last name
* Add `isAdminMixin` mixin
* Add cli utility to show outstanding paperwork
* Separate out tentative event calendar feed
* Security Update: pillow, sqlparse, django-unicorn 
* Sort paperwork instances by processed or not
* Show outstanding paperwork for each employee
* Add "Abandoned" estimate status
* Add ATTN ENG (gig notes) to printed and virtual estimate
* Add training department to manager email
* Add custom 500 error page
* Add support for multiple types of office hour rates under one employee
* View estimate by status
* Add description to shifts (applicable for office hours)
* Show shifts on "You" page sorted by most recent
* Add one time fees prior to regular fees and convert %'s to running totals
* Add employee staffing stats to staffing page
* Add "pre-canned" messages to estimates for commonly added notes
* Show setup by time on showview page
* Gigs are now sortable by system rented
* Add next/current show timeline
* Accept all button for financial overview
<br><br>
BUG FIXES: 
    * Show "Signed Reservation" instead of "Signed Estimate"
    * Get rid of duplicate shifts showing on timesheet when shift started at midnight
    * Corrected issue where all addons where displayed as "SpotlightSpotlight Operator" in ICS output
    * Fixed formatting error with addons in ICS output
    * Fix error where estimate would not save if load out was after show end 
    * Corrected formatting error where gig str showed date in UTC
    * Corrected formatting error where training str showed date in UTC
    * Fixed error where signed estimates could not be viewed via admin
    * Fixed `(+1)` showing on timesheet when shift did not span day (was using UTC time for conversion)
    * Allow shows to be partially staffed
    * Fixed graphical bug where training request notes would expand page width on mobile
    * Estimate now shows billing contact not booking contact
    * Race condition handled when multiple managers attempt to staff an event at the same time
    * New multi-office hour manager page caching multiple objects
    * Make event ticket on homepage visisble up to 5 hours after event end time (useful for day of show)
    * Could not use day of show on mobile due to datetime widget not showing seconds (step="1")
    * Hopefully solve cross-user caching issue (NOT SECURITY RELATED)
        * Swap django-loginas for django-hijack
    * Don't show meta-data in admin (paid-at)
    * Error calculating edge case load in/out times
    * Update staffing score function + provide explaination
    * Current show ticket disappearing too soon
    * Changed logic for showing gigs staffed on to exclude duplicate gigs resulting from multiple jobs on same gig
    * Timeline starting gig early
    * Scroll lockout added while using mobile menu

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
