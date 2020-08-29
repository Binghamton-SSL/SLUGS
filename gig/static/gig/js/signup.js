$(document).ready(function() {
    $('.uk-checkbox').change(function() {
        $.ajax({
            url:'/gigs/signup/',
            type:'post',
            data: JSON.stringify({"value":this.checked,"id":$(this).attr('id').split("-")[0]}),
            success: function (data) {
                console.log("test")
                if(data.status == 400) UIkit.notification({message: data.message, status: 'danger', pos: 'bottom-right','timeout': 1000}) 
                else if(data.status == 200) {
                    UIkit.notification({message: data.message, status: 'success', pos: 'bottom-right','timeout': 1000})
                }
            },
        })    
    });
});