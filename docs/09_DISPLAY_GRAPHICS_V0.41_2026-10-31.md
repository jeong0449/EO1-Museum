# EO1 Museum v0.41 --- Display Timing과 EO1 Graphics 탐색

**작성일:** 2026-10-30\
**프로젝트:** EO1 Museum\
**대상 기기:** Electric Objects EO1\
**패키지:** `com.dan.eo1`\
**버전:** v0.41

------------------------------------------------------------------------

## 1. 개요

v0.4에서는 PC Gallery와 Local Gallery를 Safe Sync로 연결하였다. PC에서
준비한 전시를 EO1 내부 저장공간으로 전달하고, 이후에는 PC 없이 Local
Gallery에서 감상할 수 있게 되었다.

v0.41에서는 두 가지 문제를 다루었다.

1.  Local Gallery의 이미지 표시 시간을 사용자가 조절할 수 있게 한다.
2.  EO1의 실제 graphics stack을 조사하여 HTML animation에 적합한
    rendering 방법을 찾는다.

v0.4가 콘텐츠 전달 경로를 만든 버전이었다면, v0.41은 실제 감상 경험과
EO1의 그래픽 능력을 탐색한 버전이다.

------------------------------------------------------------------------

## 2. 이미지 표시 시간 조절

개발 중에는 빠른 확인을 위해 약 16초의 전환 시간을 사용했지만, 실제 작품
감상에는 짧다. 반대로 긴 간격만 고정하면 개발과 테스트가 불편하다.

따라서 v0.41에서는 마우스 메뉴에서 다음 값을 선택할 수 있도록 하였다.

``` text
15 seconds
30 seconds
1 minute
2 minutes
```

일상적인 감상에는 **1 minute**을 기본값으로 두고, 15초와 30초는 테스트
또는 빠른 감상, 2분은 한 작품을 오래 볼 때 사용할 수 있다.

`Next`를 선택하면 설정된 시간이 남아 있어도 즉시 다음 작품으로 이동하며,
그 시점부터 timer를 다시 시작한다.

``` text
현재 작품
   |
   +---- Next ----> 다음 작품
                       |
                       +---- display timer restart
```

이미지 사이의 cross-fade는 기존처럼 약 2초를 유지한다. 따라서 **작품
표시 시간(display interval)**과 **전환 효과 시간(transition
duration)**은 서로 독립적이다.

------------------------------------------------------------------------

## 3. EO1 graphics stack 탐색

ADB를 이용한 탐색에서 EO1의 그래픽 환경에 대해 다음 사항을 확인하였다.

``` text
SoC              Freescale i.MX6 family
GPU              Vivante GC2000
OpenGL ES        2.0
Display          1080 × 1920 portrait
Android          4.4.2 KitKat
SurfaceFlinger   hardware-accelerated composition available
```

EO1은 단순한 framebuffer 장치가 아니다. GPU가 있으며 Android UI의
hardware acceleration도 동작한다.

따라서 중요한 질문은 "GPU가 있는가?"가 아니라 **오래된 Android 4.4.2의
각 API와 WebView가 GPU를 어떤 경로로 이용하는가?**이다.

------------------------------------------------------------------------

## 4. SurfaceFlinger와 hardware acceleration

Android의 최종 화면 합성은 SurfaceFlinger가 담당한다. EO1에서는
hardware-accelerated composition이 작동한다.

이미 rasterize된 layer의 위치, 크기, 투명도를 바꾸는 작업은 화면 전체
pixel을 CPU에서 매번 다시 그리는 것보다 유리하다.

이 특성은 HTML animation의 설계에도 그대로 적용된다.

------------------------------------------------------------------------

## 5. KitKat WebView에서 확인한 차이

오늘의 탐색에서 가장 중요한 결과는 다음과 같다.

``` text
Canvas 2D
    -> 매우 느림
    -> 테스트에서 약 4 fps

WebGL
    -> NOT AVAILABLE

CSS transform / translate3d
    -> 빠르게 동작
```

이 결과 때문에 EO1용 HTML animation은 Canvas 중심이 아니라 **DOM layer +
CSS transform/opacity 중심**으로 만드는 것이 적합하다.

------------------------------------------------------------------------

