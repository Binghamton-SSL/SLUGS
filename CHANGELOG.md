### V2.3.1 - In Progress
* Added basic employee metrics
    * Number of jobs worked
    * Trainings attended
    * Time with company
    * Staffing score
    * Job Interest + placement over time
    * Types of jobs worked 
* Added end of employment date field
* Estimates will show the outstanding balance in their title
* BSSL Bingo board 
* Expand/Contract finance portal
* Add communication model
* Allow paperwork to be auto-assigned to employees on account creation (send email about paperwork on account activation if outstanding)
* Add ID barcode field to employee
* Add 3rd party vendor support
    * Add vendor equipment 
    * Add vendor rentals to Gig
    * Add subcontracted equipment to invoice and estimate
    * Add Subcontracted Equipment Order Form Generation
* Add auto-sign functionality to contracts for managers
* Add rich HTML notes to Vendors
* Add capability to remove signature lines from Estimate
* Spookify SLUGS
* Add pricing for show duration only on addons
* Add group support to OIDC authentication
* Add Self Service Kiosk
* Mark Timesheet as signed widget now adds a Object Log
<br><br>
BUG FIXES:
    * Saving a fee will now save the associated estimate to update price
    * Saving a payment will now save the associated estimate to update price
    * On paperwork admin page, only show current employees (to limit loading times)
    * Only show shift statistics on employee overview page if they've worked a shift
    * Remove automatic print dialog from pages
    * Only show one timeline per department, even if multiple load in/out exist per dept.
    * Fix bug where number of man hours were not present on previous pay period
    * Move office hours input errors to their respective entry
    * Marking estimates as concluded en masse now updates their respective gigs
    * Correctly show descriptions for addons (both db and individualized)
    * Add subcontracted equipment fees to estimates and invoices
    * Correct baseShiftFormset to correct for errors arising when attempting to DELETE overlapping shifts
    * Add validation to pricing to make sure there isn't overlapping pricing types for addons, systems, etc.
    * Allow Estimates to be viewed if not logged in on a Kiosk machine
    * Add subtotal to Subcontracted Equipment form
    * Update staffing store to fallback to first date work requested when not staffed (was reporting 0's)
    * Add line breaks between subcontracted equipment forms
    * Allow CORS for wiki support
    * Fix jquery formset to properly delete shifts
    * Fix error where URL Encode on login next screen dropped all get variables
    * Add useful errors to gigShift clock in/out
    * Add description to previous pay period shifts

### V2.3.0 - 05/18/2022
* Add Djangoql Admin Search
* Add DEBUG banner to admin
* Add ability to automatically sign forms using user signature
* Email sent when broken equipment report is filed
* Add action to restart the server via admin
* Add chosen/preferred name
* Contact info is now restricted to employees you are working a show with (not available to everyone on every showview)
* Added validation
    * Each system in gig must have a load in
    * Shifts cannot overlap for a given employee
    * Shifts cannot be a negative payout
* Wages now have dateframes that they are in effect
* Time Sheets are now available to employees electronically
* Time Sheets can now be signed electronically
* Make signup button more noticeable / add redirect on Shows page
* Add print tag
* Quickly mark time sheets as signed using Financial Overview
* Add barcode to timesheets
* Add timesheet quick process
* Add customized shift calendar ICS for all employees
* Systems and Addons can now adjust in price over time
* "Awaiting Paperwork" and "Cannot Work" groups are automatically added and removed based on paperwork status
* Move all fees to an inline and subclass prepared fees
* Allow fees to be sorted naturally
* Allow pricing of fees to change over time
* Improve code reuse/duplication
* Add equipment management (Kene)
* Add barcode field to Item
* Allow for multiple of same system to be booked (road to new booking equipment validation)
* Add pricing set validation
* Process timesheets on pay period submission if not previously processed
* Send email to FD when timesheet is auto-signed
* Add sent to payroll stamp
* Adding booking overview page
* Add event contact to showView
* Add children to items in inventory
* Add status' to items
* Add reservation number to estimate object
* Add billing contact signature to estimate
* Choose employees to send staffing email to (defaults to all)
* Booking page: Show gigs without estimate and highlight those less than 3 weeks out
* Add validation to Jobs in addition to Systems on Gigs to ensure load in/out
* Add Employee ID module
* Add search to Timesheet admin
* Update SA billing summary to include estimates where payment date is set to specific month/year
* Add DjangoQL search to Job Admin
* Add BSSL Bingo Board
* Add gig notes to staffing email
* Distinguish between graduation year and final year with BSSL (grad students)
* Add field to store final date of employment
* Add travel time required for venue (currently unused)
* Show outstanding balance in title of Estimates that are "Awaiting Payment" `eg. (OB: $100)`
<br><br>
BUG FIXES:
    * Fix formatting error in estimate signature box
    * Move 404 page to correct place
    * Wages would still have been overwritten due to Job-Wage relationship. Changed Wage date/pay structure
    * Updated outstandingpaperwork script to 
    * Adjust issue with upside down form filling
    * Log when employee signs paperwork
    * Move purchase date to unit not Equipment
    * Fix shift validation where person is not clocked out
    * WIP new summary processing w timesheets
    * Make finance widgets responsive
    * Fix summary table to expand with as many rates as paid
    * Fix formatting of setup time / view estimate to be more space efficient
    * Remove ordering from predefined fees (no longer needed with drag and drop)
    * Add manager notes to estimate admin
    * Fix issue with unassigned shift crashing showview
    * Fix inconsistent financial summary generation
    * Timesheet ID clears on enter when using quick action on finance page
    * Add all active rates to new finance summary page
    * Estimate would show first load out time, not last
    * Validation for overlapping shifts would only apply once a shift is entered. Locking the shift in.
    * Allow for an employee to work multiple Jobs in a shift and clock in/out appropriately 
    * SA Billing summary now sorted by group entry, not account #
    * Fix PayPeriod issue where shifts overlapping periods were unassigned.
    * Fix phantom login bug
    * Fix bug where FinanceShift crashed out (gracefully handled)
    * Sign Timesheet widget now fades background color to provide greater visual clarity
    * Fix bug where you had to save Estimate twice

### V2.2.0 - 12/2/2021
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
* Add DEV mode indicator for superusers
* Add Job pay rate validation directly to model
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
