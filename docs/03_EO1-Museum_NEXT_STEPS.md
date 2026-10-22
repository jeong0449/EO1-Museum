# EO1-Museum 개발 인수인계 및 다음 작업 지시문

> 작성 시점: 2026-10-22\
> 목적: 현재까지의 EO1-Museum 개발 상태를 보존하고, 새 대화나 새 작업
> 세션에서 곧바로 개발을 이어갈 수 있도록 기술적 배경, 확인된 사실,
> 의사결정, 다음 작업 순서를 정리한다.

## 1. 프로젝트 목표

**EO1-Museum**은 서비스가 종료된 Electric Objects EO1 디지털 아트
디스플레이를 다시 활용하여, 공개 미술관 작품을 표시하는 독립형 디지털
미술관 디스플레이로 만드는 프로젝트이다.

현재 안정적으로 동작하는 방식은 PC가 작품 이미지를 준비하고 HTTP 서버로
제공하며 EO1의 Firefox가 이를 표시하는 구조이다. 앞으로의 핵심 목표는 이
구조를 보존하면서, 별도의 **native Android replacement app**을 개발하여
EO1이 PC와 Wi-Fi 없이도 내부 저장공간의 작품을 독립적으로 표시하게
만드는 것이다.

개발 원칙: - 현재 정상 작동하는 환경을 파괴하지 않는다. - eMMC의 Android
시스템이나 kernel을 불필요하게 수정하지 않는다. - 가능한 한 되돌릴 수
있는 실험부터 한다. - Linux USB boot, kernel rebuild, UART 연결 등은
현재 목표에 우선하지 않는다. - **Planning → Experiment → Result →
Decision** 순서로 기록을 먼저 남기고 개발한다.

## 2. EO1 하드웨어 및 시스템

확인된 정보:

``` text
Device       : Electric Objects EO1
Display      : 23-inch portrait display
Panel        : Samsung LTM230HL07
Resolution   : 1080 × 1920
SoC          : Freescale i.MX6 family
CPU ABI      : armeabi-v7a
Processor    : ARMv7 Processor rev 10 (v7l)
Hardware     : Boundary Devices EO Board
Android      : 4.4.2
RAM          : MemTotal 837012 kB (~818 MiB)
Internal /data:
              2.4 GB total / ~1.4 GB free
MTP-visible user storage:
              ~2.38 GB total / ~960 MB free
```

`Hardware : Boundary Devices EO Board`는 EO1에 맞춘 Boundary Devices
계열 board/kernel의 중요한 단서이다.

## 3. 현재 안정적으로 동작하는 v1

``` text
PC
 ├─ Met Open Access 작품 다운로드
 ├─ 1080×1920용 이미지 가공
 └─ local HTTP server :8000
             │ Wi-Fi
             ▼
EO1 Android
 └─ MetBoot
      └─ Firefox 실행
           └─ Firefox startup page
                └─ PC EO1-Museum HTTP server
```

주요 PC 측 구성: - `GET_MET_ART_KEYWORD.py`: Met Open Access CSV/API,
public-domain painting, 원본 cache/metadata - `make_gallery.py`:
`original/` → `display/`, 1080×1920 black canvas, aspect ratio 유지,
`images.js` 생성 - `index.html`: 약 15초 간격 slideshow - `server.py`:
`ThreadingTCPServer`, port 8000, no-cache headers, APK MIME -
`START_EO1.bat`, `UPDATE_MET.bat`, `GET_MET_AND_START.bat`

**v1은 이미 잘 작동하므로 native app 개발 중에도 반드시 보존한다.**

## 4. MetBoot의 정확한 역할

MetBoot는 EO1-Museum 서버나 작품을 관리하지 않는다.

``` text
Android boot
   ↓
BOOT_COMPLETED
   ↓
MetBoot
   ↓
Firefox 실행
   ↓
Firefox에 설정된 startup page 표시
```

즉 **Firefox 기반 PC-server 방식의 boot helper**이다. 향후 native app이
`BOOT_COMPLETED`를 직접 처리하면 standalone mode에서는 필요 없지만 기존
Firefox mode를 위해 보존한다.

## 5. ADBApprovalHelper

EO1은 touchscreen이 아니다. PC와 처음 ADB 연결하면 Android가 RSA 승인을
요구하지만, micro-USB 포트가 이미 PC 연결에 사용되어 OTG mouse로 OK를
누를 수 없다.

이를 해결하기 위해 **ADBApprovalHelper.apk**를 만들었다.

-   AccessibilityService 사용
-   `com.android.systemui` USB debugging dialog 감지
-   `Always allow from this computer` 선택
-   `OK` 자동 실행

