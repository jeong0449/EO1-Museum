package com.eo1.adbapprovalhelper;
import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class AdbApprovalService extends AccessibilityService {
 private static final String PKG="com.android.systemui";
 private static final String MARKER="Always allow from this computer";

 @Override public void onAccessibilityEvent(AccessibilityEvent e) {
  if(e==null || e.getPackageName()==null || !PKG.contentEquals(e.getPackageName())) return;
  AccessibilityNodeInfo root=getRootInActiveWindow(); if(root==null) return;
  List<AccessibilityNodeInfo> marks=root.findAccessibilityNodeInfosByText(MARKER);
  if(marks==null || marks.isEmpty()) return;
  for(AccessibilityNodeInfo n:marks) check(n);
  List<AccessibilityNodeInfo> oks=root.findAccessibilityNodeInfosByText("OK");
  if(oks!=null) for(AccessibilityNodeInfo n:oks) if(click(n)) return;
 }
 private void check(AccessibilityNodeInfo n){
  AccessibilityNodeInfo c=n;
  for(int i=0;c!=null && i<4;i++,c=c.getParent()){
   if(c.isCheckable()){ if(!c.isChecked()) c.performAction(AccessibilityNodeInfo.ACTION_CLICK); return; }
  }
  click(n);
 }
 private boolean click(AccessibilityNodeInfo n){
  AccessibilityNodeInfo c=n;
  for(int i=0;c!=null && i<4;i++,c=c.getParent()){
   if(c.isClickable()) return c.performAction(AccessibilityNodeInfo.ACTION_CLICK);
  }
  return false;
 }
 @Override public void onInterrupt(){}
}
