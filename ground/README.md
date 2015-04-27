Vanguard Ground Station
---
A command line program that runs on a computer attached to an Xtend900, listening
for new messages from a Vanguard mission.

## Features

1. Logs incoming messages
2. Forwards position and telemetry messages to aprs.fi
3. Saves all messages to a local PouchDB

### Environment setup w/ nodejs v0.10.x+

        $ npm install

### Build system

* Stage code

        $ gulp

* Run the unit tests

        $ gulp test

* Run the ground station

        $ node dist/index.js [args]
