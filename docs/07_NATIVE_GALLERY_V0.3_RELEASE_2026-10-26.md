# EO1 Native Gallery v0.3 — 배포판 완성

**작성일:** 2026-10-26  
**프로젝트:** EO1 Museum  
**대상 기기:** Electric Objects EO1  
**패키지:** `com.dan.eo1`  
**개발 디렉토리:** `EO1-main_v0.3`

---

## 1. 개요

v0.3은 EO1 Museum 프로젝트에서 처음으로 **실사용 가능한 배포판(release version)**이라 부를 만한 버전이다.

v0.1에서는 EO1 내부 저장소의 이미지를 네이티브 앱으로 재생하는 데 성공했고, v0.2에서는 여기에 MP4 동영상 재생과 Bluetooth 오디오를 추가하였다. v0.3에서는 이를 한 단계 더 발전시켜 다음 기능을 하나의 앱으로 통합하였다.

- 내부 저장소 기반 Local Gallery
- PC 웹 서버를 이용하는 PC Gallery
- 마우스 우클릭 제어 메뉴
- 현재 Gallery 모드 표시
- 이미지 간 cross-fade
- 시계 오버레이
- 미디어 재검색
- 부팅 후 자동 실행
- 이미지와 동영상의 혼합 재생
- Bluetooth를 통한 동영상 오디오 출력

가장 중요한 변화는 이제 PC에서 제공하는 콘텐츠를 표시하기 위해 **Firefox나 MetBoot가 필요하지 않다**는 것이다. EO1 Museum 앱 자체에 WebView를 포함시켜 Local Gallery와 PC Gallery를 하나의 앱 안에서 선택할 수 있게 되었다.

기본 동작은 다음과 같다.

```text
EO1 전원 켜기
      |
      v
Android 부팅
      |
      v
EO1 Museum 자동 실행
      |
      v
Local Gallery
      |
      +----> 내부 저장소의 이미지/MP4 재생
      |
      +----> 마우스 우클릭
                 |
                 +----> Local Gallery
                 +----> PC Gallery
                 +----> Next
                 +----> Rescan Media
                 +----> Clock On/Off
```

앱을 새로 실행하거나 EO1을 재부팅하면 항상 다음 상태로 시작한다.

```text
Gallery mode : Local Gallery
Clock        : ON
```

PC Gallery는 필요할 때만 선택하며, 다음 부팅까지 기억하지 않는다.

---

## 2. v0.3의 개발 목표

v0.3의 목표는 새로운 기능을 많이 추가하는 것보다는 지금까지 실험적으로 구현한 기능을 **하나의 일관된 EO1용 애플리케이션으로 완성하는 것**이었다.

구체적인 목표는 다음과 같았다.

1. v0.2에서 완성한 이미지/MP4 재생 기능을 그대로 유지한다.
2. Firefox 없이 PC의 웹 콘텐츠를 표시한다.
3. 마우스로 간단하게 Gallery 동작을 제어한다.
4. Local Gallery와 PC Gallery를 명확하게 구분한다.
5. 이미지 전환을 부드럽게 만든다.
6. 시계를 선택적으로 표시한다.
7. EO1을 켜기만 하면 자동으로 Gallery가 실행되게 한다.
8. 외부 PC가 없어도 EO1 자체만으로 정상 동작하게 한다.
9. 불필요한 설정 저장 기능은 만들지 않는다.
10. 가능한 한 기존 Electric Objects 서비스에 의존하지 않는다.

결국 일반 Android 앱이라기보다는 **전원을 켜면 바로 작동하는 가전제품에 가까운 동작**을 목표로 하였다.

---

## 3. Local Gallery

Local Gallery는 EO1 Museum의 기본 동작 모드이다.

미디어 파일은 다음 디렉토리에서 읽는다.

```text
/sdcard/EO1-Museum/images
```

현재 지원하는 파일 형식은 다음과 같다.

```text
.jpg
.jpeg
.png
.mp4
```

