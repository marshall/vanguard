package com.arcaner.vanguard;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

public class SmsReceiver extends BroadcastReceiver {
    private static final String TAG = "SmsReceiver";

    private VanguardMain mVanguardMain;

    public SmsReceiver(VanguardMain vanguardMain) {
        mVanguardMain = vanguardMain;
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        Bundle extras = intent.getExtras();
        if (extras != null) {
            Object[] smsExtras = (Object[]) extras.get("pdus");
            for (int i = 0; i < smsExtras.length; i++) {
                SmsMessage smsMsg = SmsMessage.createFromPdu((byte[]) smsExtras[i]);
                String strMsgBody = smsMsg.getMessageBody().toString();
                String strMsgSrc = smsMsg.getOriginatingAddress();

                Log.i(TAG, "SMS from " + strMsgSrc + " : " + strMsgBody);
                mVanguardMain.onTextReceived(strMsgBody, strMsgSrc);
            }
        }
    }

}
