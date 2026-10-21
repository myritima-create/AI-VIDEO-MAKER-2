package com.bga.aivideo;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.webkit.URLUtil;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

public class MainActivity extends Activity {
    WebView web;
    EditText url;
    SharedPreferences sp;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        sp = getSharedPreferences("p", 0);
        if (Build.VERSION.SDK_INT <= 28)
            requestPermissions(new String[]{"android.permission.WRITE_EXTERNAL_STORAGE"}, 1);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        LinearLayout bar = new LinearLayout(this);
        url = new EditText(this);
        url.setHint("PC address, e.g. 192.168.1.5:8501");
        url.setSingleLine(true);
        url.setText(sp.getString("u", ""));
        Button go = new Button(this);
        go.setText("Go");
        bar.addView(url, new LinearLayout.LayoutParams(0, -2, 1));
        bar.addView(go);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        web.setWebViewClient(new WebViewClient());
        web.setDownloadListener((u, ua, cd, mime, len) -> {
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(u));
            r.setMimeType(mime);
            r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, URLUtil.guessFileName(u, cd, mime));
            ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(r);
            Toast.makeText(this, "Downloading to Downloads folder", Toast.LENGTH_SHORT).show();
        });
        go.setOnClickListener(v -> load());
        root.addView(bar);
        root.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        if (!url.getText().toString().isEmpty()) load();
    }

    void load() {
        String u = url.getText().toString().trim();
        if (!u.startsWith("http")) u = "http://" + u;
        sp.edit().putString("u", u).apply();
        web.loadUrl(u);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