앱이 미디어 목록을 읽으면 순서를 무작위로 섞는다.

이미지는 기본적으로 15초 동안 표시하며, MP4 파일을 만나면 동영상 전체를 재생한 뒤 다음 미디어로 넘어간다.

목록의 끝에 도달하면 다시 순서를 섞어 처음부터 재생한다.

따라서 이미지와 동영상을 같은 디렉토리에 넣어 두기만 하면 별도의 playlist 없이 계속 순환하는 mixed-media Gallery가 된다.

---

## 4. PC Gallery

PC Gallery는 앱 내부에 포함된 Android `WebView`를 사용한다.

현재 개발 환경에서 사용하는 주소는 다음과 같다.

```text
http://192.168.1.103:8000/
```

PC에서는 간단히 다음과 같이 웹 서버를 실행할 수 있다.

```text
python -m http.server 8000
```

v0.3 이전에는 PC에서 제공하는 콘텐츠를 EO1에 표시하기 위해 다음과 같은 구조를 사용하였다.

```text
Android
  -> MetBoot
      -> Firefox
          -> PC HTTP server
```

v0.3에서는 다음과 같이 단순해졌다.

```text
Android
  -> EO1 Museum
      -> WebView
          -> PC HTTP server
```

따라서 정상적인 PC Gallery 사용에는 더 이상 Firefox도, MetBoot도 필요하지 않다.

이것은 v0.3에서 이루어진 가장 중요한 구조적 변화 중 하나이다.

---

## 5. 항상 Local Gallery로 시작하기

PC Gallery가 마지막 사용 모드였다고 해서 다음 부팅 때 다시 PC Gallery로 들어가는 것은 바람직하지 않다.

PC Gallery는 다음 조건에 의존하기 때문이다.

```text
Wi-Fi
PC
HTTP server
올바른 PC IP 주소
```

반면 Local Gallery는 EO1 내부의 파일만 있으면 된다.

따라서 v0.3에서는 Gallery 모드를 `SharedPreferences` 등에 저장하지 않는다.

항상 다음과 같이 시작한다.

```text
재부팅
   |
   v
EO1 Museum
   |
   v
Local Gallery
```

PC Gallery는 현재 세션에서만 선택하는 임시 모드이다.

이 방식이 디지털 액자라는 장치의 성격에도 더 잘 맞는다.

---

## 6. 부팅 후 자동 실행

EO1 Museum의 MainActivity는 일반 Launcher 앱인 동시에 Android의 HOME 후보로 등록되어 있다.

EO1을 기본 HOME 앱으로 선택하고 **Always**를 지정한 뒤 실제 전원을 껐다 켜는 cold boot를 시험하였다.

결과는 다음과 같았다.

```text
전원 ON
   |
   v
Android 부팅
   |
   v
EO1 Museum 자동 실행
   |
   v
Local Gallery 시작
```

별도로 앱을 실행할 필요가 없다.

개발 중 `adb install -r`로 APK를 반복 설치하면 Android의 기본 HOME 선택이 영향을 받을 가능성이 있다. 따라서 최종 APK를 설치한 뒤에는 EO1 Museum을 다시 기본 HOME 앱으로 지정해 두는 것이 좋다.

실사용 상태에서는 APK를 계속 재설치할 일이 없으므로 큰 문제는 아니다.

---

## 7. 마우스 우클릭 메뉴

EO1의 micro-USB OTG 포트에 USB 마우스를 연결하여 Gallery를 제어할 수 있다.

v0.3에서는 **마우스 오른쪽 버튼**을 누르면 제어 메뉴가 열린다.

메뉴 항목은 다음과 같다.

```text
Local Gallery
PC Gallery
Next
Rescan Media
Clock: On / Clock: Off
```

현재 동작 중인 Gallery에는 체크 표시를 붙인다.

Local Gallery라면:

```text
✓ Local Gallery
  PC Gallery
  Next
  Rescan Media
  Clock: Off
```