ADBApprovalHelper는 **개발·정비용 utility**로 보존한다.

## 6. ADB에서 확인된 사실

ADB shell은 처음부터 root이다.

``` text
uid=0(root) gid=0(root) context=u:r:shell:s0
```

Wireless ADB:

``` powershell
adb -s 115343222 tcpip 5555
adb connect 192.168.1.105:5555
adb -s 192.168.1.105:5555 shell
```

단, **TCP ADB mode는 reboot 후 유지되지 않는다.**

원칙: - 일반 APK 개발/설치/디버깅 → USB ADB - micro-USB를 OTG host로
쓰면서 shell도 필요할 때 → wireless ADB - 완성된 EO1 Gallery 운용 → ADB
불필요

## 7. USB flash storage 실험 결과

USB flash는 실제로 정상 enumeration된다.

``` text
bInterfaceClass     = 08
bInterfaceSubClass  = 06
bInterfaceProtocol  = 50
```

즉 표준 USB Mass Storage / SCSI transparent / Bulk-Only Transport
device이다. 그러나 `/dev/sda`가 생기지 않았다.

결정적 kernel config:

``` text
# CONFIG_SCSI is not set
CONFIG_USB=y
CONFIG_FAT_FS=y
CONFIG_VFAT_FS=y
```

따라서 FAT32나 vold 문제가 아니라 **stock Android kernel에 USB
mass-storage block-device 지원에 필요한 SCSI 계층이 빠져 있다.**

현재 목적에는 kernel-level 작업이 과도하므로 **USB mass-storage 지원은
보류한다.**

이 결과는 bootloader 단계의 Linux USB boot 문제와는 별개이다.

## 8. Linux USB boot 실험

2026-10-20: - Yocto Hardknott Nitrogen6X image - Ubuntu Bionic XFCE
ARMHF Nitrogen6X image - direct OTG / powered hub / keyboard 시도

모두 기존 Android로 boot하였다. 과거 EO1 Linux USB boot 성공 사례는
있으므로 불가능하다고 단정하지 않는다. 다만 현재는 UART/bootloader
reverse engineering을 진행하지 않고 **deferred experiment**로 둔다.

## 9. 내부 저장공간과 설계 전환

EO1에는 native app이 활용할 수 있는 user storage가 이미 있다. 따라서 USB
flash가 필수적이지 않다.

목표 구조:

``` text
PC
 │ USB ADB / adb push
 ▼
EO1 internal user storage
 │
 └── EO1-Museum/
      ├── images/
      ├── metadata.json
      └── exhibition.json
             │
             ▼
        EO1 Gallery
             │
             ▼
      1080×1920 fullscreen
```

`/data` free와 Windows MTP free는 동일 범위를 같은 방식으로 측정한 값이
아닐 수 있으므로 `/data`의 전체 여유공간을 작품용으로 사용할 수 있다고
가정하지 않는다.

## 10. Android Downloads UI 주의

Android의 `Downloads` 앱은 `/sdcard/Download`의 직접적인 file browser가
아니다. Download Manager의 historical entry가 남을 수 있다.

따라서 실제 file 존재 여부는 ADB/filesystem으로 확인한다.

## 11. Native replacement app 이름

전체 프로젝트: **EO1-Museum**

기존 helper: - **MetBoot** --- boot 후 Firefox 실행 -
**ADBApprovalHelper** --- ADB RSA 승인 보조

새 standalone artwork display app:

# **EO1 Gallery**

권장:

``` text
App name : EO1 Gallery
APK      : EO1Gallery.apk
Package  : com.eo1museum.gallery
```

## 12. EO1 Gallery v0.1 목표

첫 버전 목표는 하나다.

> 내부 저장공간의 JPEG/PNG를 native Android app이 fullscreen slideshow로
> 표시한다.

필수 기능: 1. Android 4.4.2에서 실행 2. `/sdcard/EO1-Museum/images/`
읽기 3. JPG/JPEG/PNG 목록 생성 4. `ImageView`에 표시 5. 1080×1920에
aspect ratio 유지하여 fit 6. 남는 영역은 검정 7. 약 15초마다 다음 이미지
8. fullscreen/immersive 9. screen-on 유지 10. 마지막 이미지 다음에는
처음으로 순환

v0.1에서 하지 않을 것: - BOOT_COMPLETED - Home/Launcher replacement -
metadata overlay - Flickr - network download - remote control - USB
storage - database - 복잡한 settings UI - kernel modification

**v0.1은 manual launch 가능한 최소 slideshow APK**로 만든다.

## 13. Android 호환성

``` text
Android 4.4.2
API level 19
32-bit ARM
armeabi-v7a
```