## 6. Canvas 2D가 불리한 이유

Canvas animation은 흔히 JavaScript가 매 frame 화면을 다시 그린다.

``` javascript
ctx.clearRect(0, 0, width, height);
ctx.drawImage(image, x, y);
```

EO1의 1080×1920 화면에서 이런 full-screen redraw를 계속 수행하면 CPU와
memory bandwidth에 부담이 크다. 실제 테스트에서는 약 4 fps 수준으로,
부드러운 animation에는 부족했다.

따라서 다음 구조는 피한다.

``` text
JavaScript loop
     |
     v
Canvas full-screen redraw
     |
     v
Canvas full-screen redraw
     |
     ...
```

Canvas를 정적인 그림 생성에 한 번 사용하는 것과, 매 frame 전체를 다시
그리는 것은 다른 문제이다. EO1에서는 후자가 특히 불리하다.

------------------------------------------------------------------------

## 7. OpenGL ES 2.0과 WebGL은 다르다

EO1의 Vivante GC2000은 OpenGL ES 2.0을 지원한다. 그러나 이것이 곧 KitKat
WebView에서 WebGL을 사용할 수 있다는 뜻은 아니다.

실제 WebView 탐색에서는 **WebGL을 사용할 수 없었다.**

따라서 현재 EO1 HTML 콘텐츠에서는 다음을 전제로 삼지 않는다.

``` text
WebGL
Three.js
WebGL shader animation
WebGL 기반 particle system
```

이것은 GPU 부재의 문제가 아니라 현재 WebView/browser software stack의
제약이다.

------------------------------------------------------------------------

## 8. translate3d가 잘 동작한 이유

반대로 CSS `transform`, 특히 `translate3d()`를 사용한 움직임은 빠르게
동작하였다.

``` css
.artwork {
    transform: translate3d(0, 0, 0);
}
```

animation에서는 다음과 같이 이동과 확대를 함께 사용할 수 있다.

``` css
transform: translate3d(0, -25px, 0) scale(1.04);
```

목적은 3D 장면을 만드는 것이 아니다. 이미 만들어진 layer를 compositor가
이동·확대·합성하도록 만드는 것이다.

``` text
불리한 방식

JavaScript
   -> pixel redraw
   -> Canvas


유리한 방식

HTML image/layer
   -> 한 번 rasterize
   -> CSS transform
   -> compositor/GPU composition
```

EO1에서는 두 번째 방식이 훨씬 현실적이다.

------------------------------------------------------------------------

## 9. EO1용 HTML animation의 기본 원칙

핵심 원칙은 다음 한 문장으로 정리할 수 있다.

> **그림을 계속 다시 그리지 말고, 이미 그려진 layer를 움직인다.**

animation 대상은 가능하면 다음과 같이 단순하게 한다.

``` text
<img>
<div>
background-image
pre-rendered graphic layer
```

주로 변경할 속성은:

``` text
transform
opacity
```

반대로 animation 중에 다음을 계속 변경하는 것은 줄인다.

``` text
width / height
top / left
background-size
복잡한 shadow
복잡한 filter
Canvas pixel redraw
```

layout과 repaint를 반복해서 일으키는 작업을 줄이는 것이 중요하다.

------------------------------------------------------------------------

## 10. CSS animation을 우선 사용

단순한 반복 animation이라면 JavaScript가 매 frame 좌표를 계산하기보다
CSS animation을 우선한다.

``` html
<div class="frame">
    <img class="artwork" src="art.jpg">
</div>
```

``` css
html, body {
    margin: 0;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
    background: black;
}

.frame {
    position: absolute;
    left: 0;
    top: 0;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
}

.artwork {
    width: 1080px;
    height: 1920px;
    object-fit: contain;
    transform: translate3d(0, 0, 0) scale(1.0);
    animation: drift 30s linear infinite alternate;
}

@keyframes drift {
    from {
        transform: translate3d(0, 0, 0) scale(1.0);
    }
    to {
        transform: translate3d(0, -25px, 0) scale(1.04);
    }
}
```

이 방식에서는 JavaScript가 pixel을 다시 만드는 것이 아니라, 이미
렌더링된 image layer의 transform만 바뀐다.

