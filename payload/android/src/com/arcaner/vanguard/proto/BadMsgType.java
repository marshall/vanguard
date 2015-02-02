package com.arcaner.vanguard.proto;

public class BadMsgType extends Exception {
    public BadMsgType(int msgType) {
        super(String.format("Bad message type %d", msgType));
    }
}
