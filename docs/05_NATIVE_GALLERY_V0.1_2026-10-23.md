# EO1-Museum Native Gallery v0.1 개발 및 실기 시험

**Date:** 2026-10-23  
**Device:** Electric Objects EO1  
**Project:** EO1-Museum  
**Version:** v0.1  
**Repository:** `jeong0449/EO1-Museum`

---

## 1. 목적

기존 EO1-Museum의 초기 구현은 PC에서 Python으로 작품 이미지를 준비하고 HTTP 서버를 실행한 뒤, EO1에서 Firefox를 이용하여 이미지를 표시하는 방식이었다.

이 방식은 EO1의 원래 서비스를 사용할 수 없게 된 상황에서 비교적 쉽게 구현할 수 있었지만 다음 요소가 필요했다.

- 같은 네트워크에 연결된 PC
- PC에서 실행되는 HTTP 서버
- Wi-Fi 연결
- EO1의 Firefox
- 부팅 후 Firefox를 실행하기 위한 보조 앱인 MetBoot

이번 실험의 목적은 이러한 외부 의존성을 제거하고, EO1 자체 저장공간에 있는 이미지를 네이티브 Android 앱에서 직접 표시하는 것이었다.

최종 목표는 다음과 같이 정의하였다.

> 전원만 연결하면 EO1이 부팅되고, 내부 저장공간의 작품 이미지를 자동으로 읽어 슬라이드쇼를 시작한다.

---

## 2. 개발 전략

새로운 Android 프로젝트를 처음부터 Android 4.4.2에 맞추는 대신, 실제 EO1에서 작동하는 것이 확인된 `spalt/EO1` 프로젝트를 기반으로 개발하기로 하였다.

EO1의 환경은 다음과 같다.

- Android 4.4.2
- API 19
- 32-bit ARM (`armeabi-v7a`)
- Freescale i.MX6 계열 SoC
- 약 818 MiB RAM
- 4 GB eMMC
- 디스플레이 해상도 1080 × 1920 사용

기존 `spalt/EO1` 프로젝트는 Flickr 연동, 이미지 및 비디오 표시, 밝기 제어, 하드웨어 버튼 처리, HOME/Launcher 기능 등을 이미 구현하고 있었다.

따라서 최신 Android 환경에서 새 앱을 만드는 것보다 이 코드를 단순화하여 EO1-Museum 전용 Gallery로 만드는 것이 더 현실적이라고 판단하였다.

---

## 3. 빌드 환경 복구

원본 `spalt/EO1` 프로젝트에는 Gradle wrapper 관련 파일이 완전하지 않아 그대로는 빌드할 수 없었다.

별도의 Android 프로젝트에서 `gradle/` wrapper 디렉터리를 가져오고 다음 조합을 사용하여 빌드 환경을 복구하였다.

- JDK 17
- Gradle 7.5
- Android Gradle Plugin 7.4.1

Gradle wrapper 설정:

```text
distributionUrl=https\://services.gradle.org/distributions/gradle-7.5-bin.zip
```

기존 설정에 남아 있던 `distributionSha256Sum`은 제거하였다.

이 조합에서 Gradle Sync 및 APK 빌드에 성공하였다.

APK 출력 위치:

```text
app/build/outputs/apk/debug/app-debug.apk
```

---

## 4. 1차 실험: 로컬 이미지 한 장 표시

기존 `MainActivity.java`에는 Flickr API를 이용하여 이미지를 가져오는 코드가 포함되어 있었다.

우선 네트워크 관련 기능을 제거하고 다음 파일 하나를 직접 읽도록 단순화하였다.

```text
/sdcard/EO1-Museum/images/test.jpg
```

Android의 `BitmapFactory.decodeFile()`을 이용하여 이미지를 읽고 기존 `ImageView`에 표시하였다.

PC에서 ADB를 이용하여 테스트 이미지를 전송하였다.

```powershell
adb -s 115343222 shell mkdir -p /sdcard/EO1-Museum/images
adb -s 115343222 push test.jpg /sdcard/EO1-Museum/images/test.jpg
```

