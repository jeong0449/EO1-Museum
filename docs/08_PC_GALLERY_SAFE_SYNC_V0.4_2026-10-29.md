# EO1 Museum v0.4 — PC Gallery와 Local Gallery의 연결

**작성일:** 2026-10-29  
**프로젝트:** EO1 Museum  
**대상 기기:** Electric Objects EO1  
**패키지:** `com.dan.eo1`  
**버전:** v0.4

---

## 1. 개요

v0.3에서 EO1 Museum은 두 가지 Gallery 모드를 하나의 Android 앱 안에 통합하였다.

```text
Local Gallery
    -> EO1 내부 저장공간의 미디어 재생

PC Gallery
    -> WebView를 이용하여 PC의 Gallery 표시
```

두 모드는 같은 앱 안에 들어 있었지만 서로 독립적이었다.

Local Gallery에서 사용할 이미지를 추가하려면 ADB 등을 이용하여 직접 다음 디렉토리에 파일을 복사해야 했다.

```text
/sdcard/EO1-Museum/images
```

반면 PC Gallery는 PC의 HTTP server가 제공하는 콘텐츠를 WebView에서 실시간으로 표시할 뿐이었다.

v0.4에서는 이 두 기능을 연결하였다.

PC Gallery에 준비된 이미지를 네트워크를 통해 EO1의 내부 저장공간으로 복사하여, 이후에는 PC 없이도 Local Gallery에서 같은 이미지를 감상할 수 있도록 하였다.

개념적으로는 다음과 같다.

```text
PC
 |
 +--> original/
 |
 +--> make_gallery.py
 |
 +--> display/
 |      0001.jpg
 |      0002.jpg
 |      0003.jpg
 |      ...
 |
 +--> images.js
 |
 +--> server.py
          |
          | Wi-Fi / HTTP
          v
       EO1 Museum
          |
          +--> PC Gallery
          |
          +--> Safe Sync
                  |
                  v
       /sdcard/EO1-Museum/images
                  |
                  v
             Local Gallery
```

이제 PC Gallery는 단순한 원격 표시 기능뿐 아니라 **PC에서 준비한 전시 컬렉션을 EO1으로 전달하는 통로**가 되었다.

---

## 2. v0.4의 개발 목표

v0.4의 핵심 목표는 명확하다.

> PC에서 Gallery를 준비하고 필요할 때 EO1의 내부 저장공간으로 안전하게 복사한다.

이를 위해 다음과 같은 원칙을 세웠다.

1. EO1은 항상 Local Gallery로 시작한다.
2. PC가 없어도 기존 Local Gallery는 정상 작동해야 한다.
3. PC Gallery를 선택했다고 해서 항상 sync하지는 않는다.
4. sync 여부는 PC server가 결정한다.
5. PC의 Gallery collection을 EO1으로 단방향 전송한다.
6. 같은 이름의 파일은 새 파일로 교체한다.
7. 다운로드 실패 때문에 기존 파일이 손상되어서는 안 된다.
8. EO1의 남은 저장공간을 보호한다.
9. 한 번에 저장할 미디어 수를 제한할 수 있어야 한다.
10. sync 진행 상태를 EO1 화면에서 확인할 수 있어야 한다.

따라서 이것은 일반적인 양방향 파일 동기화 시스템이라기보다 **PC Gallery에서 EO1 Local Gallery로 전시 콘텐츠를 배포하는 기능**에 가깝다.

---

## 3. PC가 master, EO1이 local copy

v0.4의 sync는 양방향이 아니다.

PC에서 준비된 Gallery를 기준으로 EO1에 이미지를 전달한다.

```text
PC Gallery
    |
    | one-way
    v
EO1 Local Gallery
```

EO1에서 수정한 내용을 PC로 되돌리는 기능은 없다.

이러한 구조는 EO1 Museum의 실제 사용 방식에 잘 맞는다.

작품의 검색, 선택, 다운로드 및 Gallery 제작은 저장공간과 계산 능력이 충분한 PC에서 수행하고, EO1은 최종적으로 만들어진 전시 콘텐츠를 받아 표시하는 장치로 사용한다.

