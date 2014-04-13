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
        var time = dateObj.getTime() - dateObj.getTimezoneOffset() * 60 * 1000;
        //console.log(event_data);
        if ("update" == event_data.type)
        {
            data.food_temp.push([time, event_data.data.food_temp[0]]);
            data.pit_temp.push([time, event_data.data.pit_temp]);
            data.setpoint.push([time, event_data.data.setpoint]);
            data.blower_speed.push([time, event_data.data.blower_speed]);

        }
        else
        {
            var max_time = -1;
            var times = [];
            data.food_temp = [];
            data.pit_temp = [];
            data.setpoint = [];
            data.blower_speed = [];

            $.each(event_data.data, function(key, value) {
                var key_int = parseInt(key);
                max_time = key_int > max_time ? key_int: max_time;
                times.push(key_int);
            });
            
            times.sort();

            $.each(times, function(time_offset) {
                var entry_time = time + ((time_offset - max_time) * 60 * 1000);
                var time_offset_str = String(time_offset);
                var data_item = event_data.data[time_offset_str];

                data.food_temp.push([entry_time, data_item.food_temp[0]]);
                data.pit_temp.push([entry_time, data_item.pit_temp]);
                data.setpoint.push([entry_time, data_item.setpoint]);
                data.blower_speed.push([entry_time, data_item.blower_speed]);
            });
        }
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
    /* Add onclick action for the Basting Settings button */
    $("#basteBtn").click(function() {
        /* Need to do an AJAX call to get the current basting settings */
        $.ajax({
            type: 'GET',
            url: '/baste',
            contentType: "application/json",
            dataType: 'json'
        })
        .done(function(data) {
            $('#basteFreq').val(data.data.frequency);
            $('#basteDur').val(data.data.duration);
            $('#basteModal').modal()
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
                //console.log(form_data);

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

    $("#basteForm")
        .submit(function(e){
            e.preventDefault()
        })
        .validate({
            rules: {
                basteFreq: {
                    number: true,
                    range: [0, 120],
                    required: true
                },
                basteDur: {
                    number: true,
                    range: [0, 10],
                    required: true
                }
            },
            messages: {
                basteFreq: "Frequency must be between 0 (disabled) and 120 minutes",
                basteDur: "Duration must be between 0 and 10 seconds"
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
                        "frequency": $("#basteFreq").val(),
                        "duration": $("#basteDur").val()
                    }
                )
                //console.log(form_data);

                $.ajax({
                    type: 'PUT',
                    url: '/baste',
                    data: form_data,
                    processData: false,
                    contentType: "application/json",
                    dataType: 'json'
                })
                .done(function(data) {
                    $('#basteModal').modal('hide');
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
