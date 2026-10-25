# EO1-Museum Native Gallery v0.2 — MP4 동영상 재생

**Date:** 2026-10-25  
**Working directory:** `EO1-main_v0.2`  
**Previous version:** v0.1  
**Result:** 성공

---

## 1. 목적

EO1-Museum v0.1에서는 EO1 내부 저장공간에 저장된 JPG/JPEG/PNG 이미지를 읽어 무작위 순서로 15초씩 표시하는 네이티브 Android Gallery를 구현하였다.

v0.2의 첫 번째 목표는 이 구조를 확장하여 이미지와 MP4 동영상을 같은 디렉터리에 저장하고 하나의 미디어 목록으로 재생하는 것이었다.

목표 동작은 다음과 같다.

```text
JPG/PNG
   ↓ 15초
JPG/PNG
   ↓ 15초
MP4
   ↓ 동영상 끝까지 재생
JPG/PNG
   ↓ 15초
...
```

이미지는 기존처럼 15초 동안 표시하지만, 동영상은 15초 타이머의 영향을 받지 않고 파일의 끝까지 재생한 뒤 다음 미디어로 넘어가도록 하는 것이 핵심이다.

---

## 2. 개발 기준

v0.1의 실제 EO1 동작이 이미 확인되었으므로 기존 코드를 직접 변경하지 않고 전체 개발 디렉터리를 복사하여 다음 작업 디렉터리를 만들었다.

```text
EO1-main_v0.2
```

따라서 v0.1은 known-good 상태로 보존하고, MP4 관련 변경은 v0.2에서만 수행하였다.

v0.2에서도 미디어 저장 위치는 기존과 동일하게 유지하였다.

```text
/sdcard/EO1-Museum/images/
```

별도의 `videos` 디렉터리를 만들지 않고 이미지와 동영상을 하나의 디렉터리에 함께 두도록 하였다.

---

## 3. v0.1 코드의 한계

v0.1에서는 이미지 목록을 `imageFiles`에 저장하고 `Handler`와 `Runnable`을 이용하여 15초마다 다음 이미지를 표시하였다.

개념적으로 다음과 같은 구조였다.

```text
showNextImage()
      ↓
15초 대기
      ↓
showNextImage()
      ↓
15초 대기
```

이 구조에 MP4 파일을 단순히 추가하면 동영상 역시 15초 뒤에 다음 파일로 넘어갈 가능성이 있다.

따라서 v0.2에서는 미디어 종류에 따라 다음 파일로 넘어가는 조건을 다르게 처리하도록 구조를 변경하였다.

- 이미지: 15초 후 다음 미디어
- 동영상: 재생 완료 후 다음 미디어

---

## 4. 미디어 목록으로 확장

기존의 이미지 전용 목록:

```java
List<File> imageFiles
```

을 이미지와 동영상을 함께 담는 목록으로 변경하였다.

```java
List<File> mediaFiles
```

디렉터리를 스캔할 때 다음 확장자를 미디어 파일로 인식한다.

```text
.jpg
.jpeg
.png
.mp4
```

목록을 읽은 뒤에는 v0.1과 마찬가지로 `Collections.shuffle()`을 이용하여 순서를 무작위로 섞는다.

따라서 한 번의 재생 cycle 안에서는 같은 파일을 반복하지 않고 모든 미디어를 한 번씩 재생한 뒤, 목록의 끝에 도달하면 다시 shuffle하여 새로운 순서로 재생한다.

---

## 5. 이미지와 동영상의 재생 방식 분리

다음 미디어를 선택하는 `showNextMedia()`에서 파일 확장자를 확인한다.

MP4이면:

```text
showVideo()
```

그 외 JPG/JPEG/PNG이면:

```text
showImage()
```

를 호출한다.

### 이미지

이미지는 기존 v0.1과 마찬가지로 `BitmapFactory.decodeFile()`을 이용하여 읽고 `ImageView`에 표시한다.

이미지가 표시된 후:

```java
handler.postDelayed(nextMediaRunnable, SLIDE_INTERVAL);
```

을 호출하여 15초 뒤 다음 미디어로 이동한다.

`SLIDE_INTERVAL`은 다음과 같다.

```java
private static final long SLIDE_INTERVAL = 15000;
```

즉 이미지 한 장의 기본 표시 시간은 15초이다.

### 동영상

MP4 파일을 만났을 때에는 `ImageView`를 숨기고 `VideoView`를 표시한다.

```java
videoView.setVideoURI(Uri.fromFile(file));
```

로 동영상 파일을 지정하고, `OnPreparedListener`에서 실제 재생을 시작한다.

```java
videoView.start();
```

중요한 점은 MP4를 재생할 때에는 15초짜리 `Handler` 타이머를 예약하지 않는다는 것이다.

