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

## HTML5/JavaScript artwork를 1080 × 1920 video로 기록하기

EO1에서 HTML5/JavaScript 기반의 generative artwork를 직접 실행하는 실험은
graphics stack의 특성을 이해하는 데 유용했지만, 복잡한 animation에서는 실제
전시용으로 충분한 frame rate를 얻기 어려웠다. 특히 Canvas 2D의 지속적인
full-screen redraw는 약 4 fps 수준이었고, CSS transform을 이용한 animation도
복잡도가 높아지면 움직임이 매끄럽지 않을 수 있다.

따라서 보다 복잡한 generative artwork에 대해서는 다음과 같은 별도의 전달
경로를 고려한다.

```text
HTML5 / JavaScript artwork
        ↓
PC에서 정상 속도로 실행
        ↓
1080 × 1920 video로 기록
        ↓
MP4
        ↓
EO1 Local Gallery
```

이 방식의 목적은 EO1에서 artwork를 실시간으로 계산하게 하는 것이 아니라,
PC에서 생성된 최종 움직임을 EO1의 native video playback 기능으로 재생하는
것이다.

아래 방법은 HTML5/JavaScript artwork를 정확한 **1080 × 1920 portrait
frame**으로 기록하기 위한 실용적인 workflow이다. EO1-Museum은 이미 native
MP4 playback을 지원하므로, 남은 실제 작업은 artwork를 MP4로 기록하여 EO1에서
재생하는 것이다.

### 왜 일반적인 screen capture를 사용하지 않는가

가장 단순한 방법은 Chrome이나 Firefox에서 artwork를 실행한 뒤 화면의 일부를
녹화하는 것이다. 그러나 이 방식에는 문제가 있다.

```text
browser window
 ├── title bar
 ├── tab bar
 ├── address bar
 ├── page viewport
 └── window border
```

EO1의 실제 화면은 정확히 **1080 × 1920 portrait**이다. 일반 browser window를
screen capture하면 browser chrome과 Windows window border를 제외한 실제
content area를 정확히 1080 × 1920으로 맞추기가 번거롭다.

마우스로 capture rectangle을 지정하는 방식 역시 1~2 pixel의 오차가 생기기
쉽고, window를 다시 열거나 이동하면 capture 영역을 다시 맞춰야 한다.

따라서 EO1용 artwork에서는 **화면의 일부를 잘라 녹화하는 방식보다 OBS
Browser Source 자체를 1080 × 1920으로 생성하는 방식**이 더 적합하다.

### 권장 방법: OBS Browser Source

OBS Studio에서 artwork의 HTML page를 Browser Source로 직접 읽는다.

이 방식에서는 실제 desktop browser window가 필요하지 않다. OBS 내부 browser가
지정된 URL을 직접 열고, 그 browser viewport의 크기를 숫자로 지정할 수 있다.

따라서 다음 네 단계의 크기를 모두 동일하게 맞출 수 있다.

```text
HTML artwork viewport
        1080 × 1920
             ↓
OBS Browser Source
        1080 × 1920
             ↓
OBS Canvas
        1080 × 1920
             ↓
Recorded video
        1080 × 1920
```

이것이 일반적인 Window Capture나 Display Capture보다 중요한 장점이다.
화면의 어느 부분을 녹화할지 마우스로 정확하게 선택할 필요가 없다.

### 1. HTML artwork의 frame을 고정한다

가능하면 HTML document 자체를 처음부터 EO1의 native resolution에 맞춘다.

```css
html, body {
    margin: 0;
    padding: 0;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
    background: black;
}
```

Canvas를 사용하는 artwork라면 CSS 크기뿐 아니라 실제 Canvas bitmap의 크기도
명시한다.

```html
<canvas id="art" width="1080" height="1920"></canvas>
```

중요한 점은 다음 두 값의 차이를 피하는 것이다.

```text
CSS display size
        vs.
Canvas internal bitmap size
```

둘 다 1080 × 1920으로 맞추면 불필요한 scaling을 줄이고 최종 video와 EO1
display 사이의 좌표 관계도 단순해진다.

Artwork가 DOM/CSS 기반이라면 최상위 container 역시 1080 × 1920으로 고정하는
것이 좋다.

### 2. HTML artwork를 PC에서 제공한다

로컬 HTML file을 직접 열 수도 있지만, EO1-Museum의 기존 개발 방식처럼
간단한 local HTTP server를 사용하는 편이 resource loading과 상대 경로 처리에
편리하다.

예:

```text
http://localhost:8000/art/example.html
```

또는 PC의 실제 local address를 사용할 수 있다.