---

## 4. Gallery Builder와 display 디렉토리

PC에서는 `make_gallery.py`가 `original/`에 들어 있는 이미지를 EO1 화면에 맞게 변환한다.

기본 출력 해상도는 다음과 같다.

```text
1080 × 1920
```

출력 파일은 다음과 같이 순차적으로 만들어진다.

```text
display/
    0001.jpg
    0002.jpg
    0003.jpg
    ...
```

동시에 Network Gallery에서 사용할 파일 목록인:

```text
images.js
```

도 생성한다.

예를 들면 다음과 같다.

```javascript
var images = [
  "display/0001.jpg",
  "display/0002.jpg",
  "display/0003.jpg",
];
```

따라서 `images.js`는 PC Gallery의 표시 목록인 동시에 EO1이 어떤 파일을 가져와야 하는지를 알려주는 간단한 manifest 역할도 할 수 있다.

별도의 sync manifest 형식을 새로 만들지 않고 기존 Gallery 구조를 그대로 활용하였다.

---

## 5. 기존 HTTP server에서 server.py로

초기 PC Gallery에서는 Python의 기본 HTTP server를 사용하였다.

```text
python -m http.server 8000
```

이 방법은 Gallery를 표시하기에는 충분하지만 EO1에게 다음과 같은 정보를 전달할 수 없다.

```text
이번 접속에서 sync를 수행할 것인가?
```

v0.4에서는 이를 위해 전용 `server.py`를 사용한다.

평상시에는:

```text
python server.py
```

로 실행한다.

이 경우 PC Gallery는 정상적으로 작동하지만 EO1에 sync를 요청하지 않는다.

새로운 Gallery를 EO1 내부 저장공간으로 전달하고 싶을 때에는:

```text
python server.py --sync
```

로 실행한다.

즉 **sync 여부를 EO1에서 결정하는 것이 아니라 PC가 명시적으로 지시한다.**

---

## 6. /eo1-status

`server.py`는 EO1 Museum을 위한 작은 control endpoint를 제공한다.

```text
/eo1-status
```

예를 들어 sync를 허용한 서버의 응답은 다음과 같다.

```text
EO1M-8F29C74A
SYNC=1
```

일반 모드에서는:

```text
EO1M-8F29C74A
SYNC=0
```

이 된다.

첫 번째 줄은 server identity이고 두 번째 줄은 현재 server session에서 sync를 허용하는지를 나타낸다.

따라서 EO1은 PC Gallery에 접속한 뒤 단순히 이미지부터 다운로드하지 않는다.

먼저 server의 상태를 확인한다.

```text
PC Gallery 선택
      |
      v
GET /eo1-status
      |
      v
Server identity 확인
      |
      v
SYNC 값 확인
      |
      +---- SYNC=0 ----> PC Gallery만 표시
      |
      +---- SYNC=1 ----> Safe Sync 시작
```

---

## 7. TRUSTED_SERVER

EO1에는 다음 설정 파일이 있다.

```text
/sdcard/EO1-Museum/.config
```

여기에는 PC Gallery와 Safe Sync에 필요한 설정값이 저장된다.

예를 들면:

```ini
NETWORK_HOST=192.168.1.103
NETWORK_PORT=8000
CONNECT_TIMEOUT_SEC=10
MAX_MEDIA_FILES=100
MIN_FREE_MB=200
TRUSTED_SERVER=EO1M-8F29C74A
```

`TRUSTED_SERVER`는 EO1이 sync를 허용할 PC Gallery server의 identity이다.

server가 `/eo1-status`에서 반환하는 identity가 이 값과 일치해야 sync를 수행한다.

즉 같은 네트워크에 우연히 다른 HTTP server가 실행되고 있다고 해서 EO1이 임의로 파일을 받아들이지 않는다.

---

## 8. 선택적 Sync

v0.4에서 중요한 설계 결정 중 하나는 **PC Gallery를 열 때마다 무조건 sync하지 않는 것**이다.

평소에는:

```text
python server.py
```