PC Gallery라면:

```text
  Local Gallery
✓ PC Gallery
  Next
  Rescan Media
  Clock: Off
```

이 방식의 장점은 Gallery 화면 자체에는 Local/PC 같은 표시를 계속 띄우지 않아도 된다는 것이다.

평상시에는 작품만 표시하고, 현재 상태를 알고 싶을 때 우클릭하면 된다.

---

## 8. PopupMenu 대신 AlertDialog

처음에는 마우스 우클릭 메뉴를 `PopupMenu`로 구현하였다.

로그를 확인해 보니 우클릭 이벤트 자체는 정상적으로 인식되고 `showControlMenu()`까지 호출되었지만, 정작 PopupMenu가 EO1 화면에 보이지 않았다.

결국 `PopupMenu`를 포기하고 `AlertDialog`에 목록을 넣는 방식으로 변경하였다.

이 방식은 EO1의 Android 4.4.2 환경에서 안정적으로 동작하였다.

오래된 Android와 제조사 커스터마이징이 들어간 기기에서는 최신 방식의 UI를 고집하는 것보다 단순하고 전통적인 Android UI 요소를 사용하는 것이 오히려 안전하다는 것을 보여준 사례였다.

---

## 9. 마우스 우클릭 인식

마우스 이벤트 처리도 생각보다 단순하지 않았다.

한 번의 물리적인 우클릭이 Android에서는 여러 `MotionEvent` 경로를 통해 들어올 수 있었다.

따라서 이벤트가 다음 소스인지 확인하고,

```java
InputDevice.SOURCE_MOUSE
```

버튼 상태에 다음 값이 있는지를 확인한다.

```java
MotionEvent.BUTTON_SECONDARY
```

또한 하나의 물리적 우클릭으로 메뉴가 두 번 열리는 것을 막기 위해 약간의 debounce를 넣었다.

현재 값은 다음과 같다.

```text
400 ms
```

이를 통해 마우스 우클릭 메뉴가 안정적으로 작동한다.

---

## 10. Gallery 모드에 따른 메뉴 동작

`Next`와 `Rescan Media`는 Local Gallery에서만 의미가 있다.

따라서 Local Gallery에서는 모든 메뉴가 활성화된다.

```text
Local Gallery   enabled
PC Gallery      enabled
Next            enabled
Rescan Media    enabled
Clock           enabled
```

PC Gallery에서는 다음과 같다.

```text
Local Gallery   enabled
PC Gallery      enabled
Next            disabled
Rescan Media    disabled
Clock           enabled
```

PC Gallery에서는 `Next`와 `Rescan Media`를 흐리게 표시하여 사용할 수 없는 메뉴라는 것을 나타낸다.

기능적으로도 해당 항목은 선택되지 않는다.

현재 모드 자체는 `✓` 표시로 구분한다.

---

## 11. 이미지 cross-fade

v0.2에서는 이미지가 즉시 다음 이미지로 교체되었다.

v0.3에서는 두 개의 `ImageView`를 겹쳐 놓고 alpha 값을 서로 반대로 변화시켜 cross-fade 효과를 구현하였다.

개념적으로는 다음과 같다.

```text
ImageView A : 현재 이미지
ImageView B : 다음 이미지

A : alpha 1.0 -> 0.0
B : alpha 0.0 -> 1.0
```

두 애니메이션을 동시에 실행한다.

현재 cross-fade 시간은 다음과 같다.

```text
2000 ms
```

전환이 끝나면 이전 ImageView를 숨기고 두 ImageView의 역할을 서로 바꾼다.

15초 간격으로 작품을 표시하는 디지털 액자에서는 순간적으로 그림이 바뀌는 것보다 훨씬 자연스럽다.

---

## 12. 첫 이미지와 동영상 이후의 처리

Local Gallery에 처음 진입했을 때부터 검은 화면에서 2초 동안 fade-in하는 것은 불필요하다.

