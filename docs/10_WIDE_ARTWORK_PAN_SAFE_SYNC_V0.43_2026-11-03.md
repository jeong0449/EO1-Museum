# EO1 Museum v0.43 --- Wide Artwork Pan Video와 Safe Sync 확장

**작성일:** 2026-11-03\
**프로젝트:** EO1 Museum\
**대상 기기:** Electric Objects EO1\
**패키지:** `com.dan.eo1`\
**버전:** v0.43

------------------------------------------------------------------------

## 1. 개요

v0.41까지의 개발에서는 EO1의 graphics stack을 조사하고, 정지 이미지와
generative artwork를 EO1에서 안정적으로 보여 주기 위한 기본 원칙을
정리하였다. 특히 복잡한 animation은 PC에서 MP4로 미리 렌더링하고 EO1은
image/video playback에 집중하는 구조가 효과적임을 확인하였다.

이후 실제 미술 작품을 전시하면서 새로운 문제가 드러났다. EO1은 1080 ×
1920의 세로형 화면이므로, 가로로 긴 작품을 `contain` 방식으로 표시하면
작품 전체는 보이지만 화면에서 차지하는 면적이 지나치게 작아진다.

v0.43에서는 이 문제를 해결하기 위해 **가로로 긴 작품에 대해 PC에서 pan
video를 미리 생성하고, Network Gallery와 Local Gallery 모두에서 이를
재생하는 구조**를 도입하였다. 또한 Safe Sync를 확장하여 원본 이미지와
pan용 companion media를 하나의 작품 단위로 EO1에 전달하도록 하였다.

핵심 흐름은 다음과 같다.

``` text
wide artwork
    ↓
make_gallery.py
    ↓
display/NNNN.jpg
display/pan_NNNN.jpg
    ↓
make_pan_videos.py
    ↓
display/pan_NNNN.mp4
    ↓
PC Gallery
    ├─ Network playback
    └─ Safe Sync
           ↓
/sdcard/EO1-Museum/images/
           ↓
Local Gallery
```

------------------------------------------------------------------------

## 2. 가로로 긴 작품의 문제

세로형 EO1 화면에서 일반 작품은 전체 이미지를 그대로 표시해도 감상에 큰
문제가 없다. 그러나 landscape 비율이 큰 작품은 화면 중앙에 작은 띠처럼
나타난다.

``` text
EO1 display
1080 × 1920 portrait

┌──────────────┐
│              │
│              │
│ ──────────── │  ← wide artwork
│              │
│              │
└──────────────┘
```

단순히 확대하여 화면을 채우면 작품의 좌우가 잘리므로 전체 구성을 볼 수
없다. 따라서 두 가지 관점을 함께 제공하는 것이 적합하다.

``` text
Full view
    -> 작품 전체 구도 확인

Detail pan
    -> 확대된 상태에서 왼쪽부터 오른쪽까지 감상
```

이를 위해 wide artwork에는 일반 이미지 외에 pan용 media를 companion으로
생성한다.

------------------------------------------------------------------------

## 3. wide artwork의 companion media

가로로 긴 작품 하나는 다음과 같은 파일 집합으로 표현된다.

``` text
display/0017.jpg
display/pan_0017.jpg
display/pan_0017.mp4
```

각 파일의 역할은 다음과 같다.

``` text
0017.jpg
    -> 작품 전체를 보여 주는 기본 이미지

pan_0017.jpg
    -> 확대된 detail view의 source/fallback image

pan_0017.mp4
    -> 왼쪽에서 오른쪽으로 이동하는 pre-rendered pan video
```

`pan_*.jpg`라는 이름은 초기 구현에서 유래한 것이며, 현재는 단순한 별도
작품이 아니라 해당 base artwork에 종속된 companion image이다.

따라서 gallery에서 이 세 파일을 각각 독립된 작품으로 취급해서는 안 된다.

------------------------------------------------------------------------

## 4. make_pan_videos.py

pan video는 EO1에서 실시간으로 이미지를 이동시키지 않고 PC에서 미리
만든다.

기본 처리 흐름:

