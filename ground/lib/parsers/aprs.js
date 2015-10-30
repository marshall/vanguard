import _ from 'lodash';
import assert from 'assert';
import BufferOffset from 'buffer-offset';
import crc32 from 'buffer-crc32';
import Dissolve from 'dissolve';
import { Transform } from 'stream';
import util from 'util';
import Buffer from 'buffer';


//vanguard APRS protocol packets have fixed length data format
export const MULTIMON_PREFIX_SIZE     = 26; //The Callsign and other data prefixed to the message content
export const MSG_TYPE_LOCATION        = 1;
export const MSG_TYPE_TELEMETRY       = 2;
export const POSITION_DATA_LENGTH     = 43; 
export const TELEMETRY_DATA_LENGTH    = 34;
export const BASE_URL                 = ' https://www.google.com/maps?z=12&t=m&q=loc:';

export class Parser extends Dissolve {
  constructor() {
    super();
    this.discard = '';
    this.loop(end => {
      this.parse();
    });
  }

  parse() {
    this.string('begin', 1).tap(() => {
      if (this.vars.begin === 'A') {
        this.string('next',4).tap(() => {
          if(this.vars.next === 'PRS:'){
            this.parseHeader();
          }
        });
      }else{
        this.discard += String.fromCharCode(this.vars.begin >> 40);
        this.discard += String.fromCharCode(this.vars.begin & 0xff);
        return;
      }

      if (this.discard.length > 0) {
        this.discard = '';
      }
    });
  }

  parseHeader(){
    this.string('header', MULTIMON_PREFIX_SIZE);
    this.string('type', 1).tap(()=> {
      if (this.vars.type === '/'){
        this.vars.type = 'location';
        this.parsePosition();
      }else if (this.vars.type === 'T'){
        this.vars.type = 'telemetry';
        this.parseTelemtety();
      }
    });
  }

  parseTelemtety(){
    this.string('data', TELEMETRY_DATA_LENGTH - 1).tap(() => {
      this.tapTelemetry();
    })
  }

  parsePosition(){
      this.string('data', POSITION_DATA_LENGTH - 1).tap(() => {
        this.tapPosition();
    })
  }

  tapTelemetry(){
    let strArray = this.vars.data.split(',');
    this.vars.packetId = strArray[0];
    this.vars.intTemp  = strArray[1];
    this.vars.extTemp  = strArray[2];
    this.vars.cpu      = strArray[3];
    this.vars.freeMem  = strArray[4];
    this.vars.uptime   = strArray[5];
    this.vars.d        = strArray[6]; //unused right now
    let data = _.omit(this.vars, 'next', 'header', 'data', 'begin');
    super.push(data) 
    this.vars = {};
  }

  tapPosition(){
    let expr = /h|O|\//g;   //fixed field format and deliminators in the APRS Prototcol.
    let strArray = this.vars.data.split(expr);
    this.vars.time   = strArray[0];
    this.vars.lat    = strArray[1].replace(/\D/g,''); // remove n
    this.vars.lon    = strArray[2].replace(/\D/g,''); // remove w
    this.vars.course = strArray[3];
    this.vars.speed  = strArray[4];
    this.vars.alt    = strArray[5].replace(/\D/g,''); //remove A
    this.addMapLink();
  }

  addMapLink(){ //add the google map link to coordnates
    this.vars.lon = this.vars.lon/-10000; // negative to account for western hemisphere.
    this.vars.lat = this.vars.lat/10000 ; 
    this.vars.url = BASE_URL + this.vars.lat + '+' + this.vars.lon; 
    let data = _.omit(this.vars, 'next', 'header', 'data', 'begin');
    super.push(data);
    this.vars = {};
  }
}