따라서 첫 번째 이미지는 즉시 표시한다.

```text
Local Gallery 진입
        |
        v
첫 이미지 -> 즉시 표시
        |
        v
두 번째 이미지 -> cross-fade
        |
        v
이후 이미지 -> cross-fade
```

동영상을 재생할 때는 두 ImageView를 모두 숨긴다.

동영상이 끝나고 다시 이미지가 나타날 때에는 이미지 상태를 초기화하여 깨끗하게 표시하도록 하였다.

---

## 13. 이미지와 동영상 혼합 재생

Local Gallery는 이미지와 MP4를 하나의 목록에서 함께 다룬다.

이미지인 경우:

```text
이미지 표시
   |
15초 대기
   |
다음 미디어
```

MP4인 경우:

```text
VideoView 준비
   |
동영상 재생
   |
끝까지 재생
   |
다음 미디어
```

동영상 준비 중에는 progress indicator가 표시된다.

재생이 끝나면 자동으로 다음 미디어로 이동한다.

동영상 오류가 발생해도 Gallery 전체가 멈추지 않고 해당 파일을 건너뛰어 다음 미디어를 재생하도록 하였다.

---

## 14. 실제 확인한 MP4

개발 과정에서 다음과 같은 MP4 파일의 재생을 실제로 확인하였다.

```text
Container    : MP4
Video codec  : H.264 / AVC
Resolution   : 1080 × 1920
Frame rate   : 30 fps
Pixel format : yuv420p
Bitrate      : 약 15.8 Mbps
Audio        : AAC, 48 kHz, stereo
Duration     : 약 48초
File size    : 약 96 MB
```

EO1에서 영상과 음성이 모두 정상 재생되었다.

물론 이것이 EO1의 절대적인 codec 또는 bitrate 한계를 의미하는 것은 아니다. 현재까지 **정상 작동을 직접 확인한 사례**로 기록해 둔다.

---

## 15. Bluetooth 오디오

EO1 자체에는 이 프로젝트에서 바로 활용할 수 있는 내장 오디오 출력 장치가 없다.

따라서 Bluetooth 오디오 장치를 Android 설정에서 연결해 보았다.

페어링은 정상적으로 이루어졌고, 더욱 중요한 것은 EO1의 전원을 완전히 껐다 켠 뒤에도 Bluetooth 장치가 자동으로 다시 연결되었다는 점이다.

MP4에 포함된 AAC 오디오 역시 Bluetooth를 통해 정상적으로 출력되었다.

따라서 다음과 같은 동작이 가능하다.

```text
전원 ON
   |
Android 부팅
   |
Bluetooth 자동 재연결
   |
EO1 Museum
   |
Local Gallery
   |
MP4 영상 + Bluetooth 음성
```

EO1 Museum 앱 자체에는 Bluetooth를 위한 별도의 코드를 넣을 필요가 없다.

Android가 일반적인 media audio routing을 담당한다.

---

## 16. USB 오디오 실험

보유하고 있던 Behringer UCA200 USB 오디오 인터페이스도 시험하였다.

USB 장치 자체는 kernel에서 인식되었다.

Burr-Brown/TI USB Audio CODEC의 VID/PID도 확인되었으나 kernel log에는 다음 메시지가 나타났다.

```text
device v08bb p2902 is not supported
```

또한:

```text
/proc/asound/cards
--- no soundcards ---
```

였다.

즉 USB 장치의 일부 HID interface는 인식했지만 USB audio interface는 ALSA sound card로 등록되지 않았다.

따라서 이것은 단순히 Android의 `audio_policy.conf`를 수정해서 해결할 문제가 아니다. kernel 또는 USB audio driver 수준의 작업이 필요할 가능성이 높다.

Bluetooth 오디오가 이미 잘 작동하므로 v0.3에서는 USB 오디오 지원을 더 이상 추구하지 않기로 하였다.

---

## 17. 시계 오버레이

