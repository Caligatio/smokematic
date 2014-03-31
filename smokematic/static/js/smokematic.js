(function( skillet, $, undefined ) {
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
            console.log('Client notified socket has closed',event);
        };
    } 
}( window.smokematic = window.smokematic || {}, jQuery ));

$(function () {
    var data = {food_temp: [], pit_temp: [], blower_speed: [], setpoint: []};

    var options = {
        legend: {position: "sw"},
        xaxis: {mode: "time", timeformat: "%H:%M:%S"},
        yaxes: [
            {position: "left", min: 0, max: 350},
            {position: "right", min:0, max: 100}],
    };

    var plot = $.plot($("#graph"), [], options);

    smokematic.connect(function(event_data) {
        var dateObj = new Date();

        /* Localize the timestamps */
        time = dateObj.getTime() - dateObj.getTimezoneOffset() * 60 * 1000;

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
    // process the form
    $("#profile").submit(function(event) {

        // get the form data
        // there are many ways to get this data using jQuery (you can use the class or id also)
        var form_data = JSON.stringify(
            {
                "profile": {
                    0: $("#temperature").val()
                }
            }
        )
        console.log(form_data);

        $.ajax({
            type: 'PUT',
            url: '/profile',
            data: form_data,
            processData: false,
            contentType: "application/json",
            dataType: 'json'
        })
            // using the done promise callback
            .done(function(data) {

                // log data to the console so we can see
                console.log(data); 

                // here we will handle errors and validation messages
            });

        // stop the form from submitting the normal way and refreshing the page
        event.preventDefault();
    });
});

$(function() {
    // process the form
    $("#pid").submit(function(event) {

        // get the form data
        // there are many ways to get this data using jQuery (you can use the class or id also)
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
            // using the done promise callback
            .done(function(data) {

                // log data to the console so we can see
                console.log(data); 

                // here we will handle errors and validation messages
            });

        // stop the form from submitting the normal way and refreshing the page
        event.preventDefault();
    });
})