새 APK를 설치하고 실행하였다.

```powershell
adb -s 115343222 install -r app-debug.apk
adb -s 115343222 shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

### 결과

성공.

EO1 내부 저장공간의 JPEG 파일이 네트워크 연결 없이 네이티브 Android 앱에서 정상적으로 표시되었다.

이 실험으로 다음 경로가 실제 EO1에서 작동함을 확인하였다.

```text
PC
 ↓ ADB push
EO1 internal storage
 ↓
BitmapFactory
 ↓
EO1 Gallery
 ↓
ImageView
```

이 시점에서 Firefox와 PC 웹 서버 없이 EO1 자체에서 이미지를 표시할 수 있다는 것이 확인되었다.

---

## 5. 2차 실험: 여러 이미지의 랜덤 슬라이드쇼

다음 단계로 `/sdcard/EO1-Museum/images/`에 저장된 여러 이미지 파일을 자동으로 검색하도록 `MainActivity.java`를 확장하였다.

지원 확장자는 다음과 같이 설정하였다.

```text
.jpg
.jpeg
.png
```

검색된 파일 목록은 `Collections.shuffle()`을 이용하여 섞은 뒤 순차적으로 표시한다.

따라서 매번 완전히 무작위로 하나씩 선택하는 방식과 달리, 한 사이클 안에서는 모든 이미지가 한 번씩 표시된다.

한 사이클이 끝나면 다시 목록을 섞는다.

슬라이드 간격은 다음과 같이 설정하였다.

```java
private static final long SLIDE_INTERVAL = 15000;
```

즉 작품 하나를 15초 동안 표시한다.

---

## 6. 이미지 복사 과정에서 발견한 문제

PC의 기존 EO1-Museum 프로젝트에는 The Met에서 가져와 가공한 이미지가 다음 디렉터리에 저장되어 있었다.

```text
C:\EO1-Museum\display
```

처음에는 다음 명령으로 이미지를 EO1에 전송하였다.

```powershell
adb -s 115343222 push "C:\EO1-Museum\display" /sdcard/EO1-Museum/images/
```

그러나 앱을 실행하면 다음 메시지만 표시되었다.

```text
1 images found
```

15초를 기다려도 화면이 바뀌지 않았다.

원인은 `adb push`의 디렉터리 처리 방식이었다.

위 명령은 `display` 안의 파일을 `images`에 넣는 것이 아니라 디렉터리 자체를 복사하여 다음 구조를 만들었다.

```text
/sdcard/EO1-Museum/images/
├── test.jpg
└── display/
    ├── ...
    ├── ...
    └── ...
```

현재 Gallery는 `images` 바로 아래의 파일만 검색하고 하위 디렉터리를 재귀적으로 검색하지 않는다.

따라서 앱이 발견한 파일은 `test.jpg` 하나뿐이었다.

잘못 복사된 디렉터리는 다음과 같이 제거하였다.

```powershell
adb -s 115343222 shell rm -rf /sdcard/EO1-Museum/images/display
```

PowerShell에서 각 파일을 직접 `images` 디렉터리에 복사하였다.

```powershell
Get-ChildItem "C:\EO1-Museum\display\*" -File | ForEach-Object {
    .\adb.exe -s 115343222 push $_.FullName /sdcard/EO1-Museum/images/
}
```

기존 `test.jpg`를 포함하여 총 58개의 이미지가 인식되었다.

### 결과

성공.

58장의 작품이 무작위 순서로 표시되었으며 15초마다 다음 작품으로 정상적으로 전환되었다.

---

## 7. 완전 오프라인 동작 확인

슬라이드쇼 동작에는 다음 요소가 필요하지 않음을 확인하였다.

- Wi-Fi
- 인터넷 연결
- Firefox
- PC
- Python HTTP server

즉 작품 파일을 EO1 내부 저장공간에 넣은 이후에는 EO1만으로 독립적으로 슬라이드쇼를 실행할 수 있다.

현재 기본 구조는 다음과 같다.

```text
/sdcard/EO1-Museum/images/
        ↓