v0.3에는 간단한 디지털 시계를 추가하였다.

표시 형식은:

```text
HH:mm
```

이다.

초 단위는 표시하지 않는다.

따라서 매초 화면을 갱신할 필요도 없다. 다음 분이 시작된 직후에만 시계를 갱신하도록 하였다.

오래된 EO1 하드웨어에서 불필요한 작업을 줄이는 데에도 적합하다.

시계는 Gallery 콘텐츠보다 위에 표시되며 progress indicator가 나타나더라도 그 위에 유지된다.

최종적으로 v0.3에서는 **시계를 기본 ON**으로 하였다.

즉 앱이 시작되면:

```text
Local Gallery
Clock ON
```

상태가 된다.

시계를 끄고 싶으면 우클릭 메뉴에서:

```text
Clock: Off
```

를 선택한다.

시계가 꺼져 있는 경우에는 메뉴가:

```text
Clock: On
```

으로 바뀐다.

메뉴 문구는 현재 상태가 아니라 **선택했을 때 실행할 동작**을 나타낸다.

시계 상태 역시 영구 저장하지 않는다. 새로 앱을 실행하면 다시 기본값인 ON으로 돌아온다.

---

## 18. Rescan Media

초기 버전에서는 앱을 시작할 때 미디어 디렉토리를 한 번 읽었다.

따라서 ADB 등을 이용하여 파일을 새로 넣거나 삭제하면 앱을 재시작해야 목록에 반영되었다.

v0.3에서는 우클릭 메뉴에:

```text
Rescan Media
```

를 추가하였다.

이를 선택하면:

```text
/sdcard/EO1-Museum/images
```

를 다시 읽고, 목록을 섞고, media index를 초기화한 뒤 새 목록으로 재생을 시작한다.

따라서 미디어 파일을 관리하기 위해 앱 전체를 다시 시작할 필요가 없어졌다.

---

## 19. 키보드 제어

개발과 테스트를 위해 키보드 조작도 남겨 두었다.

현재 주요 키는 다음과 같다.

```text
Space -> Next
M     -> Menu
L     -> Local Gallery
P     -> PC Gallery
R     -> Rescan Media
```

일반적인 디지털 액자 사용에는 필요하지 않지만 개발이나 점검에는 편리하다.

---

## 20. EO1 상단 터치키 문제

EO1 상단의 터치 버튼은 Android에서 다음과 같은 key code를 발생시키는 것으로 확인하였다.

```text
132
134
```

문제는 이 이벤트가 경우에 따라 매우 많은 횟수로 연속 발생한다는 것이다.

한때 이 키를 이용하여 화면 밝기 등을 조절하려 하였으나 화면이 어두워지거나 동작이 불안정해지는 문제가 생겼다.

진단 로그 역시 불필요하게 커졌다.

따라서 v0.3에서는 이 두 key code를 완전히 무시한다.

```text
132 -> ignore
134 -> ignore
```

로그에도 기록하지 않는다.

화면 밝기는 EO1과 Android 자체의 기능에 맡긴다.

---

## 21. 진단 로그

개발 과정에서 다음 파일에 진단 로그를 기록하도록 하였다.

```text
/sdcard/EO1-Museum/mouse_log.txt
```

특히 다음 문제를 해결하는 데 유용했다.

- 마우스 우클릭 인식
- 중복 mouse event
- 메뉴 호출 여부
- 이미지 timer
- 동영상 재생 상태
- 미디어 선택
- EO1 상단 터치키의 event burst

v0.3에서도 이 기능은 그대로 남겨 두었다.

동작 부담이 크지 않고 향후 문제가 생겼을 때 유용하기 때문이다.

완전히 정리된 production build를 별도로 만들게 된다면 나중에 제거하거나 축소할 수 있다.

---

## 22. WebView 설정

PC Gallery의 WebView는 의도적으로 단순하게 구성하였다.

JavaScript를 사용할 수 있도록 설정하고 `WebViewClient`를 지정하였다.

