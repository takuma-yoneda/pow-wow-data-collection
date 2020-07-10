var timestep = 0;  // store current timestep (globa var)
var port = 10080;
var MAX_TIMESTEPS = 800;
$(document).ready(function(){
    $("#left").click(function(){
        if (timestep > 0){
            timestep--;
            request_render(timestep, port);
            request_message(timestep, port);
            $("#step").val(timestep);
        }
    });

    $("#right").click(function(){
        console.log('timestep: '+ timestep);
        if (timestep <= MAX_TIMESTEPS){
            timestep++;
            request_render(timestep, port);
            request_message(timestep, port);
            $("#step").val(timestep);
        }
    });

    // $('#text').keypress(function (e) {
    //     let hostUrl= 'http://localhost:' + port + '/message';
    //     let message_val = $('#text').val();
    //     if (e.which == 13){
    //         console.log('catch enter keypress');
    //         send_message(hostUrl, message_val, username, agent_port);
    //         return false;
    //     }
    // });

    // $('#get_messages').click(
    //     function(){
    //         get_messages(already_visualized, username);
    //     });


    // $('#submit_send_message').click(
    //     function() {
    //         let hostUrl= 'http://localhost:8000/message';
    //         let message_val = $('#message_box').val();

    //         $('#message_box').val('');  // clear the text box
    //         console.log('message_val:', message_val);
    //         $.ajax({
    //             url: hostUrl,
    //             type:'POST',
    //             dataType: 'json',
    //             contentType: "application/json; charset=utf-8",
    //             data : JSON.stringify({message: message_val}),
    //             timeout:1000,
    //         }).done(function(data) {
    //             alert("ok");
    //             console.log(data);
    //         }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
    //             console.log(XMLHttpRequest, textStatus, errorThrown);
    //             alert("error");
    //         });
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


});

// function get_messages(already_visualized, username){
//     let hostUrl= 'http://localhost:' + port + '/get_messages';
//     console.log('get_messages is clicked');
//     $.ajax({
//         url: hostUrl,
//         type:'GET',
//         dataType:'json',
//         timeout:1000,
//     }).done(function(data) {
//         console.log(data);
//         parse_messages(data, already_visualized, username);
//     }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
//         // never put alert() here, because this will be called iteratively
//         console.log(XMLHttpRequest, textStatus, errorThrown);
//     });
// }


function request_message(timestep, port){
    console.log('request_message at timestep:' + timestep + '\t port:' + port);
    let hostUrl= 'http://localhost:' + port + '/get_messages';
    $.ajax({
        url: hostUrl,
        type:'POST',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data : JSON.stringify({timestep: timestep,
                              }),
        timeout:2000,
    }).done(function(data) {
        console.log(data);
        $('div.speech-display').empty();  // clear up the visualized messages
        visualize_messages(data);  // visualize messages
    }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
        console.log(XMLHttpRequest, textStatus, errorThrown);
        alert("error");
    });
}


function request_render(timestep, port){
    console.log('request_message at timestep:' + timestep + '\t port:' + port);
    let hostUrl= 'http://localhost:' + port + '/render';
    $.ajax({
        url: hostUrl,
        type:'POST',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data : JSON.stringify({timestep: timestep,
                              }),
        timeout:2000,
    }).done(function(data) {
        console.log(data);
    }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
        console.log(XMLHttpRequest, textStatus, errorThrown);
        alert("error");
    });
}

function visualize_messages(messages){
    sorted_keys = Object.keys(messages).sort();
    sorted_vals = sortObject(messages);
    console.log("SORTED KEYS!");
    console.log(sorted_keys);
    console.log(sorted_vals);
    for (let i=0; i < sorted_keys.length; i++){
        let timestep = sorted_keys[i];
        let messages = sorted_vals[timestep];

        insert_separator(timestep);
        for (let j=0; j < messages.length; j++){
            subject = (messages[j].agent_ip == "9000" ? "me":"theother");
            append_message(messages[j].message, subject);
        }
    }
    scroll_speech_display();
}

function scroll_speech_display(){
    $('.speech-display').animate({scrollTop: $('.speech-display')[0].scrollHeight});
}

function append_message(message, subject){
    let side = 'right';
    if(subject == "me"){
        side = 'left';
    }
    console.log("appendding message!");
    $(".box .speech-display").append('<div class="speech-item ' + side + '">'  + message + "</div>");

    // $('.speech-display').animate({scrollTop: $('.speech-display')[0].scrollHeight}, 'slow');
}

function insert_separator(timestep){
    console.log("insert_separator");
    // $(".box .speech-display").append('<div class="speech-item ' + side + '">'  + message + "</div>");
    $(".box .speech-display").append('<div class="strike"><span>TimeStep: ' + timestep + ' finished</span></div>');
    // $('.speech-display').animate({scrollTop: $('.speech-display')[0].scrollHeight}, 'slow');
}

// function parse_messages(messages, already_visualized, username){
//     // TEMP:
//     // temporary, just check the message at current timestep
//     current_timestep = messages.messages['current_timestep'];

//     // if next game is started, force reload the page
//     console.assert(current_timestep >= timestep);
//     // if (current_timestep < timestep && current_timestep == 0){
//     //     location.reload();  // force reload
//     // }

//     // insert separator
//     if (current_timestep > timestep){
//         insert_separator(timestep);
//     }
//     timestep = current_timestep; // update local timestep

//     // draw only if there's current_timestep message
//     console.log('messages:');
//     console.log(messages);
//     if (messages.messages.hasOwnProperty(current_timestep)){
//         current_messages = messages.messages[current_timestep];
//         console.log('--- parsing messages... ---');
//         console.log(current_messages);
//         for (let i = 0; i < current_messages.length; ++i){
//             let key_username = current_messages[i]['username'];
//             let message = current_messages[i]['message'];
//             let timestamp = current_messages[i]['timestamp'];
//             let hash = current_messages[i]['hash'];

//             if (key_username == username){
//                 // my own message
//                 if (!already_visualized.includes(hash)){
//                     append_message(message, 'me');
//                     already_visualized.push(hash);
//                 }
//             }else{
//                 // the other's message
//                 if (!already_visualized.includes(hash)){
//                     append_message(message, 'another');
//                     already_visualized.push(hash);
//                 }
//             }
//         }
//     }
// }


// From https://stackoverflow.com/a/29622653/7057866
function sortObject(obj) {
    return Object.keys(obj).sort().reduce(function (result, key) {
        result[key] = obj[key];
        return result;
    }, {});
}
