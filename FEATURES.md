## Client
### Models
* Organization contact
* Organization

## Employee
### Models 
* Employee
* Office Hours
* Paperwork
* PaperworkForm (via to Paperwork and Employee)
### Admins
* Paperwork Admin/Inline
    * Search by form name
    * View employees assigned paperwork + status
* Employee Admin
    * Email notifications when account is activated/deactivated 
    * Email notifications when paperwork is assigned
    * Mass assign paperwork to employees
    * View and assign paperwork by employee
* Office Hours
### Views
* Account Signup
* User overview
    * View account info / paperwork / shifts + payroll
    * Upload and automatically sign paperwork
* Office hours
    * Submit and view unprocessed office hours
    * Support for multiple office hour rates for one employee
* User change password

## Equipment
### Models
* System
* System Addon
* Broken Equipment Report
    * Email shop techs on broken equipment
### Views
* Report broken equipment
### Admins
* System Addon
* System
* Broken equipment report
    * Log and investigate issues

## Finance
### Models
* Wage
* Fee
* One Time Fee
* Estimate
* Canned Notes
* Shift
* PayPeriod
* Payment
### Views
* View Estimates
* View Invoices
* View Timesheets
* View Payroll Summaries
* Export Payroll Summary as CSV
* View SA Billing Summary
* View and Approve shifts
    * Approve all shifts at once
### Admins
* Wages
* Shifts
    * Roll over shift to another pay period
* One Time Fee Inline
* Fee Admin
* Payment (Inline Only)
* Estimate
    * Mass update status
* Pay Period
    * Print Timesheets + Payroll Summary
* Canned Notes

## Gig 
### Models
* Gig
    * Send staffing emails
    * Staff show
* Load in
* System Instance (via to System and Gig)
* Addon Instance (via to Addon and Gig)
* Job
* JobInterest
### Views
* Showview page
    * See information about show
    * See employees working show
    * Fill out digital day of show
        * Non engineer clock in
* Signup for work
* See all shows
### Admin
* Job (Inline, Sub Inline, Admin)
* Job Interest
* Addon Inline
* System Inline
* Loadin (Inline Only)
* Gig

## Location
### Model
* Location
### Admin
* Location

## Training
### Models
* Training
* Trainee
    * Trainees can be paid via a shift
* Training Request
### Views
* See available sessions
* Request training on any system
    * Send email when training session requested
### Admins
* Training Request 
* Trainee (Inline + Admin)
* Training


## Admin
### Quick actions
* Open/close onboarding
* Open/close signup
* restart server
### Data
* Employees who have not signed in in over a week
* Employees who never signed in