따라서 웹 페이지 안에서 이루어지는 navigation이 외부 브라우저를 실행하지 않고 앱 내부에 머문다.

WebView 배경은 검은색으로 설정하였다.

디지털 작품을 표시하는 장치에서는 흰색 화면이 잠시 나타나는 것보다 검은색이 훨씬 자연스럽다.

---

## 23. PC Gallery를 기본 모드로 하지 않는 이유

PC Gallery는 HTML, CSS, JavaScript를 자유롭게 사용할 수 있기 때문에 Local Gallery보다 훨씬 다양한 기능을 구현할 수 있다.

하지만 외부 조건이 필요하다.

```text
Wi-Fi
PC
HTTP server
정확한 IP 주소
```

반면 Local Gallery는 EO1만 있으면 된다.

따라서 EO1 Museum의 기본 기능은 어디까지나 Local Gallery이며, PC Gallery는 필요할 때 사용하는 확장 기능으로 정의하였다.

PC가 꺼져 있어도 EO1은 정상적인 디지털 액자로 사용할 수 있어야 한다.

---

## 24. PC 서버 주소

현재 소스에는 다음 주소가 들어 있다.

```text
http://192.168.1.103:8000/
```

현재는 hard-coded 값이다.

PC의 IP 주소가 바뀌면 소스의 주소를 수정하여 다시 빌드하거나, PC가 항상 같은 IP를 사용하도록 네트워크를 설정해야 한다.

향후 설정 메뉴에서 주소를 변경할 수 있도록 만드는 방법도 생각할 수 있다.

그러나 현재 사용 환경에서는 꼭 필요한 기능이 아니므로 v0.3을 복잡하게 만들지 않기 위해 넣지 않았다.

---

## 25. ADB와 USB 연결 문제

EO1에는 사실상 하나의 micro-USB OTG 연결부가 있다.

개발 중에는 이 때문에 다음 두 용도가 충돌한다.

```text
PC USB / ADB
       vs.
OTG mouse
```

ADB 케이블과 OTG 마우스를 반복해서 교체하는 과정에서 USB 연결이 불안정해지는 현상도 경험하였다.

때로는:

- `adb devices`에는 나타나지만 shell이 응답하지 않거나,
- Windows에서 USB 장치 자체가 사라지거나,
- USB 연결음조차 나지 않는

상황이 발생하였다.

Windows가 USB 장치 자체를 인식하지 않는 경우에는 `adb kill-server` 같은 명령으로 해결할 문제가 아니다.

실제 복구에는 다음 방법이 효과적이었다.

1. OTG 장치와 USB 케이블을 모두 제거한다.
2. 약간 기다린다.
3. PC USB 케이블만 연결한다.
4. 그래도 Windows가 인식하지 않으면 micro-USB 포트를 비운 상태에서 EO1을 재부팅한다.
5. Android 부팅 후 PC USB를 다시 연결한다.

그러나 이것은 어디까지나 **개발 과정의 문제**이다.

배포된 EO1 Museum 자체는 ADB를 필요로 하지 않는다.

---

## 26. Wi-Fi ADB

개발 과정에서는 USB 포트를 다른 장치가 차지하고 있을 때 Wi-Fi ADB도 사용하였다.

예를 들면:

```text
adb tcpip 5555
adb connect <EO1-IP>:5555
```

방식이다.

정상적으로 작동하지만 재부팅 후에는 유지되지 않는다.

또한 IP 주소 확인 등 번거로운 과정이 필요하다.

따라서 개발에는 여전히 USB ADB가 더 단순하며 Wi-Fi ADB는 필요한 경우에만 사용하는 보조 수단으로 남겨 두었다.

---

## 27. USB 저장장치의 한계

USB flash drive도 시험하였다.

USB device 자체는 kernel에서 인식하지만 stock Android kernel에는 필요한 SCSI block device 지원이 빠져 있었다.

kernel configuration에서는 다음을 확인하였다.

