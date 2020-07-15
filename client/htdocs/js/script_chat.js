var timestep = 0;  // store current timestep (globa var)
var port = 8000;
var username;
var agent_port;
var on_game = false;
var resetted = false;
var already_visualized = [];
$(document).ready(function(){
    agent_port = $("span#agent_port").text();
    user_input_dialog();

    // Static event handlers
    $('#submit').on('click', function(){
        let hostUrl= 'http://localhost:' + port + '/message';
        let message_val = $('#text').val();
        // console.log('submit botton is clicked ;)');
        send_message(hostUrl, message_val, username, agent_port);
    });

    $('#text').on('keypress', function (e) {
        let hostUrl= 'http://localhost:' + port + '/message';
        let message_val = $('#text').val();
        // catch enter key press
        if (e.which == 13){
            send_message(hostUrl, message_val, username, agent_port);
        }
    });

    $(window).on("blur focus", function(e) {
        var prevType = $(this).data("prevType");

        if (prevType != e.type) {   //  reduce double fire issues
            switch (e.type) {
            case "blur":
                $('body').removeClass("overlay");
                $('body').addClass("overlay");
                break;
            case "focus":
                $('body').removeClass("overlay");
                break;
            }
        }

        $(this).data("prevType", e.type);
    });

    // continuously checks if the game is going on or not
    poll(function() {
        check_if_on_game();  // this changes game_is_started to True when the game is started.
        return false;
    }, Infinity, 1000).then(function() {
    }).catch(function(err) {
        // Polling timed out, handle the error!
        console.log(err);
    });

    // continuously get messages.
    poll(function() {
        if (on_game){
            get_messages(already_visualized, username, agent_port);
            resetted = false;
        }else{
            // prevent reset from running again and again.
            if (!resetted){
                console.log('Reset is called because on_game is false (' + on_game + ')');
                reset();
                resetted = true;
            }
        }
        return false;
    }, Infinity, 500).then(function() {
        // Polling done, now do something else!
        // reset everything
        console.log('Game is done! reset everything!!');
        console.log('Reset is called because polling for get_message is done (something is wrong) (' + on_game + ')');
        setTimeout(function(){
            reset();
            resetted = true;
        }, 800);

    }).catch(function(err) {
        // Polling timed out, handle the error!
        console.log(err);
    });

});

function user_input_dialog(){
    $( "#dialog" ).dialog({
        dialogClass: "no-close",
        draggable: false,
        modal:true,
        width: 500,
        buttons: [
            {
                text: "Play",
                // icon: "ui-icon-submit",
                click: function() {
                    username = $("#username").val();
                    // let age = $("#age").val();
                    // let played_bomberman = $("#played_bomberman option:selected").val();
                    // let is_native_speaker = $("#native_speaker option:selected").val();
                    let age = "-1";
                    let played_bomberman = "no";
                    let is_native_speaker = "no";

                    if (username != "" && age != ""){
                        $( this ).dialog( "close" );
                        $("#dialog-waiting").dialog("open");
                        // submit_to_sheet(username, age, is_native_speaker, played_bomberman);
                        waiting_dialog();

                    }
                }
                // Uncommenting the following line would hide the text,
                // resulting in the label being used as a tooltip
                //showText: false
            }
        ]
    });

    $("#dialog-waiting").dialog({
        autoOpen: false,
        dialogClass: "no-close",
        draggable: false,
        modal:true,
        width: 500,
        buttons: [
            {
                text: "Quit",
                // icon: "ui-icon-submit",
                click: function() {
                    $('#dialog-waiting').dialog('close');
                    unready_to_start(); // reset will be called inside.

                }
                // Uncommenting the following line would hide the text,
                // resulting in the label being used as a tooltip
                //showText: false
            }
        ]
    });
}

function waiting_dialog(){
    ready_to_start();

    // polling ;)
    poll(function() {
        if (on_game){
            console.log("game is started!!");
            return true;
        }else{
            return false;
        }
    }, Infinity, 1000).then(function() {
        // Polling done, now do something else!
        $("#dialog-waiting p").html("Waiting for the Game Server...<br>(It will take ~10 seconds.)");

        // Intentionaly delay closing waiting dialog
        setTimeout(function() {
            $("#dialog-waiting").dialog("close");
            main(username);
        }, 5000);
    }).catch(function(err) {
        // Polling timed out, handle the error!
        console.log(err);
    });
}

