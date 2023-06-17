## 주요 변경사항

  * PlexMate 스캔 기능 추가
  * support_site, make_yaml 플러그인 사용.
  * 기본 파일명을 최대한 유지
---

## 다운로드 파일처리

#### 1. 기본 (다운로드 파일처리)

  - 설정 값을 설정하는 UI 
  - 세부 설정은 yaml로 설정
  - yaml 에 없는 장르는 장르 예외 설정 폴더명을 따라감
  - {SEASON} 은 Season 1, Season 101 같은 조건에 맞는 시즌명으로 변경되고 {season} 은 Season 1 형식만 사용

#### 공통

  - 파일처리 이후 소스 폴더는 모두 비워짐.
  - 타겟 폴더, 에러 폴더는 소스 폴더 안에 두지 말 것
  - 처리 상태화면에 "Dry Run 시작" 버튼이 있음. 설정 후 이 버튼으로 시작하면 실제 파일 변경을 하지 않고 결과만 확인 가능 

----

## yaml

![](https://cdn.discordapp.com/attachments/631112094015815681/857275999913377822/unknown.png)

  - data/db 폴더에 fileprocess_ftv_basic.yaml 파일과 fileprocess_ftv_simple.yaml 자동생성
  - 세부 설정을 원할 경우 파일의 주석부분을 확인하여 옵션 추가.