를 실행한다.

EO1에서 PC Gallery를 선택하면 WebView를 통해 PC Gallery를 볼 수 있지만 Local Gallery의 파일에는 아무 변화가 없다.

새로운 전시를 EO1으로 옮기고 싶을 때만:

```text
python server.py --sync
```

를 사용한다.

따라서 PC에서 sync 여부를 명시적으로 선택할 수 있다.

사용 흐름은 다음과 같다.

```text
평상시

python server.py
      |
      v
PC Gallery
      |
      v
EO1 WebView에서 감상
      |
      X
Local storage 변경 없음
```

새 전시를 전달할 때에는:

```text
python server.py --sync
      |
      v
PC Gallery 선택
      |
      v
Safe Sync
      |
      v
EO1 internal storage
```

이 방식은 사용자의 행동 자체가 sync 의도를 명확하게 표현하도록 한다.

---

## 9. Network Gallery가 Sync trigger

EO1은 재부팅하거나 앱을 새로 실행하면 항상 Local Gallery로 시작한다.

따라서 부팅 시점에는 sync를 시도하지 않는다.

```text
POWER ON
    |
    v
Android
    |
    v
EO1 Museum
    |
    v
Local Gallery
```

PC가 꺼져 있거나 Wi-Fi가 연결되지 않았더라도 기존 Local Gallery는 정상적으로 작동한다.

sync가 필요한 경우 사용자가 마우스 우클릭 메뉴에서:

```text
PC Gallery
```

를 선택한다.

이 동작이 PC server의 상태를 확인하는 trigger가 된다.

따라서 v0.4의 기본 철학은 다음과 같이 정리할 수 있다.

```text
부팅
  = 기존 Local Gallery 감상

PC Gallery 선택
  = PC server 접속

server.py --sync
  = PC가 EO1에 새로운 collection 전달 허용
```

---

## 10. images.js를 이용한 파일 목록

sync가 허용되면 EO1은 PC server에서 `images.js`를 읽는다.

예:

```javascript
var images = [
  "display/0001.jpg",
  "display/0002.jpg",
  "display/0003.jpg",
];
```

EO1은 여기에서 이미지 경로를 얻는다.

따라서 PC server에 별도의 데이터베이스나 복잡한 API가 필요하지 않다.

기존 Network Gallery가 사용하는 파일 목록을 그대로 sync에서도 이용한다.

이것은 v0.4의 구현을 상당히 단순하게 만든다.

---

## 11. EO1의 저장 위치

PC에서 받은 이미지는 다음 위치에 저장한다.

```text
/sdcard/EO1-Museum/images
```

예를 들어 PC에:

```text
display/0001.jpg
display/0002.jpg
display/0003.jpg
```

가 있다면 EO1에는:

```text
/sdcard/EO1-Museum/images/0001.jpg
/sdcard/EO1-Museum/images/0002.jpg
/sdcard/EO1-Museum/images/0003.jpg
```

형태로 저장된다.

이 디렉토리는 기존 Local Gallery가 사용하는 바로 그 디렉토리이다.

따라서 별도의 변환 과정 없이 Local Gallery가 새로 받은 이미지를 재생할 수 있다.

---

## 12. 같은 이름의 파일은 교체

`make_gallery.py`는 Gallery를 새로 만들 때마다 파일명을:

```text
0001.jpg
0002.jpg
0003.jpg
...
```

형태로 다시 부여한다.

따라서 이전 Gallery의 `0001.jpg`와 새로운 Gallery의 `0001.jpg`는 이름은 같지만 전혀 다른 작품일 수 있다.

이 때문에 v0.4에서는 다음과 같은 규칙을 사용한다.

> 같은 이름의 파일이 EO1에 이미 있어도 새 파일로 교체한다.

즉:

```text
PC                    EO1

0001.jpg  --------->  0001.jpg  replace
0002.jpg  --------->  0002.jpg  replace
0003.jpg  --------->  0003.jpg  replace
```

파일명이 존재한다는 이유만으로 다운로드를 건너뛰지 않는다.

PC Gallery가 현재 전시의 기준이기 때문이다.