function ready_to_start(){
    let hostUrl= 'http://localhost:' + agent_port + '/ready_to_start';
    $.ajax({
        url: hostUrl,
        type:'GET',
        dataType:'json',
        timeout:800,
        retryLimit: 10,
        success: function(data) {
            // console.log(data);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            // retry Ajax: https://stackoverflow.com/a/10024557
            console.log(XMLHttpRequest, textStatus, errorThrown);
            this.retryLimit--;
            if(this.retryLimit > 0){
                console.log('retrying (remaining: ' + this.retryLimit + ') request to ' + hostUrl );
                // NOTE: anonymous func doesn't work because 'this' will point to a wrong object.
                // setTimeout(function() {$.ajax(this); }, 500);
                setTimeout(() => {$.ajax(this);}, 1000);
                return;
            }else{
                // Error
                alert("Connection Error (Hint: client.py might not be running.)");
                reset();
                resetted = true;
            }
        }
    });
}

function unready_to_start(){
    let hostUrl= 'http://localhost:' + agent_port + '/unready_to_start';
    $.ajax({
        url: hostUrl,
        type:'GET',
        dataType:'json',
        timeout:800,
        retryLimit: 3,
        success: function(data) {
            reset();
            resetted = true;
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            // retry Ajax: https://stackoverflow.com/a/10024557
            console.log(XMLHttpRequest, textStatus, errorThrown);
            this.retryLimit--;
            if(this.retryLimit > 0){
                console.log('retrying (remaining: ' + this.retryLimit + ') request to ' + hostUrl );
                // NOTE: anonymous func doesn't work because 'this' will point to a wrong object.
                // setTimeout(function() {$.ajax(this); }, 500);
                setTimeout(() => {$.ajax(this);}, 1000);
                return;
            }else{
                // Error
                alert("Connection Error (Hint: client.py might not be running.)");
                reset();
                resetted = true;
            }
        }
    });
}

function main(username){
    $("#username_placeholder").text(username);

    console.log(username);

    console.log("agent_port", agent_port);



    // $('#get_messages').click(
    //     function(){
    //         get_messages(already_visualized, username);
    //     });

    // $('#increment').click(
    //     function() {
    //         let hostUrl= 'http://localhost:' + port + '/increment';
    //         $.ajax({
    //             url: hostUrl,
    //             type:'GET',
    //             dataType:'json',
    //             timeout:1000,
    //         }).done(function(data) {
    //             alert("ok");
    //             console.log(data);
    //         }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
    //             console.log(XMLHttpRequest, textStatus, errorThrown);
    //             alert("error");
    //         });
    //     });
}

function reset(){
    console.log('reset is called');
    username = '';
    already_visualized = [];
    on_game = false;
    $('.speech-display').empty();
    $('.submit-area #text').val('');
    $('#username_placeholder').empty();
    $('#username').val('');
    $('#age').val('');
    $('#dialog-waiting').dialog('close');
    $("#dialog-waiting p").html("Waiting for the other player...");
    user_input_dialog();
}

// function check_if_game_started(){
//     // this changes game_is_started to true in an appropriate timing.
//     let hostUrl= 'http://localhost:' + port + '/is_on_game';
//     $.ajax({
//         url: hostUrl,
//         type:'GET',
//         dataType:'json',
//         timeout:800,
//     }).done(function(data) {
//         game_is_started =  data.result;
//     }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
//         // never put alert() here, because this will be called iteratively
//         console.log(XMLHttpRequest, textStatus, errorThrown);
//         game_is_started = false;
//     });
// }

function check_if_on_game(){
    // this changes game_is_started to true in an appropriate timing.
    let hostUrl= 'http://localhost:' + port + '/is_on_game';
    $.ajax({
        url: hostUrl,
        type:'GET',
        dataType:'json',
        timeout:800,
    }).done(function(data) {
        on_game =  !!data.result;  // force it to be a boolean
    }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
        // never put alert() here, because this will be called iteratively
        console.log(XMLHttpRequest, textStatus, errorThrown);
        console.log("is_on_game did not respond... This is not supposed to happen.");
        // on_game = false;
    });
}