```text
# CONFIG_SCSI is not set
```

따라서 USB 메모리를 연결해도:

```text
/dev/sda
/dev/sda1
```

같은 일반 block device가 생성되지 않는다.

즉 stock Android 상태에서 USB 메모리를 Gallery 저장공간으로 사용하는 것은 어렵다.

v0.3은 내부 eMMC 저장공간을 사용한다.

이것은 앱의 문제가 아니라 kernel 수준의 제약이다.

---

## 28. Linux USB boot는 별도의 과제로

EO1에서 Linux를 USB로 부팅한 커뮤니티 사례가 존재하며 이 프로젝트에서도 이를 시험하였다.

Yocto와 Boundary Devices/Nitrogen6X 계열 이미지를 이용하여 여러 방법을 시도했지만 현재 보유한 EO1에서는 계속 Android가 부팅되었다.

정확한 image, U-Boot 구성, partition 구조 또는 boot trigger가 맞지 않았을 가능성이 있다.

그러나 이제 Android 위에서 EO1 Museum이 필요한 기능을 거의 모두 제공하므로 Linux 부팅은 이 프로젝트의 필수 조건이 아니다.

언젠가 다시 도전해 볼 **아주 먼 미래의 별도 프로젝트**로 남겨 둔다.

---

## 29. 빌드 환경

현재 정상적으로 동작하는 빌드 환경은 다음과 같다.

```text
Gradle 7.5
Android Gradle Plugin 7.4.1
JVM 17
```

Gradle wrapper:

```text
https://services.gradle.org/distributions/gradle-7.5-bin.zip
```

빌드된 debug APK는 다음 위치에 생성된다.

```text
app/build/outputs/apk/debug/app-debug.apk
```

ADB를 이용하면 다음과 같이 설치할 수 있다.

```text
adb install -r app-debug.apk
```

개발 중 반복적인 `install -r`은 HOME 기본 앱 선택에 영향을 줄 수 있으므로 최종 APK 설치 후에는 EO1 Museum이 기본 HOME 앱인지 확인하는 것이 좋다.

---

## 30. 앱의 이름과 package

현재 package name은 원래 프로젝트의 것을 그대로 사용한다.

```text
com.dan.eo1
```

기능적으로 이를 변경할 이유는 없다.

사용자에게 보이는 앱 이름은:

```text
EO1 Museum
```

으로 정리할 수 있다.

이미 안정적으로 작동하는 package 구조를 불필요하게 바꾸지 않는 것이 낫다.

---

## 31. v0.3 최종 동작

현재 v0.3의 기본 동작을 정리하면 다음과 같다.

```text
POWER ON
   |
   v
Android 부팅
   |
   v
EO1 Museum 자동 실행
   |
   v
Local Gallery
   |
   +--> Clock ON
   |
   +--> JPG/JPEG/PNG/MP4 무작위 재생
   |
   +--> 이미지 : 15초
   |
   +--> cross-fade : 2초
   |
   +--> MP4 : 끝까지 재생
   |
   +--> Bluetooth audio
   |
   +--> 마우스 우클릭 -> 제어 메뉴
```

제어 메뉴에서는:

```text
✓ Local Gallery
  PC Gallery
  Next
  Rescan Media
  Clock: Off
```

와 같이 현재 상태를 확인할 수 있다.

PC Gallery로 전환하면:

```text
  Local Gallery
✓ PC Gallery
  Next
  Rescan Media
  Clock: Off
```

형태가 된다.

PC Gallery에서 `Next`와 `Rescan Media`는 비활성화된다.

새로 앱을 실행하거나 재부팅하면 다시 Local Gallery로 돌아온다.

---

## 32. v0.3으로 불필요해진 것

초기의 실험적 구성과 비교하면 이제 일상적인 사용에 다음 요소가 필요하지 않다.