``` text
wide source image
    ↓
height 확인
    ↓
필요한 경우 1920 px로 downscale
    ↓
vertical center
    ↓
horizontal travel 계산
    ↓
FFmpeg
    ↓
20-second H.264 MP4
```

현재 기본 조건:

``` text
Duration       20 sec
Frame rate     30 fps
Codec          H.264 / libx264
CRF            20
Preset         veryfast
Pixel format   yuv420p
Container      MP4
faststart      enabled
```

원본의 세로 해상도가 1920보다 작으면 불필요한 upscale은 하지 않는다.

수평 이동은 frame에 따라 일정하게 진행한다.

``` text
Left edge
    ↓
continuous pan
    ↓
Right edge
```

이 방식은 EO1의 오래된 WebView에서 실시간 animation을 계산하게 하는
것보다 훨씬 안정적이다.

------------------------------------------------------------------------

## 5. PC browser와 EO1 WebView의 차이

PC browser에서는 일반 HTML5 `<video>` element로 `pan_*.mp4`를 재생할 수
있다.

그러나 EO1의 Android 4.4.2 WebView에서는 embedded HTML5 video가
안정적으로 동작하지 않았다. 같은 MP4 URL을 직접 열면 Android의 native
media player에서는 정상 재생되므로, 문제는 MP4 자체가 아니라 WebView의
video playback path에 있다고 판단하였다.

따라서 EO1에서는 다음과 같은 native bridge를 사용한다.

``` text
Network Gallery WebView
        ↓
JavaScript
window.EO1.playNetworkVideo(url)
        ↓
Android Java bridge
        ↓
Native VideoView
        ↓
HTTP MP4 playback
        ↓
eo1NativeVideoFinished()
        ↓
WebView gallery resume
```

즉 Network Gallery의 HTML/JavaScript는 작품 순서와 상태를 제어하고, 실제
MP4 decode와 display는 Android native `VideoView`가 담당한다.

------------------------------------------------------------------------

## 6. Network Gallery에서의 wide artwork 재생

wide artwork의 기본 감상 흐름은 다음과 같다.

``` text
Full artwork
    ↓
pan video
    ↓
Full artwork
    ↓
Next artwork
```

전체 이미지를 먼저 보여 주어 작품의 구도를 파악하게 한 뒤, 확대된 pan
video로 세부를 감상하고, 마지막에 다시 전체 이미지를 보여 준다.

Network Gallery에서 native video playback이 성공하면 약 20초 동안 pan이
재생되고 완료 callback 후 gallery가 정상적으로 이어진다.

이 구조의 중요한 점은 **Network Gallery 전체를 native application으로
다시 작성하지 않고 기존 WebView gallery에 필요한 video playback 기능만
native로 보완했다는 것**이다.

------------------------------------------------------------------------

## 7. MP4가 없을 때의 static fallback

모든 wide artwork에 반드시 MP4가 존재한다고 가정하지 않는다.

pan video가 없거나 재생할 수 없는 경우에는 `pan_*.jpg` 하나를 서로 다른
위치로 정렬하여 detail view를 만든다.

``` text
Full
  ↓
Left detail
  ↓
Center detail
  ↓
Right detail
  ↓
Full
  ↓
Next
```

각 단계 사이에는 cross-dissolve를 사용한다.

이 방식은 움직이는 pan만큼 연속적이지는 않지만, 별도의 video 없이도
가로로 긴 작품의 좌측, 중앙, 우측 세부를 차례로 볼 수 있게 한다.

따라서 wide artwork에는 두 단계의 fallback이 존재한다.

``` text
preferred
    pan_NNNN.mp4

fallback
    pan_NNNN.jpg
    -> Left / Center / Right
```

------------------------------------------------------------------------

## 8. Safe Sync의 확장

기존 Safe Sync는 PC Gallery의 media를 EO1 내부 저장공간으로 전달하여
PC가 꺼진 뒤에도 Local Gallery에서 감상할 수 있게 하는 기능이다.

v0.43에서는 wide artwork의 companion media까지 함께 전달하도록 Safe
Sync를 확장하였다.

이전의 단순한 관점:

``` text
1 file = 1 artwork
```

