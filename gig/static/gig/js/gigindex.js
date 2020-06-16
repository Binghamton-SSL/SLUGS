$(document).ready(()=>{
})
var new_rows = 0
add_row = (name,emp_id) => {
    $(`
        <tr>
            <td>`+name+`</td>
            <td>
                <input name="e-`+ emp_id +`-in-`+ new_rows +`" class="uk-input" type="datetime-local"/>
            </td>
            <td>
                <input name="e-`+ emp_id +`-out-`+ new_rows +`" class="uk-input" type="datetime-local"/>
            </td>
            <td>
            </td>
        </tr>
    `).insertBefore( "#add_new-"+emp_id );
    new_rows++
}