------------------------------------------------------------------------

## 11. Cross-fade도 opacity로 구현

HTML에서 두 이미지 사이를 부드럽게 바꿀 때에도 Canvas 합성보다 두
layer의 `opacity`를 바꾸는 것이 적합하다.

``` css
.slide {
    position: absolute;
    left: 0;
    top: 0;
    width: 1080px;
    height: 1920px;
    transition: opacity 2s ease;
    transform: translate3d(0, 0, 0);
}

.visible { opacity: 1; }
.hidden  { opacity: 0; }
```

``` text
Layer A   opacity 1 -> 0
Layer B   opacity 0 -> 1
```

현재 Native Gallery의 cross-fade와 같은 개념을 HTML에서도 비교적
효율적으로 구현할 수 있다.

------------------------------------------------------------------------

## 12. JavaScript의 역할은 state control

JavaScript를 피할 필요는 없다. 다만 JavaScript가 매 frame 그림을 그리는
역할을 하지 않도록 한다.

JavaScript에는 다음 역할이 적합하다.

``` text
어떤 작품을 표시할 것인가
언제 다음 작품으로 넘어갈 것인가
어떤 CSS class를 적용할 것인가
animation을 언제 시작/정지할 것인가
```

예:

``` javascript
current.className = "slide hidden";
next.className = "slide visible";
```

역할을 나누면 다음과 같다.

``` text
JavaScript
    -> state / timing control

CSS transform / opacity
    -> animation

browser compositor / GPU
    -> screen composition
```

JavaScript로 시간에 따라 값을 갱신해야 한다면
`requestAnimationFrame()`을 사용할 수 있지만, 이것으로 1080×1920 Canvas
전체를 계속 redraw하는 것은 피한다. `requestAnimationFrame()` 자체가
느린 Canvas rendering을 빠르게 만들어 주지는 않는다.

------------------------------------------------------------------------

## 13. 이미지 크기와 layer 수

EO1의 실제 화면은 1080×1920이다. raster image도 가능하면 필요한 크기에
가깝게 PC에서 미리 준비한다.

현재 `make_gallery.py`가 이미 이 역할을 한다.

``` text
original/
    |
    v
make_gallery.py
    |
    v
1080 × 1920 display image
```

매우 큰 원본을 WebView에서 반복적으로 축소하게 만들 필요가 없다.

또한 GC2000이 있다고 해서 현대 GPU처럼 많은 layer와 효과를 동시에 처리할
것으로 기대해서는 안 된다. 기본적으로 다음 정도의 단순한 구성이
적합하다.

``` text
background layer
      +
1~2 moving image layers
      +
optional text layer
```

많은 반투명 layer, 복잡한 blur/filter, 수십 개 객체의 동시 animation은
피한다.

EO1-Museum에서 중요한 것은 순간적인 benchmark보다 **장시간 안정적인
전시**이다.

------------------------------------------------------------------------

## 14. 권장 HTML animation 구조

현재까지의 결과를 바탕으로 한 권장 구조는 다음과 같다.

``` text
HTML
 |
 +-- static DOM
 |
 +-- pre-sized images
 |
 +-- CSS transform
 |      translate3d()
 |      scale()
 |
 +-- CSS opacity
 |
 +-- CSS transition / @keyframes
 |
 +-- small amount of JavaScript
         |
         +-- timing
         +-- slide selection
         +-- class switching
```

피해야 할 구조:

``` text
HTML
 |
 +-- full-screen Canvas continuous redraw
 |
 +-- WebGL
 |
 +-- many dynamically changing DOM elements
 |
 +-- expensive filters/effects
```

------------------------------------------------------------------------

## 15. 정지 Gallery와 HTML animation의 공존

EO1-Museum의 기본 목적은 여전히 작품을 감상하는 디지털 액자이다. 모든
작품을 움직이게 만들 필요는 없다.

``` text
Still artwork
    -> JPEG / PNG
    -> Local Gallery
    -> adjustable display interval
    -> cross-fade

Animated artwork
    -> HTML + CSS
    -> WebView
    -> transform / opacity based animation
```

HTML은 단순한 웹페이지가 아니라 EO1에서 **가벼운 움직이는 디지털
작품**을 표현하는 포맷으로 사용할 수 있다.