EO1 Gallery
        ↓
ImageView
        ↓
15-second slideshow
```

---

## 8. HOME 앱 동작 확인

`AndroidManifest.xml`에는 원래 `spalt/EO1` 프로젝트의 HOME intent 설정이 남아 있었다.

```xml
<intent-filter>
    <action android:name="android.intent.action.MAIN" />
    <category android:name="android.intent.category.HOME" />
    <category android:name="android.intent.category.DEFAULT" />
</intent-filter>
```

실제 설치된 APK에서도 다음 명령으로 HOME category가 등록되어 있음을 확인하였다.

```sh
dumpsys package com.dan.eo1 | grep HOME
```

결과:

```text
Category: "android.intent.category.HOME"
Category: "android.intent.category.HOME"
```

또한 다음 명령으로 HOME intent를 직접 실행하였다.

```sh
am start -a android.intent.action.MAIN -c android.intent.category.HOME
```

선택 화면 없이 현재 개발한 EO1 Gallery가 즉시 실행되었다.

따라서 `com.dan.eo1`이 EO1의 HOME 앱으로 정상 동작하고 있음을 확인하였다.

---

## 9. 자동 실행 과정에서 발견한 MetBoot 문제

전원을 완전히 제거했다가 다시 연결하여 실제 cold boot 시험을 하였다.

그런데 부팅 후 오늘 개발한 네이티브 Gallery 대신 이전에 개발했던 Firefox 기반 EO1 Gallery 화면이 나타났다.

처음에는 HOME 설정 문제로 생각하였으나, 조사 결과 원인은 별도로 설치되어 있던 `MetBoot`였다.

MetBoot는 EO1-Museum의 초기 웹 기반 구현에서 사용했던 작은 Android 보조 앱이다.

역할은 다음과 같았다.

```text
Android boot
 ↓
BOOT_COMPLETED
 ↓
MetBoot
 ↓
Firefox
 ↓
PC EO1-Museum web server
```

따라서 HOME 앱이 새로운 네이티브 EO1 Gallery로 정상 설정되어 있더라도, 부팅 완료 후 MetBoot가 Firefox를 다시 실행하여 Gallery 화면을 덮어쓰고 있었다.

MetBoot를 비활성화한 뒤 재부팅하자 Firefox가 실행되지 않고 네이티브 EO1 Gallery가 정상적으로 자동 실행되었다.

### 중요

**Native EO1 Gallery에서는 MetBoot가 필요하지 않다.**

오히려 MetBoot가 설치되어 활성화되어 있으면 부팅 후 Firefox를 실행하여 네이티브 Gallery의 동작을 방해한다.

따라서 v0.1에서는 MetBoot를 비활성화하거나 제거해야 한다.

필요한 경우 EO1에서 다음과 같이 제거할 수 있다.

```sh
pm uninstall com.example.metboot
```

MetBoot의 소스 코드는 초기 웹 기반 구현의 개발 기록으로 PC 또는 Git 저장소에 남겨둘 수 있다.

---

## 10. 최종 부팅 구조

v0.1의 최종 동작 구조는 다음과 같다.

```text
EO1 power ON
      ↓
Android 4.4.2 boot
      ↓
EO1 Gallery
(com.dan.eo1)
      ↓
HOME activity
      ↓
/sdcard/EO1-Museum/images/
      ↓
local image loading
      ↓
randomized slideshow
      ↓