function get_messages(already_visualized, username){
    let hostUrl= 'http://localhost:' + port + '/get_messages';
    console.log('get_messages is clicked');
    $.ajax({
        url: hostUrl,
        type:'GET',
        dataType:'json',
        timeout:1000,
    }).done(function(data) {
        // console.log(data);
        parse_messages(data, already_visualized, username);
    }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
        // never put alert() here, because this will be called iteratively
        console.log(XMLHttpRequest, textStatus, errorThrown);
    });
}


function send_message(hostUrl, message_val, username, agent_ip){
    $('#text').val('');  // clear the text box
    console.log('submit_message');
    console.log('username: ', username);
    console.log('message_val: ', message_val);
    $.ajax({
        url: hostUrl,
        type:'POST',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data : JSON.stringify({message: encodeURIComponent(message_val),
                               username: username,
                               agent_ip: agent_ip,
                              }),
        timeout:1000,
    }).done(function(data) {
        console.log(data);
        // append_message(message_val, 'system');  // append message
    }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
        console.log(XMLHttpRequest, textStatus, errorThrown);
        console.log("Connection Error: (send_message failed.)");
        // alert("Connection Error: (Hint: message server may not be running)");
        // reset();
    });
}

function append_message(message, subject){
    let side = 'right';
    if(subject == "me"){
        side = 'left';
    }
    // console.log("appendding message!");
    $(".box .speech-display").append('<div class="speech-item ' + side + '">'  + message + "</div>");

    $('.speech-display').animate({scrollTop: $('.speech-display')[0].scrollHeight}, 'slow');
}

function insert_separator(timestep){
    // console.log("insert_separator");
    // $(".box .speech-display").append('<div class="speech-item ' + side + '">'  + message + "</div>");
    $(".box .speech-display").append('<div class="strike"><span>TimeStep: ' + timestep + ' finished</span></div>');
    $('.speech-display').animate({scrollTop: $('.speech-display')[0].scrollHeight}, 'slow');
}

function parse_messages(messages, already_visualized, username){
    // TEMP:
    // temporary, just check the message at current timestep
    current_timestep = messages.messages['current_timestep'];

    // if next game is started, force reload the page
    console.assert(current_timestep >= timestep);
    // if (current_timestep < timestep && current_timestep == 0){
    //     location.reload();  // force reload
    // }

    // insert separator
    if (current_timestep > timestep){
        insert_separator(timestep);
    }
    timestep = current_timestep; // update local timestep

    // draw only if there's current_timestep message
    // console.log('messages:');
    // console.log(messages);
    if (messages.messages.hasOwnProperty(current_timestep)){
        current_messages = messages.messages[current_timestep];
        // console.log('--- parsing messages... ---');
        // console.log(current_messages);
        for (let i = 0; i < current_messages.length; ++i){
            let key_username = current_messages[i]['username'];
            let message = current_messages[i]['message'];
            let timestamp = current_messages[i]['timestamp'];
            let hash = current_messages[i]['hash'];

            if (key_username == username){
                // my own message
                if (!already_visualized.includes(hash)){
                    append_message(message, 'me');
                    already_visualized.push(hash);
                }
            }else{
                // the other's message
                if (!already_visualized.includes(hash)){
                    append_message(message, 'another');
                    already_visualized.push(hash);
                }
            }
        }
    }
}

// https://davidwalsh.name/javascript-polling
// The polling function
function poll(fn, timeout, interval) {
    var endTime = Number(new Date()) + (timeout || 2000);
    interval = interval || 100;

    var checkCondition = function(resolve, reject) {
        // If the condition is met, we're done!
        var result = fn();
        if(result) {
            resolve(result);
        }
        // If the condition isn't met but the timeout hasn't elapsed, go again
        else if (Number(new Date()) < endTime) {
            setTimeout(checkCondition, interval, resolve, reject);
        }
        // Didn't match and too much time, reject!
        else {
            reject(new Error('timed out for ' + fn + ': ' + arguments));
        }
    };

    return new Promise(checkCondition);
}


// // Usage:  ensure element is visible
// poll(function() {
// 	return document.getElementById('lightbox').offsetWidth > 0;
// }, 2000, 150).then(function() {
//     // Polling done, now do something else!
// }).catch(function() {
//     // Polling timed out, handle the error!
// });