더 복잡한 실시간 graphics가 필요하다면 Native Android/OpenGL ES 2.0을
별도로 검토할 수 있다. 현재 WebView에서 WebGL은 선택지가 아니다.

------------------------------------------------------------------------

## 16. v0.41에서 얻은 핵심 교훈

오늘 확인한 내용을 요약하면 다음과 같다.

``` text
Vivante GC2000
    -> 존재

OpenGL ES 2.0
    -> 지원

Android hardware acceleration
    -> 작동

Canvas 2D continuous redraw
    -> 약 4 fps, 느림

WebGL in current WebView
    -> 사용 불가

CSS transform / translate3d
    -> 빠름
```

즉 성능을 결정하는 것은 단순히 하드웨어 사양이 아니라 **어떤 rendering
path를 선택하느냐**이다.

------------------------------------------------------------------------

## 17. v0.4에서 v0.41로

``` text
v0.1
Native image gallery
    |
    v
v0.2
Native image + MP4 playback
    |
    v
v0.3
Local + PC Gallery
Mouse control
Cross-fade
Clock
Automatic startup
Bluetooth multimedia
    |
    v
v0.4
PC Gallery -> Local Gallery
Optional Safe Sync
server.py --sync
Trusted server check
Storage protection
On-screen sync status
    |
    v
v0.41
Adjustable image display interval
15 sec / 30 sec / 1 min / 2 min
EO1 graphics capability exploration
Vivante GC2000 / OpenGL ES 2.0
Canvas 2D performance test
WebGL availability test
CSS transform / translate3d test
HTML animation design guidelines
```

------------------------------------------------------------------------

## 18. 다음 HTML animation 실험

첫 실험은 복잡할 필요가 없다.

1.  정지 이미지 한 장에 느린 `translate3d()` + `scale()` 적용
2.  이미지 두 장을 겹쳐 `opacity`만으로 cross-fade
3.  두 효과를 결합

``` text
Image A
   +-- slow transform
   +-- opacity 1 -> 0

Image B
   +-- slow transform
   +-- opacity 0 -> 1
```

장시간 시험에서는 frame rate만 보지 않고 다음을 함께 확인한다.

``` text
부드러움
장시간 실행 안정성
메모리 증가 여부
이미지 교체 후 resource 해제
WebView 재시작 없이 계속 실행 가능한지
발열
```

이 정도가 안정적으로 동작하면 EO1용 HTML artwork의 기본 template으로
발전시킬 수 있다.

------------------------------------------------------------------------


## WebView cache와 PC server 의존성 확인

PC server를 종료한 뒤에도 Network Gallery에서 이전에 열었던 `art` 애니메이션이 보이는 현상이 관찰되었다.

처음에는 이것이 PC server 없이도 해당 HTML artwork가 EO1 내부에서 독립적으로 다시 로드되는 현상인지 확인할 필요가 있었다. 이를 구분하기 위해 PC server를 계속 끈 상태에서 EO1 Museum 앱을 강제 종료한 뒤 다시 실행하였다.

```cmd
adb -s 115343222 shell am force-stop com.dan.eo1
adb -s 115343222 shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

그 결과 앱을 다시 시작한 뒤 Network Gallery를 열었을 때 `art` 애니메이션은 더 이상 나타나지 않았다.

따라서 앞서 관찰한 현상은 **PC server 없이 HTML artwork가 영구적으로 저장되어 실행된 것이 아니라, WebView에 이미 로드되어 있던 페이지와 관련 resource가 cache 또는 기존 WebView 상태에 남아 있었기 때문**으로 해석할 수 있다.

관찰 흐름은 다음과 같다.

```text
PC server ON
    ↓
Network Gallery에서 HTML/CSS/image resource 로드
    ↓
WebView에 resource/state가 남음
    ↓
PC server OFF
    ↓
기존 animation이 한동안 계속 표시됨

그러나:

PC server OFF
    ↓
EO1 Museum force-stop
    ↓
앱 재실행
    ↓
Network Gallery 진입
    ↓
