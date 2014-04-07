(function(smokematic, $, undefined) {
    var infoCallback = null;
    
    smokematic.connect = function(callback) {
        infoCallback = callback;
        var socket = new WebSocket('ws://'+document.location.host+'/status');
        
        socket.onmessage = function(event) {
            //console.log('Client received a message',event);
            infoCallback(JSON.parse(event.data));
        };
	
        // Listen for socket closes
        socket.onclose = function(event) {
            //console.log('Client notified socket has closed', event);
        };
    } 
}(window.smokematic = window.smokematic || {}, jQuery));

$(function () {
    var data = {food_temp: [], pit_temp: [], blower_speed: [], setpoint: []};

    var options = {
        legend: {position: "sw"},
        xaxis: {mode: "time", timeformat: "%H:%M:%S", axisLabel: "Time"},
        yaxes: [
            {position: "left", min: 0, max: 400, axisLabel: "Temperature"},
            {position: "right", min:0, max: 100, axisLabel: "Percentage"}],
    };

    var plot = $.plot($("#graph"), [], options);

    smokematic.connect(function(event_data) {
        var dateObj = new Date();

        /* Localize the timestamps */
        time = dateObj.getTime() - dateObj.getTimezoneOffset() * 60 * 1000;

        console.log(event_data);
        data.food_temp.push([time, event_data.food1_temp]);
        data.pit_temp.push([time, event_data.pit_temp]);
        data.setpoint.push([time, event_data.setpoint]);
        data.blower_speed.push([time, event_data.blower_speed]);

        plot.setData([
            {yaxis: 1, data: data.pit_temp, label: "Pit Temp"},
            {yaxis: 1, data: data.food_temp, label: "Food Temp"},
            {yaxis: 1, data: data.setpoint, label: "Setpoint Temp"},
            {yaxis: 2, data: data.blower_speed, label: "Blower Speed"}])
        plot.setupGrid()
        plot.draw();
    })
});

$(function() {
    /* Add onclick action for the Cooking Profile->New button */
    $("#newProfileBtn").click(function() {
        $('#newProfileModal').modal()
    });
    /* Add onclick action for the Temperature Override button */
    $("#tempOverrideBtn").click(function() {
        /* Need to do an AJAX call to check whether smoker is in override mode */
        $.ajax({
            type: 'GET',
            url: '/override',
            contentType: "application/json",
            dataType: 'json'
        })
        .done(function(data) {
            if (data.data.override == true) {
                $('#tempResumeBtn').show();
                $('#temperature').val(data.data.temperature);
            }
            else
            {
                $('#tempResumeBtn').hide();
                $('#temperature').val(null);
            }

            $('#tempModal').modal()
            //console.log(data); 
        });
    });
    /* Add onclick action for the PID Tweaks button */
    $("#pidTweaksBtn").click(function() {
        $.ajax({
            type: 'GET',
            url: '/pid',
            contentType: "application/json",
            dataType: 'json'
        })
        .done(function(data) {
            $('#k_p').val(data.data.coefficients.p);
            $('#k_i').val(data.data.coefficients.i);
            $('#k_d').val(data.data.coefficients.d);

            $('#pidModal').modal()
            //console.log(data); 
        })
    });

    /* Add onclick action for the "Resume Profile" button */
    $("#tempResumeBtn").click(function() {
        $.ajax({
            type: 'DELETE',
            url: '/override',
            dataType: 'json'
        })
        .done(function(data) {
            $('#tempModal').modal('hide');
            $("#temperature").closest('.form-group').removeClass('has-success');
            //console.log(data); 
        });

    });

    $("#pidForm")
        .submit(function(e){
            e.preventDefault()
        })
        .validate({
            rules: {
                k_p: {
                    number: true,
                    required: true
                },
                k_i: {
                    number: true,
                    required: true
                },
                k_d: {
                    number: true,
                    required: true
                }
            },
            highlight: function (element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
            },
            unhighlight: function (element) {
                $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
            },
            errorClass: 'help-block',
            submitHandler: function(form){
                var form_data = JSON.stringify(
                    {
                        "coefficients": {
                            p: $("#k_p").val(),
                            i: $("#k_i").val(),
                            d: $("#k_d").val()
                        }
                    }
                )
                console.log(form_data);

                $.ajax({
                    type: 'PUT',
                    url: '/pid',
                    data: form_data,
                    processData: false,
                    contentType: "application/json",
                    dataType: 'json'
                })
                .done(function(data) {
                    $('#pidModal').modal('hide');
                    //console.log(data); 
                });
            }
        })
    
    $("#newProfileForm")
        .submit(function(e){
            e.preventDefault()
        })
        .validate({
            rules: {
                newProfile:{
                    required: true
                }
            },
            highlight: function (element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
            },
            unhighlight: function (element) {
                $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
            },
            errorClass: 'help-block',
            submitHandler: function(form){
                var form_data = JSON.stringify(
                    {
                        "profile": JSON.parse($("#newProfile").val())
                    }
                )
                //console.log(form_data);

                $.ajax({
                    type: 'PUT',
                    url: '/profile',
                    data: form_data,
                    processData: false,
                    contentType: "application/json",
                    dataType: 'json'
                })
                .done(function(data) {
                    $('#newProfileModal').modal('hide');
                    //console.log(data); 
                });
            }
        })    

    $("#tempForm")
        .submit(function(e){
            e.preventDefault()
        })
        .validate({
            rules: {
                temperature:{
                    number: true,
                    range: [0, 500],
                    required: true
                }
            },
            messages: {
                temperature: "Temperature must be 0-500 degrees"
            },
            highlight: function (element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
            },
            unhighlight: function (element) {
                $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
            },
            errorClass: 'help-block',
            errorPlacement: function(error, element) {
                if(element.parent('.input-group').length) {
                    error.insertAfter(element.parent());
                } else {
                    error.insertAfter(element);
                }
            },
            submitHandler: function(form){
                var form_data = JSON.stringify(
                    {
                        "temperature": $("#temperature").val()
                    }
                )
                //console.log(form_data);

                $.ajax({
                    type: 'PUT',
                    url: '/override',
                    data: form_data,
                    processData: false,
                    contentType: "application/json",
                    dataType: 'json'
                })
                .done(function(data) {
                    $('#tempModal').modal('hide');
                    //console.log(data); 
                });
            }
        })
})