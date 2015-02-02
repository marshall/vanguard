package com.arcaner.vanguard;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.UUID;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.util.Log;

import com.arcaner.vanguard.proto.AddPhoneNumber;
import com.arcaner.vanguard.proto.ProtoMessage;
import com.arcaner.vanguard.proto.ProtoMessageReader;
import com.arcaner.vanguard.proto.SendText;
import com.arcaner.vanguard.proto.StartPhotoData;
import com.arcaner.vanguard.proto.StopPhotoData;

public class BluetoothServer implements Runnable {
    private static final String TAG          = "VANGUARD-BT";
    private static final String SERVICE_NAME = "vanguard service";
    private static final UUID SERVICE_UUID   = UUID.fromString("de746609-6dbf-4917-9040-40d1d2ce9c79");
    private static final long SERVER_CREATE_TIMEOUT = 1000 * 60;
    private static final long MSG_READ_INTERVAL = 3000L;

    private BluetoothServerSocket mBtServer;
    private BluetoothConnection mConnection;
    private BluetoothAdapter mBtAdapter;
    private VanguardMain mVanguardMain;
    private boolean mRunning = false;

    public BluetoothServer(MainActivity context, VanguardMain vanguardMain) {
        mConnection = new BluetoothConnection();

        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            mBtAdapter = BluetoothAdapter.getDefaultAdapter();
        } else {
            mBtAdapter = (BluetoothAdapter) context
                    .getSystemService("bluetooth");
        }

        mVanguardMain = vanguardMain;
        new Thread(this, TAG).start();
    }

    public void shutdown() {
        mRunning = false;

        if (mBtServer != null) {
            try {
                mBtServer.close();
            } catch (IOException e) {
            }
        }


        if (mConnection != null) {
            mConnection.shutdown();
        }

        mBtAdapter = null;
        mConnection = null;
    }

    public boolean isConnected() {
        return mConnection != null && mConnection.isConnected();
    }

    public void writeMessage(ProtoMessage message)
    {
        if (mConnection == null || mConnection.getHandler() == null) {
            return;
        }

        byte[] copy = new byte[message.getBufferLen()];
        ByteBuffer buf = message.getBuffer();
        buf.mark();
        buf.position(0);
        buf.get(copy);
        buf.reset();

        Message msg = mConnection.getHandler().obtainMessage(BluetoothConnection.MSG_WRITE_MSG, copy);
        msg.sendToTarget();
    }

    private boolean ensureServerRunning() {
        if (mBtServer != null) {
            return true;
        }

        try {
            mBtServer = mBtAdapter.listenUsingRfcommWithServiceRecord(SERVICE_NAME, SERVICE_UUID);
            return true;
        } catch (IOException e) {
            Log.e(TAG, "error setting up bt server", e);
        }

        return false;
    }

    public void run() {
        mRunning = true;
        while (mRunning) {
            try {
                if (!ensureServerRunning()) {
                    Thread.sleep(SERVER_CREATE_TIMEOUT);
                    continue;
                }

                BluetoothSocket socket = mBtServer.accept();
                if (socket == null) {
                    continue;
                }

                mConnection.setBluetoothSocket(socket);
                mConnection.ensureRunning();
            } catch (IOException e) {
                Log.e(TAG, "error accepting", e);
            } catch (InterruptedException e) {}
        }
    }

    private class BluetoothConnection extends Thread {
        private static final String TAG = "VANGUARD-BTCONN";
        private static final int MSG_MAYBE_READ_MSG = 1000;
        private static final int MSG_WRITE_MSG      = 1001;

        private InputStream mIn;
        private OutputStream mOut;
        private BluetoothSocket mSocket;
        private ProtoMessageReader mReader = new ProtoMessageReader();
        private boolean mRunning = false;
        private Handler mHandler;

        public void setBluetoothSocket(BluetoothSocket socket) {
            if (mSocket != null) {
                try {
                    mSocket.close();
                } catch (IOException e) {
                }
            }

            mSocket = socket;
            try {
                mIn = mSocket.getInputStream();
                mOut = mSocket.getOutputStream();
            } catch (IOException e) {
                Log.e(TAG, "error getting streams", e);
            }
        }

        public void ensureRunning() {
            if (!mRunning) {
                new Thread(this, TAG).start();
            }
        }

        public boolean isConnected() {
            return mRunning && mSocket != null && mSocket.isConnected();
        }

        public Handler getHandler() {
            return mHandler;
        }

        public void run() {
            Looper.prepare();
            mRunning = true;
            mHandler = new Handler() {
                @Override
                public void handleMessage(Message msg) {
                    switch (msg.what) {
                        case MSG_MAYBE_READ_MSG:
                            maybeReadMessage();
                            sendEmptyMessageDelayed(MSG_MAYBE_READ_MSG, MSG_READ_INTERVAL);
                            break;
                        case MSG_WRITE_MSG:
                            writeMessage((byte[]) msg.obj);
                            break;
                    }
                }
            };

            mHandler.sendEmptyMessageDelayed(MSG_MAYBE_READ_MSG, MSG_READ_INTERVAL);
            Looper.loop();
        }

        public void shutdown() {
            if (mSocket != null) {
                try {
                    mSocket.close();
                } catch (IOException e) { }
                mSocket = null;
            }
        }

        private void maybeReadMessage() {
            if (mSocket == null || !isConnected()) {
                return;
            }

            ProtoMessage message = mReader.read(mIn);
            if (message == null) {
                return;
            }

            switch (message.getType()) {
                case StartPhotoData.TYPE:
                    StartPhotoData start = (StartPhotoData) message;
                    if (mVanguardMain != null) {
                        mVanguardMain.startPhotoData(start.index);
                    }
                    break;
                case StopPhotoData.TYPE:
                    if (mVanguardMain != null) {
                        mVanguardMain.stopPhotoData();
                    }
                    break;
                case SendText.TYPE:
                    if (mVanguardMain != null) {
                        mVanguardMain.sendText();
                    }
                    break;
                case AddPhoneNumber.TYPE:
                    AddPhoneNumber add = (AddPhoneNumber) message;
                    if (mVanguardMain != null) {
                        mVanguardMain.addPhoneNumber(add.phoneNumber);
                    }
                    break;
                default:
                    Log.i(TAG, String.format("Unknown message type %d", message.getType()));
                    break;
            }
        }

        public void writeMessage(byte[] message)
        {
            try {
                mOut.write(message);
            } catch (IOException e) {}
        }
    }
}