animation 나타나지 않음
```

이 실험은 두 가지를 구분해 준다.

1. **resource 공급**은 PC server에 의존한다.
2. 일단 resource가 로드된 뒤의 **animation 실행 자체는 EO1의 WebView/graphics stack에서 이루어진다.**

즉 서버가 animation frame을 생성하거나 실시간으로 전송하는 구조가 아니다. HTML, CSS, image 등의 resource를 받은 뒤 `transform`, `translate3d()`, `opacity` 등의 animation은 EO1 자체에서 수행한다.

이 결과는 향후 HTML artwork를 EO1 내부 저장공간이나 앱 asset에 명시적으로 저장하여 `file://` 또는 local resource로 로드하는 방식을 시험할 근거가 된다. 다만 **이번 cache 관찰만으로 offline HTML artwork 기능이 이미 구현되었다고 보아서는 안 된다.** 그것은 별도의 실험 대상이다.

---

## Animation 속도에 대한 구분

PC server의 속도를 높인다고 이미 로드된 HTML animation의 frame rate가 빨라지는 것은 아니다. 서버는 resource 전달 단계에 관여하고, 실제 animation rendering은 EO1에서 수행한다.

또한 다음 두 가지 '속도'를 구분해야 한다.

```text
animation duration
    -> 물체가 화면에서 얼마나 빨리 움직이는가

rendering frame rate
    -> 그 움직임을 초당 몇 frame으로 표시할 수 있는가
```

예를 들어:

```css
animation: drift 30s linear infinite;
```

를

```css
animation: drift 10s linear infinite;
```

로 바꾸면 움직임 자체는 3배 빨라진다. 그러나 이것이 EO1이 처리할 수 있는 최대 frame rate를 높여 주는 것은 아니다.

EO1에서는 복잡한 Canvas redraw보다 이미 만들어진 layer를 `transform`과 `opacity`로 움직이는 방식을 우선하는 것이 바람직하다.

---

## HTML5/JavaScript generative artwork를 MP4로 렌더링하기

EO1에서 HTML5/JavaScript 기반 generative artwork를 직접 실행하는 실험은
graphics stack의 특성을 이해하는 데 유용했다. 그러나 복잡한 Canvas animation은
EO1의 KitKat WebView에서 충분한 frame rate를 얻기 어렵다.

이 문제를 해결하기 위해 EO1-Museum에서는 HTML/JavaScript를 반드시 EO1에서 직접
실행하는 배포 포맷으로 보지 않고, **PC에서 작품을 제작하고 렌더링하기 위한
authoring format**으로 사용할 수 있도록 하였다.

현재의 기본 경로는 다음과 같다.

```text
HTML / JavaScript master artwork
        ↓
render_art.py
        ↓
Headless Chromium
1080 × 1920 / 30 fps
        ↓
Chrome DevTools Protocol
real-time screen recording
        ↓
temporary WebM
        ↓
FFmpeg
H.264 / yuv420p
        ↓
5-minute MP4
        ↓
EO1 Native Local Gallery
```

이 방식에서는 EO1이 generative artwork를 실시간으로 계산하지 않는다. PC에서
완성된 움직임을 video로 만들고, EO1은 native video playback 기능으로 이를
재생한다.

이것은 EO1-Museum의 기존 원칙과도 잘 맞는다.

```text
PC
    -> 계산
    -> artwork 생성
    -> animation rendering
    -> video encoding
    -> curation

EO1
    -> 저장
    -> decode
    -> display
```

복잡한 작업은 PC가 담당하고 EO1은 이미 준비된 media를 안정적으로 표시하는 데
집중한다.

### OBS를 사용하지 않는 이유

초기에는 OBS Browser Source를 이용하여 1080 × 1920 portrait video를 만드는
방법을 검토하였다. 일반적인 Window Capture보다 Browser Source가 정확한 viewport를
만들기에는 유리했지만, 별도의 OBS 설정과 capture workflow가 필요하였다.

이후 headless Chromium 자체에서 화면을 직접 기록할 수 있음을 확인하였다.
따라서 현재 workflow에서는 physical monitor, desktop browser window, OBS,
capture rectangle, manual crop이 모두 필요하지 않다.