대신:

```java
videoView.setOnCompletionListener(...)
```

를 이용하여 동영상이 끝난 것을 확인한 뒤 `showNextMedia()`를 호출한다.

따라서 동영상의 길이가 10초이든 몇 분이든 전체 파일을 재생한 후 다음 미디어로 이동한다.

---

## 6. 테스트 동영상

v0.2의 첫 실제 테스트에는 다음 파일을 사용하였다.

```text
20260426 Fluid Ardule - Test of April 26, 2026 vertical(1).mp4
```

이 파일은 EO1 화면에 맞게 제작된 세로형 동영상이다.

확인된 주요 사양은 다음과 같다.

| 항목 | 사양 |
|---|---|
| Container | MP4 |
| Video codec | H.264 / AVC |
| Resolution | 1080 × 1920 |
| Orientation | Portrait |
| Frame rate | 30 fps |
| Pixel format | yuv420p |
| Video bitrate | 약 15.8 Mbps |
| Audio codec | AAC |
| Audio sample rate | 48 kHz |
| Audio channels | Stereo |
| Duration | 약 48초 |
| File size | 약 96 MB |

특히 해상도가 `1080 × 1920`으로 EO1의 세로형 Full HD 화면과 일치한다.

Android 4.4.2에서 호환성이 좋은 H.264/AVC + AAC 조합이며, 실제 EO1의 `VideoView`에서 정상 재생되는 것을 확인하였다.

약 15.8 Mbps의 비교적 높은 비트레이트임에도 실제 EO1에서 재생에 성공했다는 점도 의미가 있다.

따라서 적어도 다음 조건의 MP4는 실제 EO1에서 재생 가능함이 확인되었다.

```text
MP4 container
H.264 / AVC video
AAC audio
1080 × 1920
30 fps
yuv420p
약 15.8 Mbps
```

이는 해당 조건을 EO1의 절대적인 재생 한계로 확인했다는 의미는 아니다. 이번 실험에서는 위 사양의 특정 파일이 실제 EO1에서 정상적으로 재생되었다는 것을 의미한다.

---

## 7. EO1로 미디어 복사

테스트 파일은 ADB를 이용하여 기존 미디어 디렉터리에 복사하였다.

```text
/sdcard/EO1-Museum/images/
```

처음에는 기존 JPG 파일이 많이 들어 있었기 때문에 shuffle된 목록에서 MP4가 언제 나올지 기다려야 하는 문제가 있었다.

따라서 MP4 테스트를 쉽게 하기 위해 기존 미디어를 임시로 정리하고 JPG 5개와 MP4 1개 정도만 남겨 시험하였다.

테스트 구성은 다음과 같다.

```text
/sdcard/EO1-Museum/images/

    image01.jpg
    image02.jpg
    image03.jpg
    image04.jpg
    image05.jpg
    20260426 Fluid Ardule - Test of April 26, 2026 vertical(1).mp4
```

총 6개의 미디어만 사용함으로써 짧은 시간 안에 MP4 재생 여부를 확인할 수 있었다.

---

## 8. 미디어 목록 갱신 시 주의사항

현재 v0.2에서는 미디어 디렉터리 스캔을 앱의 `onCreate()`에서 수행한다.

따라서 Gallery가 이미 실행 중인 상태에서 ADB를 이용하여 파일을 추가하거나 삭제하더라도 현재 메모리에 들어 있는 `mediaFiles` 목록에는 즉시 반영되지 않는다.

파일을 변경한 뒤에는 앱을 다시 실행해야 한다.

예:

```text
adb shell am force-stop com.dan.eo1
adb shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

재실행하면 `/sdcard/EO1-Museum/images/`를 다시 스캔하여 현재 파일 목록을 읽는다.

향후 마우스 제어 메뉴를 구현할 경우 다음 기능을 추가하는 것이 유용할 것으로 보인다.

```text
Rescan media
```

이를 이용하면 앱을 종료하지 않고도 미디어 목록을 다시 읽을 수 있다.

---

## 9. 실제 EO1 테스트 결과

`EO1-main_v0.2`에서 수정된 코드를 빌드하였으며 컴파일 오류 없이 APK 생성에 성공하였다.

APK를 EO1에 설치하고 JPG 파일과 테스트 MP4를 `/sdcard/EO1-Museum/images/`에 복사한 뒤 Gallery를 다시 실행하였다.

실제 EO1에서 다음 동작을 확인하였다.

```text
이미지 표시
    ↓
15초 후 다음 미디어
    ↓
이미지 표시
    ↓
MP4 선택
    ↓
VideoView 전환
    ↓
MP4 동영상 정상 재생
    ↓