```text
http://192.168.x.x:8000/art/example.html
```

OBS Browser Source에는 이 URL을 직접 입력한다.

### 3. OBS canvas를 1080 × 1920으로 설정한다

OBS에서:

```text
Settings
    ↓
Video
```

로 이동하여 다음과 같이 설정한다.

```text
Base (Canvas) Resolution       1080 × 1920
Output (Scaled) Resolution     1080 × 1920
Common FPS Values              30
```

여기서 가장 중요한 것은 **Base와 Output을 모두 1080 × 1920으로 유지하는
것**이다.

이렇게 하면 recording 과정에서 portrait artwork를 landscape canvas에 넣었다가
다시 scaling하거나 crop할 필요가 없다.

30 fps는 generative artwork를 기록하기에 적당한 기본값이다. 특정 artwork나
EO1 playback에서 문제가 있을 때만 frame rate나 encoding 조건을 조정한다.

### 4. Browser Source를 정확히 1080 × 1920으로 만든다

OBS의 Sources 영역에서:

```text
+
    ↓
Browser
```

를 선택한다.

Browser Source의 properties에서 다음 값을 지정한다.

```text
URL       http://localhost:8000/art/example.html
Width     1080
Height    1920
```

가능한 경우 source의 frame rate도 30 fps를 기준으로 한다.

여기서 `Width`와 `Height`는 desktop browser window의 크기가 아니라 **OBS
내부 browser viewport의 크기**이다.

따라서 browser title bar나 address bar는 존재하지 않는다.

### 5. Browser Source와 OBS canvas를 1:1로 맞춘다

Browser Source를 선택한 뒤:

```text
Right click
    ↓
Transform
    ↓
Fit to Screen
```

을 적용한다.

Source와 canvas가 모두 1080 × 1920이면 scaling 없이 정확히 일치해야 한다.

더 확실하게 확인하려면:

```text
Right click
    ↓
Transform
    ↓
Edit Transform
```

에서 다음 항목을 확인한다.

```text
Position
    X = 0
    Y = 0

Size
    1080 × 1920

Crop
    Left   = 0
    Right  = 0
    Top    = 0
    Bottom = 0
```

즉 최종적으로 다음 관계가 되어야 한다.

```text
source pixel (0,0)
        =
OBS canvas pixel (0,0)

source pixel (1079,1919)
        =
OBS canvas pixel (1079,1919)
```

이 상태라면 별도의 manual crop이나 browser-window alignment가 필요하지 않다.

### 6. OBS preview에서 확인할 사항

녹화 전에 다음을 확인한다.

```text
[ ] artwork가 canvas 전체를 채우는가
[ ] 좌우에 예상하지 않은 여백이 없는가
[ ] 위아래가 잘리지 않았는가
[ ] browser scrollbar가 나타나지 않는가
[ ] source가 회전되거나 scaling되지 않았는가
[ ] crop 값이 모두 0인가
```

HTML의 `margin: 0`, `padding: 0`, `overflow: hidden` 설정은 특히 중요하다.

검은 배경을 의도했다면 여백과 artwork의 실제 검은 영역을 혼동하지 않도록
원본 HTML에서도 frame 경계를 확인하는 것이 좋다.

### 7. 녹화

Frame이 정확히 맞는 것을 확인한 뒤 OBS recording을 시작한다.

이 단계에서 중요한 것은 codec을 먼저 최적화하는 것이 아니라 **정확한
1080 × 1920 master video를 얻는 것**이다.

```text
HTML/JS artwork
        ↓
OBS Browser Source
        ↓
1080 × 1920 / 30 fps recording
        ↓
master video
```

OBS의 recording container와 encoder는 PC 환경에 따라 달라질 수 있다.
최종 결과는 EO1-Museum에서 재생할 수 있는 MP4로 준비한다. 필요할 경우
recording 후 FFmpeg를 이용하여 MP4로 변환하거나 encoding 조건을 조정할 수
있다.

### 8. EO1에서 재생

EO1-Museum native application은 이미 MP4 playback을 지원한다. 따라서 기록한
video는 다음과 같은 기존 media workflow에 넣으면 된다.

```text
master recording
        ↓
필요하면 MP4로 변환
        ↓
Safe Sync 또는 ADB transfer
        ↓
/sdcard/EO1-Museum/images/
        ↓
Local Gallery playback
```

실제로 문제가 발생하는 경우에만 codec, bitrate, frame rate 등의 encoding
조건을 조정하면 된다. 별도의 복잡한 검증 절차를 먼저 만들 필요는 없다.

### 9. 왜 이 방식이 EO1-Museum에 적합한가