```text
이전 검토 방식

HTML
  ↓
OBS Browser Source
  ↓
OBS Canvas
  ↓
recording


현재 방식

HTML
  ↓
Headless Chromium
  ↓
CDP direct recording
  ↓
FFmpeg
  ↓
MP4
```

### render_art.py

이 workflow를 자동화하기 위해 `render_art.py`를 사용한다.

현재 버전은:

```text
render_art.py 1.1.0
```

기본 사용법:

```powershell
python render_art.py artwork.html -o artwork.mp4 -d 300
```

`-d 300`은 300초, 즉 **5분짜리 작품**을 만든다는 뜻이다.

렌더러는 headless Chromium의 viewport를 EO1의 native resolution과 같은
1080 × 1920으로 만들고 artwork를 실제 시간으로 실행한다. 녹화 결과는 임시
WebM으로 받은 뒤 FFmpeg로 MP4로 변환한다.

현재 기본 video 조건은 다음과 같다.

```text
Resolution     1080 × 1920
Frame rate     30 fps
Video codec    H.264
Pixel format   yuv420p
Audio          none
Container      MP4
```

FFmpeg 변환은 다음 계열의 설정을 사용한다.

```text
libx264
preset veryfast
CRF 18
yuv420p
faststart
```

임시 WebM은 MP4 변환이 끝나면 삭제한다.

### real-time recording

초기 renderer 실험에서는 각 frame을 screenshot으로 얻거나 virtual time으로
animation 시간을 제어하는 방법을 시험하였다. 정확한 animation 속도는 얻을 수
있었지만 처리 시간이 길었다.

현재 방식에서는 Chromium에서 artwork를 **실제 시간으로 실행하면서 직접
recording**한다. 따라서 JavaScript의 `requestAnimationFrame()`이나 timer를
인위적으로 다시 구현할 필요가 없다.

실험에서 60초 artwork의 전체 처리 시간은 약 76초였으며, 대략 1.27배의 wall
time으로 최종 MP4를 만들 수 있었다. 이 정도라면 5분짜리 artwork를 일상적으로
제작하는 데 충분히 실용적이다.

### preview mode

일부 artwork는 PC에서 parameter를 조절하기 위한 control panel을 가지고 있다.
예를 들어 Collision Trails에는 공의 수, 속도, 크기, trail persistence 등의
control이 있다.

작품 제작용 HTML에서는 이러한 control을 그대로 유지하는 것이 편리하지만,
EO1용 video에는 control panel이 나타나면 안 된다.

이를 위해 artwork가 `?preview=1`을 지원하는 경우 다음과 같이 실행한다.

```powershell
python render_art.py collision.html -o collision.mp4 -d 300 --preview
```

`--preview`는 HTML을 다음과 같은 형태로 연다.

```text
file:///.../collision.html?preview=1
```

따라서 master HTML을 별도로 복제하거나 control panel을 삭제할 필요가 없다.

### --set을 이용한 artwork parameter 지정

`render_art.py` v1.1.0에서는 렌더링 시작 전에 HTML form control의 값을 지정할
수 있다.

예:

```powershell
python render_art.py collision.html -o collision.mp4 -d 300 --preview \
    --set balls=12 speed=80 size=16 trail=97
```

`--set`은 HTML element의 `id`를 사용한다.

```text
--set id=value
```

렌더러는 Chromium에서 해당 element를 찾아 값을 바꾼 뒤 `input`과 `change`
event를 발생시킨다. 따라서 slider, number input, checkbox 등으로 만든 기존
interactive control을 artwork의 parameter interface로 그대로 활용할 수 있다.

checkbox도 다음과 같이 지정할 수 있다.

```text
--set collisions=true sphere=false
```

이 구조의 장점은 renderer가 특정 artwork에 종속되지 않는다는 것이다.

```text
interactive HTML master
        ↓
control parameter 선택
        ↓
render_art.py --set ...
        ↓
특정 parameter를 가진 MP4
```

같은 HTML master에서 parameter만 바꾸어 여러 variation을 만들 수 있다.

### Collision Trails 예

Collision Trails의 기본 공 크기를 약 30% 크게 하여 5분짜리 작품을 만들려면:

```powershell
python render_art.py "EO1_Collision_Trails_Glass_Spheres.html" \
    -o "EO1_Collision_Trails_Glass_Spheres.mp4" \
    -d 300 --preview --set size=16
```