---

## 13. 임시 파일을 이용한 Safe Sync

기존 파일을 바로 덮어쓰는 방식은 위험하다.

Wi-Fi가 끊기거나 HTTP 전송이 실패하면 기존 이미지까지 손상될 수 있기 때문이다.

따라서 새 파일은 먼저 임시 파일로 받는다.

개념적으로는:

```text
0001.jpg.tmp
```

와 같은 형태이다.

다운로드가 정상적으로 끝난 뒤에만 기존 파일을 교체한다.

```text
PC
 |
 | download
 v
0001.jpg.tmp
 |
 | success
 v
기존 0001.jpg 제거
 |
 v
0001.jpg.tmp -> 0001.jpg
```

전송이 실패하면 기존 `0001.jpg`는 그대로 남아 있다.

따라서 네트워크 오류 때문에 현재 Local Gallery까지 사용할 수 없게 되는 일을 줄일 수 있다.

이러한 이유로 v0.4의 기능을 **Safe Sync**라고 부를 수 있다.

---

## 14. MAX_MEDIA_FILES

EO1의 내부 저장공간은 무한하지 않다.

따라서 `.config`에는 다음 설정을 둔다.

```ini
MAX_MEDIA_FILES=100
```

예를 들어 PC의 `images.js`에 300개의 이미지가 있더라도 이 값이 100이면 EO1은 최대 100개의 파일까지만 sync 대상으로 삼는다.

Gallery 규모를 PC에서 실수로 지나치게 크게 만들더라도 EO1 내부 저장공간을 무제한으로 사용하는 것을 방지한다.

이 값은 필요에 따라 `.config`에서 변경할 수 있다.

---

## 15. MIN_FREE_MB

파일 개수뿐 아니라 남은 저장공간도 확인한다.

예:

```ini
MIN_FREE_MB=200
```

이는 sync 때문에 EO1의 여유 공간이 지나치게 줄어들지 않도록 하기 위한 안전장치이다.

개념적으로는 각 파일을 받기 전에 다음을 확인한다.

```text
다음 파일
   |
   v
남은 공간 확인
   |
   +---- 충분함 ----> download
   |
   +---- 부족함 ----> sync 중단
```

EO1은 Android 자체와 앱 실행을 위해서도 일정한 여유 공간이 필요하다.

따라서 저장장치를 끝까지 채우는 것보다 일정 공간을 항상 남겨 두는 편이 안전하다.

---

## 16. EO1 화면의 Sync 상태 표시

네트워크 sync는 몇 초 이상 걸릴 수 있다.

아무 표시가 없으면 사용자는 현재 파일을 받고 있는지, 멈춘 것인지 알기 어렵다.

따라서 v0.4에서는 sync 진행 상태를 EO1 화면에 표시한다.

예:

```text
Syncing... 23 / 100
```

다운로드가 진행되면서 숫자가 갱신된다.

완료되면:

```text
Sync complete: 100 images
```

와 같은 메시지를 잠시 표시한다.

저장공간 제한이나 오류로 중단된 경우에도 그 이유를 화면에서 알 수 있도록 한다.

예:

```text
Sync stopped: free space limit
```

평상시 `SYNC=0`인 PC Gallery에서는 sync 메시지를 표시하지 않는다.

즉 작품 감상 중에는 불필요한 상태 문구가 화면을 방해하지 않는다.

---

## 17. PC Gallery와 Local Gallery의 역할 변화

v0.3에서는 두 Gallery의 관계가 다음과 같았다.

```text
Local Gallery       PC Gallery
     |                   |
     |                   |
EO1 storage          PC server
```

서로 독립적인 두 표시 방식이었다.

v0.4에서는 다음과 같이 연결된다.

```text
             PC Gallery
                 |
                 | Safe Sync
                 v
             EO1 storage
                 |
                 v
            Local Gallery
```

따라서 PC Gallery는 이제 두 가지 역할을 가진다.

```text
1. PC 콘텐츠를 실시간으로 표시

2. PC에서 준비한 콘텐츠를
   EO1 Local Gallery로 전달
```