이 방식은 EO1-Museum의 전체 설계 원칙과도 잘 맞는다.

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

즉 복잡한 작업은 PC가 담당하고, EO1은 이미 완성된 media를 안정적으로
표시하는 데 집중한다.

정지 artwork에서는 이미 같은 원칙을 사용한다.

```text
large original image
        ↓
PC make_gallery.py
        ↓
1080 × 1920 prepared image
        ↓
EO1 Local Gallery
```

Generative artwork에서도 같은 생각을 적용하면:

```text
HTML5 / JavaScript generative artwork
        ↓
PC rendering / recording
        ↓
1080 × 1920 prepared video
        ↓
EO1 Local Gallery
```

가 된다.

따라서 HTML5/JavaScript는 반드시 EO1에서 직접 실행해야 하는 **배포 포맷**일
필요가 없다. PC에서 artwork를 생성하는 **authoring/rendering environment**로
사용하고, EO1에는 최종 결과인 video만 전달하는 것도 충분히 자연스럽다.

### 10. 현재 workflow

현재 권장 방향은 다음과 같이 정리된다.

```text
HTML5/JavaScript artwork
        ↓
PC에서 실행
        ↓
OBS Browser Source
1080 × 1920 / 30 fps
        ↓
MP4
        ↓
Safe Sync 또는 ADB
        ↓
EO1 Local Gallery
```

핵심은 HTML5/JavaScript를 EO1에서 반드시 직접 실행해야 하는 배포 포맷으로
보지 않는 것이다. PC에서는 자유롭게 generative artwork를 만들고, EO1에는
그 결과를 안정적으로 재생할 수 있는 media로 전달한다.

이 workflow에서 추가적인 검증 절차를 별도로 정의할 필요는 없다. 실제 artwork를
녹화하여 EO1에서 재생하고, 문제가 발견될 때 필요한 encoding 조건만 조정하면
된다.

------------------------------------------------------------------------


## 19. README와 upstream attribution

현재 source tree의 root README가 여전히 **spalt의 원본 README**라면,
프로젝트가 지금 수준까지 달라진 뒤에도 그것을 프로젝트의 대표 README로
계속 유지할 필요는 없다.

원본 코드를 기반으로 시작했다는 사실과 원저작자 attribution은 보존해야
한다. 그러나 repository의 첫 화면인 `README.md`는 이제 **현재
EO1-Museum이 무엇인지** 설명하는 편이 맞다.

권장 구조:

``` text
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
    -> 09_DISPLAY_GRAPHICS_V0.41_2026-10-30.md

docs/upstream/ 또는 legacy/
    -> 필요하면 원본 README 별도 보존
```

새 README에는 예를 들어 다음과 같이 upstream을 명시할 수 있다.

``` text
EO1-Museum was developed from earlier EO1 community work by spalt.
The original source and attribution are preserved in this repository.
EO1-Museum substantially extends that work with a native local gallery,
PC gallery integration, media playback, mouse controls, Safe Sync,
and additional display features for the discontinued Electric Objects EO1.
```

원본 source의 license와 copyright notice가 있다면 README 교체 여부와
관계없이 그대로 유지해야 한다.

즉 **README를 EO1-Museum의 것으로 바꾸는 것과 spalt의 attribution을
지우는 것은 전혀 다른 일**이다.

------------------------------------------------------------------------

## 20. 맺음말

v0.41의 변화는 v0.4의 Safe Sync보다 코드 규모는 작지만 EO1을 이해하는 데
의미가 있다.

이미지 표시 시간을 15초, 30초, 1분, 2분으로 조절할 수 있게 하여 개발
테스트와 실제 감상을 모두 편하게 만들었다.

또한 EO1의 graphics stack을 조사하면서 이 오래된 기기가 어떤 종류의
animation을 잘 처리하고 어떤 방식에는 약한지를 확인하였다.

핵심은 단순하다.

> **EO1에서는 pixel을 계속 다시 그리기보다, 이미 그려진 layer를 움직이는
> 것이 낫다.**

Canvas 2D의 지속적인 full-screen redraw는 느리지만 CSS `transform`,
`translate3d()`와 `opacity`를 이용한 합성은 훨씬 현실적이다. WebGL은
현재 WebView에서는 사용할 수 없지만 Vivante GC2000과 OpenGL ES 2.0
자체는 존재한다.

오래된 하드웨어의 특성에 맞는 rendering path를 선택한다면 EO1-Museum은
정지 이미지와 MP4뿐 아니라 HTML/CSS 기반의 가벼운 움직이는 디지털 작품도
새로운 전시 형식으로 활용할 수 있다.