이처럼 interactive control은 작품을 설계하고 시험하는 interface이고,
`render_art.py`는 선택된 상태를 최종 video로 고정하는 rendering 도구가 된다.

### 여러 artwork의 batch rendering

각 artwork를 5분짜리 MP4로 만들 때에는 명령을 순서대로 실행하거나 PowerShell
script로 묶을 수 있다.

```powershell
python render_art.py "EO1_Collision_Trails_Glass_Spheres.html" -o "EO1_Collision_Trails_Glass_Spheres.mp4" -d 300 --preview --set size=16
python render_art.py "EO1_Cosmic_Flow_Field.html" -o "EO1_Cosmic_Flow_Field.mp4" -d 300
python render_art.py "EO1_Infinite_Spiral_Zoom.html" -o "EO1_Infinite_Spiral_Zoom.mp4" -d 300
python render_art.py "EO1_Newtons_Cradle.html" -o "EO1_Newtons_Cradle.mp4" -d 300
python render_art.py "EO1_Neon_Wireframe_Dreamscape_Animated.html" -o "EO1_Neon_Wireframe_Dreamscape_Animated.mp4" -d 300
python render_art.py "EO1_Space_Jellyfish.html" -o "EO1_Space_Jellyfish.mp4" -d 300
```

따라서 generative artwork의 추가는 특별한 recording setup을 다시 만드는 작업이
아니다. HTML master를 준비한 뒤 같은 renderer를 반복해서 사용하면 된다.

### EO1용 video file size

5분짜리 generative artwork가 약 59 MB인 사례를 기준으로 하면 평균 data rate는
약 1.6 Mbps 수준이다. 현재의 H.264/yuv420p 조건에서는 화질을 더 낮추어 file
size를 억지로 줄이기보다 실제 EO1 playback과 저장공간을 기준으로 판단하는 편이
낫다.

EO1-Museum에서는 여러 artwork를 장기간 보관할 때 내부 저장공간의 여유를
확인해야 하지만, 개별 5분 video가 수십 MB인 것은 현재 workflow에서 특별히
비정상적인 크기로 보지 않는다.

### EO1에서의 전달과 재생

완성된 MP4는 기존 EO1-Museum media workflow를 그대로 사용한다.

```text
render_art.py
        ↓
EO1-ready MP4
        ↓
Safe Sync 또는 ADB transfer
        ↓
/sdcard/EO1-Museum/images/
        ↓
Native Local Gallery
        ↓
video playback
```

따라서 generative artwork를 위해 EO1 쪽에 별도의 HTML runtime이나 새로운
player를 추가할 필요가 없다.

### 정지 작품, 가벼운 HTML animation, generative video의 공존

현재 EO1-Museum의 display path는 세 종류로 정리할 수 있다.

```text
Still artwork
    → JPEG / PNG
    → Native Local Gallery
    → adjustable display interval
    → cross-fade


Lightweight HTML animation
    → HTML / CSS
    → EO1 WebView
    → transform / opacity 중심
    → 실험 및 제한적 사용


Complex generative artwork
    → HTML / JavaScript master
    → PC render_art.py
    → H.264 / yuv420p MP4
    → Native Local Gallery
```

따라서 HTML은 두 가지 역할을 할 수 있다.

1. EO1에서 직접 실행하는 가벼운 animation format
2. PC에서 복잡한 generative artwork를 만드는 authoring/rendering format

두 번째 역할에서는 EO1의 오래된 WebView 성능이 작품의 복잡도를 제한하지 않는다.

### 현재 권장 workflow

현재 generative artwork에 대한 권장 workflow는 다음과 같다.

```text
HTML / JavaScript artwork
        ↓
PC에서 interactive하게 개발
        ↓
필요하면 control panel로 parameter 조정
        ↓
render_art.py 1.1.0
        ↓
--preview
--set id=value
        ↓
Headless Chromium
1080 × 1920 / 30 fps
        ↓
CDP real-time recording
        ↓
temporary WebM
        ↓
FFmpeg
H.264 / yuv420p
        ↓
5-minute MP4
        ↓
Safe Sync / ADB
        ↓
EO1 Native Local Gallery
```