권장: - Java - `minSdkVersion 19` - AndroidX 의존성 최소화 또는 미사용 -
단순 Activity + ImageView + Handler/Runnable - 오래된 Android에서도
확실히 동작하는 API 사용

## 14. spalt/EO1을 reference implementation으로 사용

참고 저장소:

`https://github.com/spalt/EO1`

특히 참고: - Home/Launcher behavior - fullscreen display - ImageView -
screen/brightness control - ambient-light sensor - quiet hours - EO1
hardware button handling - screen-on 방식 - local/public Downloads 접근

당장 불필요: - Flickr integration - Retrofit Flickr services - 외부
network image source - 불필요한 remote service

원칙은 **spalt/EO1의 EO1-specific 구현을 reference로 삼아 새 EO1
Gallery를 단순하게 만드는 것**이다. 실제 코드 재사용 여부는 검토 후
결정한다.

## 15. Roadmap

### v0.1 --- Local slideshow

`/sdcard/EO1-Museum/images` → EO1 Gallery → fullscreen slideshow

성공 조건: - 10장 이상 이미지 - 정상 표시 - 15초 전환 - 순환 - 장시간
crash 없음

### v0.2 --- Standalone boot

-   `BOOT_COMPLETED`
-   boot 후 EO1 Gallery 자동 실행
-   기존 Firefox mode용 MetBoot는 repository에 보존

### v0.3 --- Exhibition behavior

-   random/shuffle
-   `exhibition.json`
-   slideshow interval
-   작품별 metadata

### v0.4 --- EO1-specific integration

spalt/EO1 참고: - brightness - ambient light - quiet hours - physical
buttons - Home/Launcher 검토

### v0.5 이후

필요할 때만: - landscape slow panning - transitions - phone/PC remote
control - exhibition switching - Wi-Fi content update - metadata overlay

## 16. 다음 개발 세션에서 바로 할 일

### Step 1 --- spalt/EO1 코드 재검토

Manifest, MainActivity, fullscreen flags, ImageView, screen-on, storage
access, EO1-specific code를 확인한다.

목적은 복제가 아니라 **EO1 Gallery v0.1에 필요한 최소 EO1-specific
지식을 추출하는 것**이다.

### Step 2 --- EO1 Gallery Android Studio project 생성

``` text
App name     EO1 Gallery
Package      com.eo1museum.gallery
minSdk       19
Language     Java
```

### Step 3 --- test exhibition 준비

``` powershell
adb shell mkdir -p /sdcard/EO1-Museum/images
adb push test-exhibition/. /sdcard/EO1-Museum/images/
```

### Step 4 --- v0.1 APK 설치

``` powershell
adb install -r EO1Gallery.apk
```

### Step 5 --- manual launch 및 관찰

확인: - portrait orientation - fullscreen - scaling - black border -
15-second transition - screen timeout - memory consumption -
30분\~수시간 안정성

### Step 6 --- 결과 기록

항상 다음 형식으로 남긴다.

``` text
Planning
Experiment
Result
Decision
```

**v0.1이 안정화되기 전에는 boot receiver나 Launcher replacement를
건드리지 않는다.**

## 17. 현재 단계에서 다시 빠지지 말아야 할 우회로

-   USB flash: `# CONFIG_SCSI is not set`까지 원인 확인 완료.
    FAT32/vold/mount 반복시험 불필요.
-   Linux USB boot: EO1 Gallery의 dependency가 아님.
-   Kernel rebuild: 현재 목표에 필요 없음.
-   UART/board opening: 현재 필요 없음.
-   Persistent wireless ADB: 일반 개발은 USB ADB가 더 단순함.

## 18. 최종 운용 구조

### Mode A --- 기존 network/server mode

``` text
PC EO1-Museum server
       │ Wi-Fi
       ▼
Android → MetBoot → Firefox → web slideshow
```

### Mode B --- standalone gallery mode

``` text
Android → EO1 Gallery → internal storage → local slideshow
```

두 mode는 경쟁 관계가 아니라 **EO1-Museum의 서로 다른 운용 방식**으로
함께 보존한다.

## 19. 현재 핵심 판단

> EO1을 다시 유용한 디지털 미술관으로 만들기 위해 Linux를 설치하거나
> Android kernel을 교체할 필요는 없다.

현재 가장 유망한 개발 대상은 **EO1 Gallery**이다.

첫 성공 기준:

> `/sdcard/EO1-Museum/images/`에 넣은 작품을 EO1 Gallery가 1080×1920
> 전체 화면으로 안정적으로 순환 표시한다.

여기까지 성공하면 EO1-Museum은 PC 의존형 prototype에서 **standalone
digital art display**로 넘어가는 중요한 전환점을 맞게 된다.
