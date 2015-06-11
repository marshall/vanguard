var child_process = require('child_process');
child_process.exec('cat ./__init__.py', function (err, stdout, stderr){
    console.log(stdout);
});