이것이 v0.4에서 가장 중요한 구조적 변화이다.

---

## 18. PC가 없어도 계속 작동한다

Safe Sync가 끝난 뒤에는 PC가 더 이상 필요하지 않다.

```text
PC에서 Gallery 준비
       |
       v
server.py --sync
       |
       v
EO1 Safe Sync
       |
       v
Local Gallery
       |
       v
PC 종료 가능
```

이미지는 EO1 내부 저장공간에 있기 때문이다.

이것은 EO1 Museum의 기본 원칙과도 일치한다.

> EO1은 가능한 한 독립적인 디지털 액자로 동작해야 한다.

PC는 콘텐츠를 준비하고 전달할 때만 필요하다.

실제 감상에는 PC나 네트워크가 필요하지 않다.

---

## 19. 기존 ADB 파일 전송과의 차이

v0.3까지 Local Gallery에 새 이미지를 넣는 가장 직접적인 방법은 ADB였다.

예:

```text
adb push artwork.jpg /sdcard/EO1-Museum/images/
```

개발 중에는 편리하지만 일반적인 Gallery 운영 방식으로는 번거롭다.

Safe Sync를 사용하면:

```text
PC에서 Gallery 제작
        |
        v
server.py --sync
        |
        v
EO1에서 PC Gallery 선택
```

만으로 이미지를 전달할 수 있다.

따라서 콘텐츠 갱신을 위해 더 이상 USB 케이블을 연결하거나 ADB 명령을 입력할 필요가 없다.

ADB는 다시 개발과 진단을 위한 도구로 돌아간다.

---

## 20. v0.4의 전체 동작

현재 구조를 전체적으로 정리하면 다음과 같다.

```text
POWER ON
   |
   v
Android
   |
   v
EO1 Museum
   |
   v
Local Gallery
   |
   +--> 내부 저장 이미지/MP4 재생
   |
   +--> PC 없이 독립 동작
   |
   +--> 마우스 우클릭
             |
             v
         PC Gallery
             |
             v
       GET /eo1-status
             |
             +--> SYNC=0
             |       |
             |       v
             |   WebView Gallery
             |
             +--> SYNC=1
                     |
                     v
              TRUSTED_SERVER 확인
                     |
                     v
                images.js
                     |
                     v
             MAX_MEDIA_FILES
             MIN_FREE_MB 확인
                     |
                     v
                 Safe Sync
                     |
                     v
       /sdcard/EO1-Museum/images
                     |
                     v
                Local Gallery
```

---

## 21. v0.3에서 v0.4로

Native Gallery의 발전 과정은 이제 다음과 같이 정리할 수 있다.

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
```

v0.3이 Local Gallery와 PC Gallery를 **하나의 앱 안에 통합한 버전**이었다면, v0.4는 그 두 Gallery 사이에 **콘텐츠 이동 경로를 만든 버전**이라고 할 수 있다.

---

## 22. Collection workflow와의 연결

EO1 Museum 프로젝트의 PC 쪽 작업도 점차 역할이 분명해졌다.

작품을 발견하고 수집하는 단계와 EO1에서 표시하는 단계는 서로 분리된다.

```text
The Met
   |
   +--> GET_MET_ART_KEYWORD.py
   |
Wikimedia Commons
   |
   +--> GET_COMMONS_ART.py
              |
              v
           original/
              |
              v
       make_gallery.py
              |
              v
           display/
              |
              v
           images.js
              |
              v
          server.py
              |
              v
           Safe Sync
              |
              v
        EO1 Local Gallery
```

따라서 전체 프로젝트는 이제 크게 다음 두 부분으로 볼 수 있다.

```text
Collection
    -> 무엇을 전시할 것인가?

App / Gallery
    -> 그것을 EO1에서 어떻게 보여줄 것인가?
```

v0.4의 Safe Sync는 이 두 영역을 연결하는 마지막 전달 단계에 해당한다.

---

## 23. v0.4에서 해결된 문제

이번 버전으로 다음 문제가 해결되었다.

### 이전

```text
PC에서 작품 준비
      |
      v