현재의 관점:

``` text
1 artwork
    ├─ base image
    ├─ optional pan image
    └─ optional pan MP4
```

따라서 `MAX_MEDIA_FILES`는 물리적인 파일 개수가 아니라 **base artwork의
수**를 제한하는 값으로 해석한다.

예를 들어:

``` text
MAX_MEDIA_FILES=100
```

이면 최대 100개의 base artwork를 선택하고, 그 작품에 해당하는
`pan_*.jpg`와 `pan_*.mp4`가 있으면 함께 sync한다.

실제 저장되는 파일 수는 100개보다 많을 수 있다.

------------------------------------------------------------------------

## 9. Safe Sync는 EO1 pull 방식

`server.py --sync`는 PC에서 EO1로 파일을 직접 push하지 않는다.

PC server는 `/eo1-status`에서 Safe Sync가 허용되었음을 알린다.

``` text
EO1M-8F29C74A
SYNC=1
```

EO1 application은 이 상태를 확인한 뒤 `images.js`를 읽고 필요한 media를
PC server에서 다운로드한다.

``` text
PC
server.py --sync
    ↓
SYNC=1

EO1
    ↓
trusted server 확인
    ↓
images.js 읽기
    ↓
artwork 목록 결정
    ↓
base + companion media download
```

즉 Safe Sync의 실제 전송 방향은 다음과 같다.

``` text
EO1  ←pull—  PC server
```

------------------------------------------------------------------------

## 10. 항상 덮어쓰는 sync 정책

EO1-Museum에서는 PC의 `display/`를 전시 media의 source of truth로 본다.

따라서 같은 이름의 파일이 EO1에 이미 존재하더라도 sync 시 새 파일을 다시
받아 덮어쓰는 정책을 사용한다.

``` text
PC display/
    ↓
download to temporary file
    ↓
download complete
    ↓
old target delete
    ↓
temporary file rename
    ↓
new target active
```

이 방식의 장점은 단순하다.

``` text
같은 filename
    ≠ 같은 content라고 가정하지 않음

PC에서 작품을 다시 생성
    ↓
다음 sync에서 EO1도 같은 상태로 갱신
```

중간에 다운로드가 실패한 파일을 바로 target으로 사용하지 않고 temporary
file을 거치므로 기존 파일을 가능한 한 안전하게 유지할 수 있다.

------------------------------------------------------------------------

## 11. 저장공간 보호

EO1의 내부 사용자 저장공간은 약 2.4 GB로 크지 않다.

현재 확인한 예:

``` text
/sdcard total       2.4 GB
used                1.8 GB
free                558 MB

EO1-Museum/images   206 MB
```

Safe Sync는 `.config`의 다음 값을 이용하여 최소 여유공간을 보존한다.

``` text
MIN_FREE_MB=200
```

따라서 companion MP4 때문에 예상보다 media 용량이 커지더라도, 여유공간이
설정된 한계 아래로 내려가기 전에 sync를 중단할 수 있다.

현재 기본값:

``` text
MAX_MEDIA_FILES=100
MIN_FREE_MB=200
```

은 그대로 유지한다.

------------------------------------------------------------------------

## 12. Local Gallery의 companion-aware playback

Safe Sync로 `pan_*.jpg`와 `pan_*.mp4`가 EO1에 저장되면 Local Gallery도
이를 독립된 작품으로 shuffle해서는 안 된다.

따라서 Local Gallery의 media list에서는 다음 파일을 base artwork와
분리한다.

``` text
0017.jpg
    -> artwork

pan_0017.jpg
    -> companion

pan_0017.mp4
    -> companion
```

shuffle 대상은 base artwork이다.

``` text
base artwork list
    ↓
shuffle
    ↓
show artwork
    ↓
companion 존재 여부 확인
```

wide artwork에 MP4가 있으면:

``` text
Full image
    ↓
15 sec
    ↓
pan MP4
    ↓
20 sec
    ↓
Full image
    ↓
5 sec
    ↓
Next artwork
```

MP4가 없으면 static fallback을 사용한다.