동영상 종료
    ↓
다음 이미지로 자동 복귀
```

따라서 이미지와 MP4를 하나의 shuffle 목록에서 혼합 재생하는 v0.2의 핵심 기능이 실제 EO1에서 정상적으로 동작함을 확인하였다.

---

## 10. v0.2의 현재 기능

v0.2에서 확인된 기능은 다음과 같다.

- Android 4.4.2 기반 EO1에서 네이티브 실행
- HOME 앱으로 사용
- 부팅 후 자동 실행
- 네트워크 없이 독립 실행
- EO1 내부 저장공간의 미디어 사용
- JPG 지원
- JPEG 지원
- PNG 지원
- MP4 지원
- 이미지 15초 표시
- MP4 전체 길이 재생
- 이미지와 동영상 혼합 shuffle
- cycle 내 중복 없는 재생
- cycle 종료 후 재-shuffle
- 동영상 종료 후 다음 이미지/미디어 자동 재생
- Space 키를 이용한 다음 미디어 이동
- EO1 상단 하드웨어 버튼 처리
- 화면 상단을 내려 Android 시스템 UI 및 설정 접근 가능

---

## 11. v0.1에서 v0.2로의 변화

v0.1의 구조는 다음과 같았다.

```text
EO1 Gallery
    ↓
Local image directory
    ↓
JPG / JPEG / PNG
    ↓
15-second randomized slideshow
```

v0.2에서는 다음과 같이 확장되었다.

```text
EO1 Gallery
    ↓
Local media directory
    ↓
Randomized media list
    │
    ├── JPG/JPEG/PNG
    │       ↓
    │     15 sec
    │
    └── MP4
            ↓
       play to completion
            ↓
        next media
```

따라서 EO1-Museum은 단순한 이미지 슬라이드쇼에서 로컬 이미지와 동영상을 함께 감상할 수 있는 네이티브 미디어 Gallery로 발전하였다.

---

## 12. 다음 개발 후보

v0.2의 핵심 목표인 MP4 재생은 달성하였다.

다음 버전에서 고려할 기능은 다음과 같다.

1. 마우스 오른쪽 클릭으로 제어 메뉴 호출
2. `Next` — 다음 미디어
3. `Rescan media` — 저장공간의 미디어 목록 다시 읽기
4. `Web mode` — Firefox를 실행하여 PC 웹 서버의 콘텐츠 표시
5. `Android Settings` — 시스템 설정 접근
6. 필요하면 Local Gallery로 명시적으로 복귀
7. 시작 시 간단한 splash screen 표시
8. 이미지 전환 시 짧고 절제된 cross-fade 효과

평상시에는 이러한 UI가 화면에 보이지 않고 작품만 표시하는 것을 기본 원칙으로 한다.

마우스는 상시 연결하지 않고 설정이나 모드 변경이 필요한 경우에만 연결하는 방식이 적합하다.

---

## 13. v0.2의 의미

v0.1에서 EO1은 제조사의 서버, Firefox, PC 웹 서버 및 인터넷 연결 없이도 독립적으로 작품 이미지를 표시할 수 있는 장치가 되었다.

v0.2에서는 여기에 로컬 MP4 동영상 재생 기능이 추가되었다.

특히 1080 × 1920 H.264/AAC MP4 파일이 실제 EO1에서 정상적으로 재생됨으로써, EO1의 Full HD 세로 화면을 정지 이미지뿐 아니라 동영상 작품에도 활용할 수 있음을 확인하였다.

현재의 기본 동작은 매우 단순하다.

```text
전원 연결
    ↓
Android 부팅
    ↓
EO1 Gallery 자동 실행
    ↓
로컬 미디어 검색
    ↓
이미지 + 동영상 자동 감상
```

PC, 웹 서버 또는 네트워크는 기본 동작에 필요하지 않다.

향후 Web mode가 추가되더라도 Local Gallery를 기본 동작으로 유지하고, 웹 콘텐츠는 필요할 때만 선택적으로 사용하는 구조가 적절하다.

---

## 14. 결론

2026-10-25, `EO1-main_v0.2`에서 JPG/JPEG/PNG 이미지와 MP4 동영상을 하나의 미디어 목록으로 혼합하여 재생하는 기능을 구현하였다.

이미지는 15초 동안 표시하고, MP4는 전체 길이를 재생한 뒤 자동으로 다음 미디어로 이동한다.

테스트에 사용한 1080 × 1920, 30 fps, H.264/AVC + AAC MP4 동영상은 실제 Electric Objects EO1에서 정상적으로 재생되었다.

따라서 EO1-Museum Native Gallery v0.2의 핵심 목표인 **로컬 이미지와 MP4 동영상의 혼합 재생**은 성공하였다.
