import _ from 'lodash';
import log from './log';
import path from 'path';
import fs from 'fs';
import PouchDB from 'pouchdb';
import PouchDB_upsert from 'pouchdb-upsert';

PouchDB.plugin(PouchDB_upsert);

export default class TrackDB {
  constructor(station, options) {
    let vgDir = path.join(process.env.HOME, '.vanguard');

    if (!fs.existsSync(vgDir)) {
      fs.mkdirSync(vgDir);
    }

    this.db = {};

    ['location', 'telemetry', 'photo-data'].forEach(db => {
      this.db[db] = new PouchDB(db, { prefix: vgDir + '/' });
      if (options.remoteURL) {
        this.syncDB(this.db[db], options.remoteURL + '/' + db);
      }
    });

    station.on('message', doc => { this.postDocument(doc) });
  }

  syncDB(localDB, remoteURL) {
    let remoteDB = new PouchDB(remoteURL);
    localDB.sync(remoteDB, { live: true, retry: true })
           .on('paused', info => {
             //log.info('replication paused for', remoteURL);
           })
           .on('active', info => {
             //log.info('replication active for', remoteURL);
           })
           .on('error', err => {
             log.info('replication error for', remoteURL, err);
           });
  }

  postDocument(doc) {
    let db = this.db[doc.type];
    if (!db) {
      log.warn('Unknown message type', doc.type);
      return;
    }

    if (doc.type === 'photo-data') {
     doc._attachments = {
        'data': {
          content_type: 'image/jpeg',
          data: doc.data
        }
      };
      delete doc.data;
    }

    var promise = db.post(doc);
    promise.catch(function(err) {
      log.error(err);
    });

    return promise;
  }
};