Gallery 생성
      |
      v
ADB 연결
      |
      v
adb push
      |
      v
EO1 Local Gallery
```

### 현재

```text
PC에서 작품 준비
      |
      v
Gallery 생성
      |
      v
server.py --sync
      |
      v
EO1에서 PC Gallery 선택
      |
      v
Safe Sync
      |
      v
EO1 Local Gallery
```

콘텐츠를 EO1으로 옮기는 과정이 Gallery 자체의 기능 안으로 들어왔다.

---

## 24. 아직 단순하게 유지한 부분

v0.4의 목적은 복잡한 파일 동기화 시스템을 만드는 것이 아니다.

따라서 다음과 같은 기능은 현재 필요하지 않다.

- 양방향 sync
- 사용자 계정
- cloud storage
- 파일별 database
- 복잡한 sync protocol
- background cloud service
- EO1에서 PC로 파일 업로드
- 여러 PC 사이의 동기화

EO1 Museum은 개인적인 디지털 액자 프로젝트이다.

따라서 현재의:

```text
PC Gallery
     |
     | HTTP
     v
EO1
```

구조만으로 충분하다.

기능을 늘리는 것보다 오래된 Android 4.4.2 환경에서 단순하고 안정적으로 작동하는 것이 더 중요하다.

---

## 25. 앞으로 확인할 사항

v0.4의 기본 기능은 구현되었지만 실제 사용을 계속하면서 다음 사항은 확인할 필요가 있다.

- 많은 파일을 연속으로 sync할 때의 안정성
- Wi-Fi가 중간에 끊겼을 때의 복구
- 저장공간 부족 상황
- 큰 JPEG 파일의 전송
- `MAX_MEDIA_FILES` 값 변경
- `MIN_FREE_MB` 값 변경
- PC IP 주소 변경
- server identity 불일치 상황
- sync 완료 후 Local Gallery의 media rescan
- 기존 collection에만 존재하는 파일을 어떻게 처리할 것인지

특히 마지막 항목은 향후 PC Gallery를 EO1에 완전히 mirror할 것인지, 아니면 기존 Local Gallery 파일을 보존할 것인지와 관련된다.

현재는 우선 **안전한 PC → EO1 전송 기능 자체를 확립하는 것**에 초점을 맞춘다.

---

## 26. 맺음말

v0.3에서 EO1 Museum은 이미 독립적인 디지털 액자로 사용할 수 있는 수준에 도달하였다.

전원을 켜면 Local Gallery가 시작되고, 내부 저장공간의 이미지와 동영상을 재생한다. 필요하면 PC Gallery로 전환하여 PC가 제공하는 콘텐츠도 볼 수 있었다.

하지만 두 Gallery 사이에는 아직 벽이 하나 있었다.

PC에서 보고 있는 좋은 전시를 Local Gallery로 가져오려면 결국 ADB를 이용하여 파일을 직접 복사해야 했다.

v0.4에서는 그 벽을 없앴다.

PC에서 새로운 Gallery를 만든 뒤:

```text
python server.py --sync
```

를 실행하고 EO1에서 PC Gallery를 선택하면 된다.

EO1은 server의 identity와 sync 요청을 확인하고, 저장공간 제한을 지키면서 이미지를 내부 저장공간으로 가져온다.

전송이 끝나면 PC를 끌 수 있다.

EO1에는 새로운 전시가 남는다.

처음 EO1-Museum 프로젝트는 사라진 공식 서비스를 대신하여 **그림을 다시 화면에 띄우는 것**에서 시작했다.

이제는 작품을 발견하고, PC에서 전시를 만들고, 그것을 네트워크를 통해 EO1으로 전달한 뒤, 다시 독립적인 액자로 감상할 수 있게 되었다.

v0.4에서 PC Gallery와 Local Gallery는 더 이상 별개의 두 기능이 아니다.

**PC Gallery는 전시를 준비하고 전달하는 창구가 되었고, Local Gallery는 그 전시를 독립적으로 계속 보여주는 최종 목적지가 되었다.**