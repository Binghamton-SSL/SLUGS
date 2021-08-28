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