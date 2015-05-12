var net = require('net');

const CONNECT_RETRY = 5000;

var socket;
function connect() {
  socket = net.connect(41002, onConnect);
  socket.on('error', function(err) {
    setTimeout(connect, CONNECT_RETRY);
  });
}

function onConnect() {
  process.stdin.pipe(socket);

  /// For backwards compatibility with Node program older than v0.10,
  /// readable streams switch into "flowing mode" when a 'data' event handler
  /// is added, or when the pause() or resume() methods are called.
  process.stdin.on('data', function (buffer) {
    if (buffer.length === 1 && buffer[0] === 0x04) {  // EOT
      process.stdin.emit('end');  // process.stdin will be destroyed
      process.stdin.setRawMode(false);
      process.stdin.pause();  // stop emitting 'data' event
    }
  });

  /// this event won't be fired if REPL is exited by '.exit' command
  process.stdin.on('end', function () {
    console.log('.exit');
    socket.destroy();
  });

  socket.pipe(process.stdout);

  socket.on('connect', function () {
    console.log('Connected.');
    process.stdin.setRawMode(true);
  });

  socket.on('close', function close() {
    console.log('Disconnected, attempting to reconnect..');
    socket.removeListener('close', close);
    setTimeout(connect, CONNECT_RETRY);
  });
}

connect();
