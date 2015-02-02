package com.arcaner.vanguard;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;
import android.view.WindowManager;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String TAG = "Main";
    public static final int PHOTO_RESULT = 10;

    private long mBegin = System.currentTimeMillis();
    private Handler mPhotoHandler;
    private int mPhotoHandlerMsg;
    private BluetoothServer mBtServer;
    private VanguardMain mVanguardMain;
    private Handler mHandler;

    public void setPhotoHandler(Handler handler, int msgType) {
        mPhotoHandler = handler;
        mPhotoHandlerMsg = msgType;
    }

    public void takePhoto() {
        Intent intent = new Intent(this, DroidCamera.class);
        startActivityForResult(intent, PHOTO_RESULT);
    }

    private TextView findTextView(int id) {
        return (TextView) findViewById(id);
    }

    private void setTextViewText(int id, String format, Object... args) {
        TextView textView = findTextView(id);
        if (textView != null) {
            textView.setText(String.format(format, args));
        } else {
            Log.e(TAG, "Invalid TextView: " + id);
        }
    }

    public void updateUI(final int photos, final boolean btConnected, final int battery, final int cellSignal, final String diskAvailable) {
        runOnUiThread(new Runnable() {
            public void run() {
                setTextViewText(R.id.photos_label, Integer.toString(photos));

                TextView connectedLabel = findTextView(R.id.connected_label);
                connectedLabel.setText(btConnected ? R.string.connected_yes : R.string.connected_no);
                connectedLabel.setTextColor(getResources().getColor(btConnected ? R.color.connected_yes : R.color.connected_no));

                long uptime = System.currentTimeMillis() - mBegin;
                long uptimeSecs = uptime / 1000;
                int hours = (int) uptimeSecs / 3600;
                int hrSecs = hours * 3600;
                int minutes = (int) (uptimeSecs - hrSecs) / 60;
                int seconds = (int) uptimeSecs - hrSecs - (minutes * 60);

                setTextViewText(R.id.uptime_label, "%02d:%02d:%02d", hours, minutes, seconds);
                setTextViewText(R.id.battery_label, "%d%%", battery);
                setTextViewText(R.id.cell_label, "%d%%", cellSignal);
                setTextViewText(R.id.disk_free, diskAvailable);
            }
        });
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);
        mVanguardMain = new VanguardMain(this, null);
        mVanguardMain.start();
        //mBtServer = new BluetoothServer(this);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mBtServer != null) {
            mBtServer.shutdown();
            mBtServer = null;
        }
        if (mVanguardMain != null) {
            mVanguardMain.shutdown();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == PHOTO_RESULT) {
            Message msg = Message.obtain(mPhotoHandler, mPhotoHandlerMsg);
            msg.arg1 = resultCode;
            msg.setData(data.getExtras());
            msg.sendToTarget();
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

}