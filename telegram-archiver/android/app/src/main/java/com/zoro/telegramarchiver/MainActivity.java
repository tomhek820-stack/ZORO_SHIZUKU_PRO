package com.zoro.telegramarchiver;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private final int bg = Color.rgb(12, 18, 27);
    private final int panel = Color.rgb(25, 36, 50);
    private final int accent = Color.rgb(63, 166, 255);
    private final String command = "cd ~/zoro-telegram-archiver && python zoro_telegram_archiver.py";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(bg);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(22), dp(28), dp(22), dp(24));
        scroll.addView(root);

        TextView brand = text("ZORO", 34, Color.WHITE, true);
        root.addView(brand);
        TextView subtitle = text("TELEGRAM ARCHIVER PRO", 17, accent, true);
        root.addView(subtitle);
        TextView status = text("LOCAL EXPORT • PRIVATE BY DESIGN", 12, Color.LTGRAY, false);
        status.setPadding(0, dp(8), 0, dp(20));
        root.addView(status);

        TextView intro = text("احفظ محادثاتك التي يستطيع حسابك الوصول إليها في أرشيف ZIP يحتوي على الرسائل وملف HTML والوسائط المتاحة.", 17, Color.WHITE, false);
        intro.setPadding(dp(16), dp(16), dp(16), dp(16)); intro.setBackgroundColor(panel);
        root.addView(intro, params());

        addSection(root, "طريقة العمل");
        addParagraph(root, "1. ثبّت Termux وافتحه.\n2. ثبّت Python واعتماديات المشروع.\n3. شغّل أداة Python وسجّل الدخول إلى حساب تيليجرام بنفسك.\n4. اختر المحادثات أو القنوات ثم أنشئ ZIP.");
        addSection(root, "أوامر التشغيل");
        TextView cmd = text("pkg update -y && pkg install -y python git\npython -m pip install --upgrade pip\npip install -r requirements.txt\n" + command, 13, Color.rgb(190, 220, 245), false);
        cmd.setTypeface(Typeface.MONOSPACE); cmd.setPadding(dp(12), dp(12), dp(12), dp(12)); cmd.setBackgroundColor(panel);
        root.addView(cmd, params());

        Button copy = button("نسخ أمر تشغيل الأداة");
        copy.setOnClickListener(v -> {
            ClipboardManager cm = (ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("ZORO Archiver command", command));
            Toast.makeText(this, "تم نسخ الأمر", Toast.LENGTH_SHORT).show();
        }); root.addView(copy, params());

        Button open = button("فتح Termux");
        open.setOnClickListener(v -> {
            Intent launch = getPackageManager().getLaunchIntentForPackage("com.termux");
            if (launch != null) startActivity(launch);
            else Toast.makeText(this, "ثبّت Termux أولاً ثم أعد المحاولة", Toast.LENGTH_LONG).show();
        }); root.addView(open, params());

        addSection(root, "مهم للخصوصية");
        addParagraph(root, "هذا APK واجهة مساعدة، ومحرك التصدير هو سكربت Python الذي يعمل داخل Termux. لا تدخل رمز تيليجرام أو كلمة مرور التحقق في هذا التطبيق. أدخلها فقط في جلسة Termux المحلية. لا تشارك ملف الجلسة .session. لا يمكن تصدير محادثات لا يملك حسابك صلاحية الوصول إليها أو تجاوز قيود المحتوى المحمي.");
        setContentView(scroll);
    }

    private void addSection(LinearLayout root, String s) {
        TextView t = text(s, 19, accent, true); t.setPadding(0, dp(22), 0, dp(8)); root.addView(t);
    }
    private void addParagraph(LinearLayout root, String s) {
        TextView t = text(s, 15, Color.rgb(220, 228, 238), false); t.setPadding(dp(4), dp(4), dp(4), dp(4)); root.addView(t, params());
    }
    private TextView text(String s, int size, int color, boolean bold) {
        TextView t = new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD); t.setLineSpacing(dp(4), 1f); return t;
    }
    private Button button(String s) {
        Button b = new Button(this); b.setText(s); b.setTextColor(Color.WHITE); b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(accent)); return b;
    }
    private LinearLayout.LayoutParams params() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2); p.setMargins(0, dp(6), 0, dp(8)); return p;
    }
    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density + 0.5f); }
}