핵심은 HTML5/JavaScript를 EO1에서 반드시 직접 실행해야 하는 배포 포맷으로
보지 않는 것이다. PC에서는 현대 browser의 기능을 이용하여 자유롭게 artwork를
만들고, EO1에는 이미 완성된 video를 전달한다.

이로써 EO1의 오래된 graphics stack은 더 이상 복잡한 generative artwork의
직접적인 표현 한계가 아니다.

------------------------------------------------------------------------

## 19. README와 upstream attribution

현재 source tree의 root README가 여전히 **spalt의 원본 README**라면,
프로젝트가 지금 수준까지 달라진 뒤에도 그것을 프로젝트의 대표 README로
계속 유지할 필요는 없다.

원본 코드를 기반으로 시작했다는 사실과 원저작자 attribution은 보존해야 한다.
그러나 repository의 첫 화면인 `README.md`는 이제 **현재 EO1-Museum이 무엇인지**
설명하는 편이 맞다.

권장 구조:

```text
README.md
    -> 현재 EO1-Museum 설명
    -> 주요 기능
    -> 설치/사용법
    -> project history
    -> upstream attribution

docs/
    -> 개발 기록
    -> ...
    -> 08_PC_GALLERY_SAFE_SYNC_V0.4_2026-10-29.md
    -> 09_DISPLAY_GRAPHICS_V0.41_2026-10-31.md

docs/upstream/ 또는 legacy/
    -> 필요하면 원본 README 별도 보존
```

새 README에는 예를 들어 다음과 같이 upstream을 명시할 수 있다.

```text
EO1-Museum was developed from earlier EO1 community work by spalt.
The original source and attribution are preserved in this repository.
EO1-Museum substantially extends that work with a native local gallery,
PC gallery integration, media playback, mouse controls, Safe Sync,
and additional display features for the discontinued Electric Objects EO1.
```

원본 source의 license와 copyright notice가 있다면 README 교체 여부와 관계없이
그대로 유지해야 한다.

즉 **README를 EO1-Museum의 것으로 바꾸는 것과 spalt의 attribution을 지우는 것은
전혀 다른 일**이다.

------------------------------------------------------------------------

## 20. 맺음말

v0.41에서는 처음에는 이미지 표시 시간과 EO1 자체의 graphics capability를
탐색하였다. 이 과정에서 Canvas 2D의 지속적인 full-screen redraw가 느리고,
현재 WebView에서는 WebGL을 사용할 수 없지만 CSS `transform`, `translate3d()`,
`opacity`를 이용한 animation은 비교적 현실적이라는 점을 확인하였다.

그러나 이 탐색의 더 중요한 결과는 EO1에서 모든 animation을 직접 계산할 필요가
없다는 결론이었다.

정지 작품은 PC에서 1080 × 1920 image로 준비한다. 복잡한 generative artwork도
같은 원칙으로 PC에서 1080 × 1920 video로 준비할 수 있다.

```text
Still artwork
    source image
        ↓
    PC preprocessing
        ↓
    prepared JPEG/PNG
        ↓
    EO1


Generative artwork
    HTML/JavaScript master
        ↓
    PC render_art.py
        ↓
    prepared MP4
        ↓
    EO1
```

`render_art.py` v1.1.0은 headless Chromium과 CDP direct recording을 이용하여
HTML/JavaScript artwork를 실제 시간으로 실행하고, FFmpeg를 통해
H.264/yuv420p MP4로 변환한다. `--preview`와 범용 `--set id=value` 기능을
이용하면 interactive master artwork를 수정하거나 복제하지 않고도 전시용
variation을 만들 수 있다.

따라서 v0.41에서 얻은 최종적인 교훈은 처음의 graphics benchmark보다 넓다.

> **EO1이 잘하는 일은 EO1에게 맡기고, 복잡한 rendering은 PC에서 끝낸다.**

이 구조를 통해 EO1-Museum은 오래된 Android 4.4.2 hardware의 한계를 억지로
극복하려 하기보다, 그 기기가 이미 잘 수행하는 image/video playback을 활용하면서
현대적인 generative artwork까지 전시할 수 있게 되었다.