- Electric Objects의 서버
- MetBoot
- Firefox
- ADB
- 개발용 PC
- Local Gallery를 위한 PC 웹 서버
- USB 저장장치
- USB 오디오
- 별도의 Linux 설치

Local Gallery를 사용하는 데 필요한 최소 구성은 사실상 다음뿐이다.

```text
EO1
+
EO1 Museum
+
내부 저장소의 미디어 파일
```

마우스는 설정을 바꿀 때 유용하지만 Gallery 재생 자체에는 필요하지 않다.

Bluetooth 오디오도 선택 사항이다.

PC 역시 PC Gallery를 사용할 때만 필요하다.

---

## 33. 버전별 발전 과정

지금까지의 Native Gallery 개발 과정은 다음과 같이 정리할 수 있다.

```text
v0.1
Native image gallery
        |
        v
v0.2
Native image + MP4 playback
        |
        v
v0.3
EO1 Museum
Local + PC Gallery
Mouse control
Current mode indicator
Cross-fade
Clock
Automatic startup
Bluetooth multimedia
```

v0.1은 EO1을 다시 독립적인 이미지 액자로 만들 수 있다는 것을 확인한 버전이었다.

v0.2에서는 이미지뿐 아니라 동영상과 음성까지 다룰 수 있게 되었다.

그리고 v0.3에서는 그동안 개별적으로 시험하던 기능을 하나의 앱으로 묶었다.

이제는 단순한 proof of concept라기보다 실제로 계속 켜 두고 사용할 수 있는 프로그램이 되었다.

---

## 34. 앞으로 생각해 볼 기능

현재 상태만으로도 실사용에는 충분하다.

추가 기능은 더 이상 필수 사항이라기보다는 선택적인 개선 사항이다.

예를 들면 다음과 같다.

- PC Gallery URL 설정 기능
- 별도의 Settings dialog
- 시작 splash 화면
- 이미지 표시 시간 설정
- cross-fade 시간 설정
- 미디어 디렉토리 선택
- WebView 연결 오류 처리
- PC server 자동 검색
- 메뉴 디자인 개선
- 진단 로그 축소 또는 제거
- 정식 release APK signing
- 더 다양한 MP4 형식 시험
- Linux USB boot 재도전

이런 기능을 넣지 않았다고 해서 v0.3이 미완성인 것은 아니다.

오히려 현재 정도에서 기능 추가를 멈추고 안정된 버전을 보존하는 것이 좋을 수도 있다.

---

## 35. 맺음말

Electric Objects의 공식 서비스는 사라졌지만 EO1이라는 하드웨어 자체는 여전히 멀쩡하다.

처음 이 프로젝트를 시작했을 때의 질문은 사실 단순했다.

> 서버가 사라진 EO1을 다시 쓸 수 있을까?

처음에는 PC에서 HTTP server를 띄우고 EO1의 브라우저로 접속하는 정도만으로도 꽤 만족스러웠다. 그러나 ADB 접근이 가능해지고, 원래 Gallery 앱의 소스를 빌드할 수 있게 되면서 상황이 달라졌다.

이미지를 EO1 자체에서 직접 표시할 수 있게 되었고, MP4도 재생할 수 있게 되었다. Bluetooth를 연결하니 음성도 나왔다. 여기에 PC Gallery를 WebView로 통합하고, 마우스 메뉴와 시계, cross-fade까지 추가하였다.

이제 EO1을 켜면 별다른 조작 없이 바로 Local Gallery가 시작된다.

필요하면 우클릭 한 번으로 PC Gallery로 바꿀 수 있다.

공식 서버도 필요 없고 Firefox도 필요 없다.

따라서 v0.3에 와서는 처음의 질문도 조금 달라졌다.

> EO1을 다시 살릴 수 있는가?

가 아니라,

> 이제 그냥 다시 써도 되는가?

가 되었다.

**그 답은 이제 ‘그렇다’고 해도 될 것 같다.**

EO1 Museum v0.3은 이 프로젝트의 첫 번째 실사용 배포판이다.