``` text
Full
    ↓
Left
    ↓
Center
    ↓
Right
    ↓
Full
    ↓
Next
```

이로써 Network Gallery에서 보던 wide artwork의 감상 방식이 Safe Sync
이후 Local Gallery에서도 유지된다.

------------------------------------------------------------------------

## 13. 전체 workflow

현재 wide artwork의 전체 workflow는 다음과 같이 정리된다.

``` text
The Met / other source
        ↓
original/
        ↓
make_gallery.py
        ↓
display/
    ├─ NNNN.jpg
    └─ pan_NNNN.jpg
        ↓
make_pan_videos.py
        ↓
display/pan_NNNN.mp4
        ↓
images.js
        ↓
PC Gallery
        │
        ├───────────────────────────────┐
        │                               │
        v                               v
Network Gallery                    Safe Sync
WebView                                │
        │                               │
        v                               v
JS native bridge             /sdcard/EO1-Museum/images/
        │                               │
        v                               v
Android VideoView                 Local Gallery
        │                               │
        v                               v
HTTP pan MP4                 Native image/video playback
```

PC가 켜져 있을 때에는 Network Gallery에서 바로 감상할 수 있고, Safe
Sync를 실행하면 같은 작품과 companion media가 EO1에 저장된다. 이후 PC
server가 없어도 Local Gallery에서 재생할 수 있다.

------------------------------------------------------------------------

## 14. v0.41 이후의 발전

``` text
v0.41
    Adjustable display interval
    EO1 graphics stack exploration
    Canvas/WebGL/CSS performance investigation
    HTML/JavaScript -> MP4 rendering workflow
        |
        v
v0.42
    Local / Network Gallery architecture refinement
    Safe Sync workflow stabilization
        |
        v
v0.43
    Wide artwork detection
    pan_*.jpg companion
    pre-rendered pan_*.mp4
    Network Gallery native VideoView bridge
    Safe Sync of base + companion media
    companion-aware Local Gallery playback
    static Left / Center / Right fallback
```

v0.41에서 얻은 원칙인

> **EO1이 잘하는 일은 EO1에게 맡기고, 복잡한 rendering은 PC에서
> 끝낸다.**

는 이번 wide artwork 처리에도 그대로 적용되었다.

실시간으로 큰 이미지를 WebView에서 부드럽게 이동시키는 대신 PC에서 pan
video를 만들고, EO1에서는 native video decoder로 재생한다.

------------------------------------------------------------------------

## 15. 현재의 media model

EO1-Museum의 media model은 이제 단순한 image/video file 목록보다 한 단계
확장되었다.

``` text
Artwork
    |
    +-- primary media
    |      JPEG / PNG / MP4
    |
    +-- optional companion media
           pan image
           pan video
```

이 구조는 향후 하나의 작품에 여러 representation을 연결하는 데에도
활용할 수 있다.

중요한 점은 **파일이 아니라 작품이 gallery의 기본 단위**라는 것이다.

------------------------------------------------------------------------

## 16. 맺음말

이번 수정으로 EO1-Museum은 세로형 화면에 불리했던 가로로 긴 작품을
단순히 작게 축소하여 보여 주는 데서 벗어났다.

PC에서는 wide artwork를 분석하여 pan용 image와 MP4를 미리 준비한다.
Network Gallery에서는 WebView와 native `VideoView`를 연결하여 pan
video를 재생한다. Safe Sync는 base artwork와 companion media를 함께
EO1에 저장하고, Local Gallery는 이를 하나의 작품으로 인식하여 같은 감상
순서로 재생한다.

``` text
Wide artwork
    ↓
Full composition
    ↓
Detail through pan
    ↓
Full composition
```

그리고 전달 경로는:

``` text
PC Gallery
    ↓
Safe Sync
    ↓
EO1 Local Gallery
```

로 이어진다.

따라서 이번 변경의 핵심은 단순히 MP4 playback을 하나 추가한 것이 아니다.
**가로로 긴 작품을 위한 표현 방식, PC에서의 사전 처리, 안전한 동기화,
EO1의 native playback을 하나의 일관된 artwork workflow로 연결했다는 데
의미가 있다.**