next image every 15 seconds
```

다음 요소는 더 이상 필요하지 않다.

```text
MetBoot        ×
Firefox        ×
PC web server  ×
Wi-Fi          ×
Internet       ×
```

즉 전원만 연결하면 EO1이 독립적인 미술 전자액자로 작동한다.

---

## 11. v0.1 정의

2026-10-23 현재 구현을 **EO1 Gallery v0.1**로 정의한다.

### EO1 Gallery v0.1

주요 기능:

- 실제 Electric Objects EO1에서 네이티브 Android 앱으로 실행
- Android 4.4.2/API 19 지원
- EO1 내부 저장공간의 이미지 직접 표시
- JPG/JPEG/PNG 파일 검색
- 여러 작품을 무작위 순서로 재생
- 한 사이클 동안 중복 없이 모든 작품 표시
- 사이클 종료 후 재셔플
- 기본 표시 간격 15초
- 네트워크 없이 완전 오프라인 동작
- HOME 앱으로 동작
- 전원 투입 후 자동 실행
- MetBoot, Firefox 및 PC 웹 서버 불필요

v0.1은 EO1-Museum의 첫 번째 실용적인 네이티브 릴리스로 간주한다.

---

## 12. v0.1의 의미

EO1-Museum 개발은 처음에는 서비스가 종료된 EO1에서 다시 이미지를 표시하는 것이 목표였다.

초기 구현에서는 EO1을 일종의 웹 디스플레이로 사용하였다.

```text
The Met
 ↓
Python
 ↓
PC web server
 ↓
Wi-Fi
 ↓
Firefox
 ↓
EO1
```

v0.1에서는 구조가 크게 단순해졌다.

```text
prepared artwork
 ↓
EO1 local storage
 ↓
native EO1 Gallery
 ↓
display
```

따라서 EO1은 더 이상 PC와 웹 브라우저에 의존하는 단말이 아니라, 자체 저장공간과 Android 앱만으로 동작하는 독립적인 디지털 액자가 되었다.

서비스가 종료된 Electric Objects EO1을 실제로 다시 사용할 수 있는 최소 기능이 완성되었다는 점에서 v0.1을 하나의 중요한 개발 이정표로 본다.

---

## 13. 다음 단계

다음 버전에서는 정지 이미지뿐 아니라 동영상 작품을 지원하는 것을 우선 검토한다.

원래 `spalt/EO1` 프로젝트에는 `VideoView` 기반의 동영상 재생 기능이 포함되어 있었으며 현재 레이아웃과 코드에도 `VideoView`를 활용할 기반이 남아 있다.

따라서 다음 목표를 다음과 같이 정의할 수 있다.

### v0.2 후보

**Mixed image and video playback**

예상 동작:

```text
/sdcard/EO1-Museum/images/
    painting01.jpg
    painting02.jpg
    video01.mp4
    painting03.jpg
```

재생 방식:

```text
JPG / JPEG / PNG
        ↓
ImageView
        ↓
15초 표시

MP4
        ↓
VideoView
        ↓
동영상 끝까지 재생
        ↓
다음 작품
```

EO1의 오래된 Android 환경을 고려하여 MP4 테스트에서는 우선 H.264/AVC 비디오와 AAC 오디오 조합을 사용한다.

그 이후에는 다음 기능을 단계적으로 검토할 수 있다.

- PC의 The Met 다운로드 프로그램과 EO1 저장공간의 자동 동기화
- 작품별 표시 시간 설정
- 작품 메타데이터 표시
- 원격 작품 목록 관리
- 자연어 기반 작품 검색
- AI를 이용한 작품 큐레이션

---

## 14. 결론

2026-10-23 실험을 통해 Electric Objects EO1에서 네트워크나 외부 서버 없이 동작하는 네이티브 Gallery를 구현하였다.

58개의 로컬 작품 이미지를 실제 기기에서 랜덤 순서로 연속 표시하였으며, HOME 앱 설정과 부팅 자동 실행도 확인하였다.

초기 웹 기반 구현에 사용했던 MetBoot는 네이티브 버전에서는 필요하지 않으며 오히려 Firefox를 자동 실행하여 방해하므로 제거하거나 비활성화해야 한다.

이 상태를 **EO1 Gallery v0.1**로 정의한다.

> **EO1 Gallery v0.1 — Native offline image slideshow with boot auto-start**

이제 EO1-Museum의 개발 목표는 더 이상 단순히 오래된 EO1을 “되살리는 것”에 머물지 않는다. v0.1에서 기본적인 독립형 전자액자 기능이 완성되었으므로, 이후 개발은 이미지와 동영상을 포함한 콘텐츠 재생, 작품 관리 및 큐레이션 기능을 확장하는 단계로 넘어간다.
