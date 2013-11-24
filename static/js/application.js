var inbox = new ReconnectingWebSocket("ws://"+ location.host + "/receive");
var outbox = new ReconnectingWebSocket("ws://"+ location.host + "/submit");

inbox.onmessage = function(message) {
  var data = JSON.parse(message.data);
  console.log(data);
  $("#twitter-stream").append("<div class='panel panel-default'><div class='panel-heading'>" + $('<span/>').text(data.handle||data.user.screen_name).html() + "</div><div class='panel-body'>" + $('<span/>').text(data.text).html() + "</div></div>");
  $("#twitter-stream").stop().animate({
    scrollTop: $('#twitter-stream')[0].scrollHeight
  }, 800);
};

inbox.onclose = function(){
    console.log('inbox closed');
    this.inbox = new WebSocket(inbox.url);
};

outbox.onclose = function(){
    console.log('outbox closed');
    this.outbox = new WebSocket(outbox.url);
};

$("#input-form").on("submit", function(event) {
  event.preventDefault();
  var handle = $("#input-handle")[0].value;
  var text   = $("#input-text")[0].value;
  outbox.send(JSON.stringify({ handle: handle, text: text }));
  $("#input-text")[0].value = "";
});

$("#track-form").on("submit", function(event) {
  event.preventDefault();
  var tracked = $("#track-text")[0].value;
  $.get('/twitterstream/track/' + tracked);
});

$("#start-stream").on('click', function() {
    $.get('/twitterstream/start/');
});

$("#stop-stream").on('click', function() {
    $.get('/twitterstream/stop/');
});

$("#clean-stream").on('click', function() {
    $("#twitter-stream").empty();
});
