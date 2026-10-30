package com.eo1.adbapprovalhelper;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
 @Override public void onCreate(Bundle b) {
  super.onCreate(b);
  LinearLayout l=new LinearLayout(this); l.setOrientation(LinearLayout.VERTICAL); l.setPadding(40,40,40,40);
  TextView t=new TextView(this);
  t.setText("ADB Approval Helper\n\nEnable the accessibility service, disconnect OTG, then connect EO1 to the PC by USB.");
  t.setTextSize(18);
  Button x=new Button(this); x.setText("OPEN ACCESSIBILITY SETTINGS");
  x.setOnClickListener(new View.OnClickListener(){ @Override public void onClick(View v){ startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)); }});
  l.addView(t); l.addView(x); setContentView(l);
 }
}
